import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.func import entrypoint

from avg_rms_core.audit import JsonlAuditLogger
from avg_rms_core.contracts import AuditEvent, FinalDecision, PlannedAction
from avg_rms_core.critics import DeterministicCritic
from avg_rms_core.fake_adapter import FakeAdapter
from avg_rms_core.guardrails import GuardrailGate
from avg_rms_core.planners import LLMPlanner, ScriptedPlanner
from avg_rms_core.splunk_adapter import SplunkAdapter
from avg_rms_core.state import AvgRMSState


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _config_value(config: RunnableConfig, key: str, default):
    return config["configurable"].get(key, default)


def _get_thread_id(config: RunnableConfig) -> str:
    return str(config["configurable"]["thread_id"])


def _get_run_id(config: RunnableConfig) -> str:
    return str(config.get("run_id") or uuid4())


def _latest_human_message(messages: list[BaseMessage]) -> HumanMessage:
    message = messages[-1]
    if not isinstance(message, HumanMessage):
        raise TypeError(f"Expected HumanMessage, got {type(message)}")
    return message


def _build_state(messages: list[BaseMessage], config: RunnableConfig) -> AvgRMSState:
    message = _latest_human_message(messages)
    audit_dir = Path(_config_value(config, "audit_log_dir", "data"))
    return AvgRMSState(
        request_text=str(message.content),
        planner_mode=_config_value(config, "planner_mode", "scripted"),
        adapter_mode=_config_value(config, "adapter_mode", "fake"),
        available_tools=[],
        max_attempts=int(_config_value(config, "max_attempts", 2)),
        audit_log_path=str(audit_dir / "avg_rms_core.audit.jsonl"),
        metadata={
            "scripted_tool_name": _config_value(config, "scripted_tool_name", None),
            "fake_adapter_mode": _config_value(config, "fake_adapter_mode", "fail_once"),
        },
    )


def _logger(state: AvgRMSState) -> JsonlAuditLogger:
    return JsonlAuditLogger(Path(state.audit_log_path))


def _planner_label(state: AvgRMSState) -> str:
    return str(state.metadata.get("audit_planner", state.planner_mode))


def _planner_reason(state: AvgRMSState) -> str | None:
    return state.metadata.get("planner_reason")


def _build_adapter(state: AvgRMSState, config: RunnableConfig):
    if state.adapter_mode == "splunk":
        verify_value = _config_value(
            config,
            "splunk_ca_bundle",
            _config_value(config, "splunk_verify_ssl", True),
        )
        return SplunkAdapter(
            base_url=_config_value(config, "splunk_base_url", ""),
            host=_config_value(config, "splunk_host", None),
            port=int(_config_value(config, "splunk_port", 8089)),
            scheme=_config_value(config, "splunk_scheme", "https"),
            token=_config_value(config, "splunk_token", ""),
            app=_config_value(config, "splunk_app", "search"),
            verify=verify_value,
        )
    return FakeAdapter(mode=state.metadata["fake_adapter_mode"])


def _coerce_scripted_action_for_adapter(
    state: AvgRMSState,
    action_or_final: PlannedAction | FinalDecision,
) -> PlannedAction | FinalDecision:
    if not isinstance(action_or_final, PlannedAction):
        return action_or_final

    if state.adapter_mode == "splunk":
        if action_or_final.id == "action-001":
            return PlannedAction(
                id=action_or_final.id,
                tool="search_spl",
                args={"spl": "search index=botsv3 sourcetype=wineventlog | head 20"},
                reason="initial hero search",
            )
        return PlannedAction(
            id=action_or_final.id,
            tool="search_spl",
            args={"spl": "search index=botsv3 sourcetype=wineventlog earliest=-30d | head 10"},
            reason="retry narrowed hero search",
        )

    if state.metadata.get("scripted_tool_name"):
        return PlannedAction(
            id=action_or_final.id,
            tool=state.metadata["scripted_tool_name"],
            args=action_or_final.args,
            reason=action_or_final.reason,
        )

    return action_or_final


