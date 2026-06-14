import json
from dataclasses import dataclass
from typing import Protocol

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from avg_rms_core.contracts import FinalDecision, PlannedAction
from avg_rms_core.openrouter import build_openrouter_client, invoke_openrouter_with_retry
from avg_rms_core.state import AvgRMSState
from schema.models import FakeModelName


class Planner(Protocol):
    def plan_next(self, state: AvgRMSState) -> PlannedAction | FinalDecision: ...

    def replan_after_result(self, state: AvgRMSState) -> PlannedAction | FinalDecision: ...


@dataclass
class ScriptedPlanner:
    def plan_next(self, state: AvgRMSState) -> PlannedAction | FinalDecision:
        return PlannedAction(
            id="action-001",
            tool="fake.lookup",
            args={"target": "alpha"},
            reason="initial lookup",
        )

    def replan_after_result(self, state: AvgRMSState) -> PlannedAction | FinalDecision:
        if state.attempt_count >= state.max_attempts:
            return FinalDecision(
                status="attempts_exhausted",
                summary="Retries exhausted after adapter runtime failures.",
            )
        return PlannedAction(
            id="action-002",
            tool="fake.lookup",
            args={"target": "alpha", "retry": 1},
            reason="retry after adapter runtime failure",
        )


def _planner_prompt(request_text: str) -> str:
    return (
        "You are generating Splunk SPL for a security investigation.\n"
        "Return JSON only with one key: spl.\n"
        "Requirements:\n"
        "- Target index=botsv3.\n"
        "- READ-ONLY queries only.\n"
        "- Prefer summarizing or flattened SPL using stats, tstats, chart, or timechart.\n"
        "- NO nested subsearches.\n"
        "- NO destructive or write commands.\n"
        "- Make the SPL directly runnable.\n"
        f"Investigation request: {request_text}\n"
        'Example response: {"spl":"search index=botsv3 | stats count by sourcetype"}'
    )


def _extract_spl(raw_output: str) -> str:
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        payload = {"spl": cleaned}
    spl = str(payload.get("spl", "")).strip()
    if not spl:
        raise ValueError("model returned empty spl")
    return spl


def _validate_spl(spl: str) -> None:
    normalized = spl.lower()
    if "botsv3" not in normalized:
        raise ValueError("model output must target index=botsv3")
    if "[" in spl or "]" in spl:
        raise ValueError("model output must not use nested subsearches")
    if "| delete" in normalized or "| collect " in normalized:
        raise ValueError("model output must be read-only")


class LLMPlanner:
    def __init__(self) -> None:
        self.last_raw_output: str | None = None

    async def plan_with_model(self, prompt: str, model_name: str | None = None) -> str:
        from core import get_model, settings

        selected_model = model_name or settings.DEFAULT_MODEL
        model = get_model(selected_model)
        payload = [HumanMessage(content=prompt)]
        if selected_model in FakeModelName:
            response = model.invoke(payload)
        else:
            response = await model.ainvoke(payload)
        return response.content if hasattr(response, "content") else str(response)

    async def plan_action(
        self,
        state: AvgRMSState,
        config,
        action_id: str,
    ) -> PlannedAction:
        configurable = config["configurable"]
        api_key = configurable.get("openrouter_api_key")
        if not api_key:
            raise ValueError("missing openrouter_api_key for llm planner")
        client = build_openrouter_client(
            api_key=api_key,
            model=configurable.get("openrouter_model", "google/gemma-2-9b-it"),
            base_url=configurable.get("openrouter_base_url", "https://openrouter.ai/api/v1"),
            timeout=float(configurable.get("openrouter_timeout_seconds", 20.0)),
        )
        self.last_raw_output = await invoke_openrouter_with_retry(
            client,
            _planner_prompt(state.request_text),
            timeout_seconds=float(configurable.get("openrouter_timeout_seconds", 20.0)),
            retries=1,
        )
        spl = _extract_spl(self.last_raw_output)
        _validate_spl(spl)
        return PlannedAction(
            id=action_id,
            tool="search_spl",
            args={"spl": spl},
            reason="llm planned spl",
        )


def build_planner_clients(
    openrouter_api_key: str,
    foundation_sec_base_url: str,
    foundation_sec_api_key: str,
    foundation_sec_model: str,
) -> dict[str, object]:
    return {
        "orchestrator": build_openrouter_client(
            api_key=openrouter_api_key,
            model="google/gemma-2-9b-it",
        ),
        "spl_generator": ChatOpenAI(
            api_key=foundation_sec_api_key,
            base_url=foundation_sec_base_url,
            model=foundation_sec_model,
            temperature=0,
        ),
    }
