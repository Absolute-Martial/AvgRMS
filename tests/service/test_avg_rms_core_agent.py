import json

import pytest

from agents.avg_rms_core_agent import avg_rms_core_agent
from avg_rms_core.contracts import PlannedAction, ToolResult
from langgraph.checkpoint.memory import MemorySaver
from schema import UserInput
from service import service


def assert_structural_event_fields(row: dict, expected: dict) -> None:
    comparable = {key: value for key, value in row.items() if key not in {"ts", "latency_ms"}}
    assert comparable == expected


@pytest.mark.asyncio
async def test_avg_rms_core_retries_after_adapter_runtime_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="investigate fake incident",
            agent_config={
                "planner_mode": "scripted",
                "adapter_mode": "fake",
                "fake_adapter_mode": "fail_once",
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Recovered after one adapter runtime failure" in response.content

    rows = [
        json.loads(line)
        for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()
    ]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert len(action_rows) == 2
    assert_structural_event_fields(
        action_rows[0],
        {
            "run_id": action_rows[0]["run_id"],
            "thread_id": action_rows[0]["thread_id"],
            "planner": "scripted",
            "planner_reason": None,
            "event_type": "action_result",
            "action_id": "action-001",
            "tool": "fake.lookup",
            "args": {"target": "alpha"},
            "decision": "allowed",
            "output_hash": action_rows[0]["output_hash"],
            "status": "error",
            "correction_of": None,
        },
    )
    assert_structural_event_fields(
        action_rows[1],
        {
            "run_id": action_rows[1]["run_id"],
            "thread_id": action_rows[1]["thread_id"],
            "planner": "scripted",
            "planner_reason": None,
            "event_type": "action_result",
            "action_id": "action-002",
            "tool": "fake.lookup",
            "args": {"target": "alpha", "retry": 1},
            "decision": "allowed",
            "output_hash": action_rows[1]["output_hash"],
            "status": "ok",
            "correction_of": "action-001",
        },
    )


@pytest.mark.asyncio
async def test_avg_rms_core_blocks_non_allow_listed_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="investigate fake incident",
            agent_config={
                "planner_mode": "scripted",
                "scripted_tool_name": "rm",
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Blocked by guardrail" in response.content

    rows = [
        json.loads(line)
        for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()
    ]
    blocked = [row for row in rows if row["event_type"] == "guardrail_decision"]

    assert blocked[-1]["decision"] == "blocked"
    assert blocked[-1]["action_id"] == "action-001"


@pytest.mark.asyncio
async def test_avg_rms_core_attempts_exhausted_with_max_attempts_one(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="investigate fake incident",
            agent_config={
                "planner_mode": "scripted",
                "fake_adapter_mode": "always_fail",
                "max_attempts": 1,
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Retries exhausted" in response.content

    rows = [
        json.loads(line)
        for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()
    ]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert len(action_rows) == 1
    assert action_rows[0]["action_id"] == "action-001"
    assert action_rows[0]["status"] == "error"


@pytest.mark.asyncio
async def test_avg_rms_core_uses_splunk_adapter(monkeypatch, tmp_path):
    class StubSplunkAdapter:
        name = "splunk"

        def list_tools(self):
            return [{"name": "search_spl"}]

        def run_tool(self, tool: str, args: dict):
            return ToolResult(
                tool=tool,
                args=args,
                stdout="[]",
                output_hash="hash-splunk",
                status="ok",
            )

    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    monkeypatch.setattr("agents.avg_rms_core_agent.SplunkAdapter", lambda **kwargs: StubSplunkAdapter())
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="Who accessed EU customer PII in the last 30 days?",
            agent_config={
                "planner_mode": "scripted",
                "adapter_mode": "splunk",
                "splunk_base_url": "https://example.splunkcloud.com",
                "splunk_token": "token",
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Completed the lookup successfully." in response.content

    rows = [
        json.loads(line)
        for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()
    ]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert action_rows[-1]["tool"] == "search_spl"
    assert action_rows[-1]["decision"] == "allowed"


@pytest.mark.asyncio
async def test_avg_rms_core_llm_mode_executes_model_generated_spl(monkeypatch, tmp_path):
    executed = {}

    class StubSplunkAdapter:
        name = "splunk"

        def list_tools(self):
            return [{"name": "search_spl"}]

        def run_tool(self, tool: str, args: dict):
            executed["tool"] = tool
            executed["args"] = args
            return ToolResult(
                tool=tool,
                args=args,
                stdout="[]",
                output_hash="hash-splunk",
                status="ok",
            )

    async def fake_plan_action(self, state, config, action_id):
        return PlannedAction(
            id=action_id,
            tool="search_spl",
            args={"spl": "search index=botsv3 | stats count by user"},
            reason="model planned spl",
        )

    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    monkeypatch.setattr("agents.avg_rms_core_agent.SplunkAdapter", lambda **kwargs: StubSplunkAdapter())
    monkeypatch.setattr("avg_rms_core.planners.LLMPlanner.plan_action", fake_plan_action)
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="Who accessed EU customer PII in the last 30 days?",
            agent_config={
                "planner_mode": "llm",
                "adapter_mode": "splunk",
                "splunk_base_url": "https://example.splunkcloud.com",
                "splunk_token": "token",
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Completed the lookup successfully." in response.content
    assert executed["tool"] == "search_spl"
    assert executed["args"]["spl"] == "search index=botsv3 | stats count by user"


@pytest.mark.asyncio
async def test_avg_rms_core_llm_failure_falls_back_to_scripted_with_audit_reason(
    monkeypatch, tmp_path
):
    class StubSplunkAdapter:
        name = "splunk"

        def list_tools(self):
            return [{"name": "search_spl"}]

        def run_tool(self, tool: str, args: dict):
            return ToolResult(
                tool=tool,
                args=args,
                stdout="[]",
                output_hash="hash-splunk",
                status="ok",
            )

    async def broken_plan_action(self, state, config, action_id):
        raise TimeoutError("openrouter timed out")

    monkeypatch.setattr(service, "get_agent", lambda agent_id: avg_rms_core_agent)
    monkeypatch.setattr("agents.avg_rms_core_agent.SplunkAdapter", lambda **kwargs: StubSplunkAdapter())
    monkeypatch.setattr("avg_rms_core.planners.LLMPlanner.plan_action", broken_plan_action)
    avg_rms_core_agent.checkpointer = MemorySaver()

    response = await service.invoke(
        UserInput(
            message="Who accessed EU customer PII in the last 30 days?",
            agent_config={
                "planner_mode": "llm",
                "adapter_mode": "splunk",
                "splunk_base_url": "https://example.splunkcloud.com",
                "splunk_token": "token",
                "audit_log_dir": str(tmp_path),
            },
        ),
        agent_id="avg-rms-core",
    )

    assert "Completed the lookup successfully." in response.content

    rows = [
        json.loads(line)
        for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()
    ]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert action_rows[-1]["planner"] == "scripted_fallback"
    assert action_rows[-1]["planner_reason"] == "openrouter timed out"
    assert action_rows[-1]["args"]["spl"] == "search index=botsv3 sourcetype=wineventlog | head 20"