async def _next_action(state: AvgRMSState, config: RunnableConfig) -> PlannedAction | FinalDecision:
    if state.planner_mode == "llm":
        planner = LLMPlanner()
        try:
            action_id = "action-001" if not state.action_history else "action-002"
            state.metadata["audit_planner"] = "llm"
            state.metadata["planner_reason"] = None
            return await planner.plan_action(state, config, action_id)
        except Exception as exc:
            reason = str(exc)
            logging.warning("Falling back to ScriptedPlanner after LLM planner failure: %s", reason)
            state.metadata["audit_planner"] = "scripted_fallback"
            state.metadata["planner_reason"] = reason

    planner = ScriptedPlanner()
    action_or_final: PlannedAction | FinalDecision
    if not state.action_history:
        action_or_final = planner.plan_next(state)
    else:
        action_or_final = planner.replan_after_result(state)

    return _coerce_scripted_action_for_adapter(state, action_or_final)


def _audit_guardrail(
    state: AvgRMSState,
    config: RunnableConfig,
    action: PlannedAction,
    decision: str,
    correction_of: str | None,
) -> None:
    _logger(state).write(
        AuditEvent(
            ts=_now_iso(),
            run_id=_get_run_id(config),
            thread_id=_get_thread_id(config),
            planner=_planner_label(state),
            planner_reason=_planner_reason(state),
            event_type="guardrail_decision",
            action_id=action.id,
            tool=action.tool,
            args=action.args,
            decision=decision,
            output_hash="",
            status=decision,
            correction_of=correction_of,
            latency_ms=0,
        )
    )


def _audit_result(
    state: AvgRMSState,
    config: RunnableConfig,
    action: PlannedAction,
    correction_of: str | None,
    result,
    latency_ms: int,
) -> None:
    _logger(state).write(
        AuditEvent(
            ts=_now_iso(),
            run_id=_get_run_id(config),
            thread_id=_get_thread_id(config),
            planner=_planner_label(state),
            planner_reason=_planner_reason(state),
            event_type="action_result",
            action_id=action.id,
            tool=action.tool,
            args=action.args,
            decision="allowed",
            output_hash=result.output_hash,
            status=result.status,
            correction_of=correction_of,
            latency_ms=latency_ms,
        )
    )


@entrypoint()
async def avg_rms_core_agent(
    inputs: dict[str, list[BaseMessage]],
    *,
    previous: dict[str, list[BaseMessage]],
    config: RunnableConfig,
):
    messages = inputs["messages"]
    if previous:
        messages = previous["messages"] + messages

    state = _build_state(messages, config)
    adapter = _build_adapter(state, config)
    state.available_tools = [tool["name"] for tool in adapter.list_tools()]
    final_response = ""

    while True:
        action_or_final = await _next_action(state, config)
        if isinstance(action_or_final, FinalDecision):
            final_response = action_or_final.summary
            break

        correction_of = state.action_history[-1].id if state.action_history else None
        state.current_action = action_or_final
        state.action_history.append(action_or_final)

        guardrail = GuardrailGate(set(state.available_tools)).check(action_or_final)
        _audit_guardrail(state, config, action_or_final, guardrail.decision, correction_of)
        if guardrail.decision == "blocked":
            state.last_block_reason = guardrail.reason
            final_response = f"Blocked by guardrail: {guardrail.reason}"
            break

        start = time.perf_counter()
        if isinstance(adapter, FakeAdapter):
            adapter.calls = state.attempt_count
        result = adapter.run_tool(action_or_final.tool, action_or_final.args)
        latency_ms = int((time.perf_counter() - start) * 1000)
        _audit_result(state, config, action_or_final, correction_of, result, latency_ms)

        state.attempt_count += 1
        state.last_result = result
        state.result_history.append(result)

        critic = DeterministicCritic().assess(state, result)
        if critic.outcome == "success":
            if len(state.result_history) > 1:
                final_response = "Recovered after one adapter runtime failure and completed the lookup."
            else:
                final_response = "Completed the lookup successfully."
            break
        if critic.outcome == "attempts_exhausted":
            final_response = critic.summary
            break

    final_message = AIMessage(content=final_response)
    return entrypoint.final(
        value={"messages": [final_message]},
        save={"messages": messages + [final_message]},
    )
