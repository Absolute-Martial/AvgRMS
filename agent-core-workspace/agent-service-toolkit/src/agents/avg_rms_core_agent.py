import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command

from avg_rms_core.audit import JsonlAuditLogger
from avg_rms_core.contracts import AuditEvent, FinalDecision, PlannedAction, ToolResult
from avg_rms_core.critics import DeterministicCritic
from avg_rms_core.fake_adapter import FakeAdapter
from avg_rms_core.guardrails import GuardrailGate
from avg_rms_core.planners import LLMPlanner, ScriptedPlanner
from avg_rms_core.state import AvgRMSState


class AgentState(MessagesState, total=False):
    request_text: str
    planner_mode: str
    adapter_mode: str
    fake_adapter_mode: str
    available_tools: list[str]
    attempt_count: int
    max_attempts: int
    current_action: PlannedAction
    action_history: list[PlannedAction]
    result_history: list[ToolResult]
    last_result: ToolResult
    last_block_reason: str
    final_response: str
    audit_log_path: str
    final_status: str
    correction_of: str | None
    metadata: dict[str, Any]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _config_value(config: RunnableConfig, key: str, default: Any) -> Any:
    return config["configurable"].get(key, default)


def _get_thread_id(config: RunnableConfig) -> str:
    return str(config["configurable"]["thread_id"])


def _get_run_id(config: RunnableConfig) -> str:
    return str(config["run_id"])


def _get_logger(state: AgentState) -> JsonlAuditLogger:
    return JsonlAuditLogger(Path(state["audit_log_path"]))


