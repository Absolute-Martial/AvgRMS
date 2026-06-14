from dataclasses import dataclass
from typing import Protocol

from langchain_core.messages import HumanMessage

from avg_rms_core.contracts import FinalDecision, PlannedAction
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


class LLMPlanner:
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