def _new_state(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    if state.get("request_text"):
        return {}
    message = state["messages"][-1]
    if not isinstance(message, HumanMessage):
        raise TypeError(f"Expected HumanMessage, got {type(message)}")
    audit_dir = Path(_config_value(config, "audit_log_dir", "data"))
    return {
        "request_text": str(message.content),
        "planner_mode": _config_value(config, "planner_mode", "scripted"),
        "adapter_mode": _config_value(config, "adapter_mode", "fake"),
        "fake_adapter_mode": _config_value(config, "fake_adapter_mode", "fail_once"),
        "available_tools": ["fake.lookup"],
        "attempt_count": 0,
        "max_attempts": int(_config_value(config, "max_attempts", 2)),
        "action_history": [],
        "result_history": [],
        "audit_log_path": str(audit_dir / "avg_rms_core.audit.jsonl"),
        "metadata": {"scripted_tool_name": _config_value(config, "scripted_tool_name", None)},
    }


async def _select_action(state: AgentState, config: RunnableConfig) -> PlannedAction | FinalDecision:
    if state["planner_mode"] == "llm":
        planner = LLMPlanner()
        await planner.plan_with_model(state["request_text"], config["configurable"].get("model"))
    planner = ScriptedPlanner()
    if not state.get("action_history"):
        action = planner.plan_next(
            AvgRMSState(
                request_text=state["request_text"],
                planner_mode=state["planner_mode"],
                adapter_mode=state["adapter_mode"],
                available_tools=state.get("available_tools", []),
                attempt_count=state.get("attempt_count", 0),
                max_attempts=state.get("max_attempts", 2),
                action_history=state.get("action_history", []),
                result_history=state.get("result_history", []),
                last_result=state.get("last_result"),
                last_block_reason=state.get("last_block_reason"),
                final_response=state.get("final_response", ""),
                audit_log_path=state.get("audit_log_path", ""),
                metadata=state.get("metadata", {}),
            )
        )
    else:
        avg_state = AvgRMSState(
            request_text=state["request_text"],
            planner_mode=state["planner_mode"],
            adapter_mode=state["adapter_mode"],
            available_tools=state.get("available_tools", []),
            attempt_count=state.get("attempt_count", 0),
            max_attempts=state.get("max_attempts", 2),
            current_action=state.get("current_action"),
            action_history=state.get("action_history", []),
            result_history=state.get("result_history", []),
            last_result=state.get("last_result"),
            last_block_reason=state.get("last_block_reason"),
            final_response=state.get("final_response", ""),
            audit_log_path=state.get("audit_log_path", ""),
            metadata=state.get("metadata", {}),
        )
        action = planner.replan_after_result(avg_state)

    if isinstance(action, PlannedAction) and state.get("metadata", {}).get("scripted_tool_name"):
        action = PlannedAction(
            id=action.id,
            tool=state["metadata"]["scripted_tool_name"],
            args=action.args,
            reason=action.reason,
        )

    return action


async def plan(state: AgentState, config: RunnableConfig) -> Command[Literal["guardrail_check", "finalize_attempts_exhausted"]]:
    updates = _new_state(state, config)
    working_state: AgentState = {**state, **updates}
    action_or_final = await _select_action(working_state, config)
    if isinstance(action_or_final, FinalDecision):
        return Command(
            update={**updates, "final_status": action_or_final.status, "final_response": action_or_final.summary},
            goto="finalize_attempts_exhausted",
        )

    action_history = [*working_state.get("action_history", []), action_or_final]
    correction_of = action_history[-2].id if len(action_history) > 1 else None
    return Command(
        update={
            **updates,
            "current_action": action_or_final,
            "action_history": action_history,
            "correction_of": correction_of,
        },
        goto="guardrail_check",
    )


def guardrail_check(state: AgentState, config: RunnableConfig) -> Command[Literal["act", "finalize_blocked"]]:
    logger = _get_logger(state)
    decision = GuardrailGate({"fake.lookup"}).check(state["current_action"])
    logger.write(
        AuditEvent(
            ts=_now_iso(),
            run_id=_get_run_id(config),
            thread_id=_get_thread_id(config),
            planner=state["planner_mode"],
            event_type="guardrail_decision",
            action_id=state["current_action"].id,
            tool=state["current_action"].tool,
            args=state["current_action"].args,
            decision=decision.decision,
            output_hash="",
            status=decision.decision,
            correction_of=state.get("correction_of"),
            latency_ms=0,
        )
    )
    if decision.decision == "blocked":
        return Command(
            update={"last_block_reason": decision.reason, "final_status": "blocked"},
            goto="finalize_blocked",
        )
    return Command(update={"last_block_reason": ""}, goto="act")


def act(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    start = time.perf_counter()
    adapter = FakeAdapter(mode=state["fake_adapter_mode"])
    if state.get("attempt_count", 0) > 0:
        adapter.calls = state["attempt_count"]
    result = adapter.run_tool(state["current_action"].tool, state["current_action"].args)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    _get_logger(state).write(
        AuditEvent(
            ts=_now_iso(),
            run_id=_get_run_id(config),
            thread_id=_get_thread_id(config),
            planner=state["planner_mode"],
            event_type="action_result",
            action_id=state["current_action"].id,
            tool=state["current_action"].tool,
            args=state["current_action"].args,
            decision="allowed",
            output_hash=result.output_hash,
            status=result.status,
            correction_of=state.get("correction_of"),
            latency_ms=elapsed_ms,
        )
    )
    return {
        "last_result": result,
        "result_history": [*state.get("result_history", []), result],
        "attempt_count": state.get("attempt_count", 0) + 1,
    }


def observe(state: AgentState) -> dict[str, Any]:
    return {}


def critic(state: AgentState) -> Command[Literal["plan", "finalize_success", "finalize_attempts_exhausted"]]:
    result = state["last_result"]
    avg_state = AvgRMSState(
        request_text=state["request_text"],
        planner_mode=state["planner_mode"],
        adapter_mode=state["adapter_mode"],
        available_tools=state.get("available_tools", []),
        attempt_count=state.get("attempt_count", 0),
        max_attempts=state.get("max_attempts", 2),
        current_action=state.get("current_action"),
        action_history=state.get("action_history", []),
        result_history=state.get("result_history", []),
        last_result=result,
        last_block_reason=state.get("last_block_reason"),
        final_response=state.get("final_response", ""),
        audit_log_path=state.get("audit_log_path", ""),
        metadata=state.get("metadata", {}),
    )
    decision = DeterministicCritic().assess(avg_state, result)
    if decision.outcome == "success":
        return Command(update={"final_status": "success"}, goto="finalize_success")
    if decision.outcome == "attempts_exhausted":
        return Command(
            update={"final_status": "attempts_exhausted", "final_response": decision.summary},
            goto="finalize_attempts_exhausted",
        )
    return Command(update={"final_status": "retry"}, goto="plan")


def finalize_success(state: AgentState) -> dict[str, Any]:
    if len(state.get("result_history", [])) > 1:
        content = "Recovered after one adapter runtime failure and completed the lookup."
    else:
        content = "Completed the lookup successfully."
    return {"messages": [AIMessage(content=content)], "final_response": content}


def finalize_blocked(state: AgentState) -> dict[str, Any]:
    content = f"Blocked by guardrail: {state['last_block_reason']}"
    return {"messages": [AIMessage(content=content)], "final_response": content}


def finalize_attempts_exhausted(state: AgentState) -> dict[str, Any]:
    content = state.get("final_response", "Retries exhausted after adapter runtime failures.")
    return {"messages": [AIMessage(content=content)], "final_response": content}


builder = StateGraph(AgentState)
builder.add_node("plan", plan)
builder.add_node("guardrail_check", guardrail_check)
builder.add_node("act", act)
builder.add_node("observe", observe)
builder.add_node("critic", critic)
builder.add_node("finalize_success", finalize_success)
builder.add_node("finalize_blocked", finalize_blocked)
builder.add_node("finalize_attempts_exhausted", finalize_attempts_exhausted)
builder.add_edge(START, "plan")
builder.add_edge("act", "observe")
builder.add_edge("observe", "critic")
builder.add_edge("finalize_success", END)
builder.add_edge("finalize_blocked", END)
builder.add_edge("finalize_attempts_exhausted", END)

avg_rms_core_agent = builder.compile()
avg_rms_core_agent.name = "avg-rms-core"
