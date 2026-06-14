import json

import pytest

from agents.avg_rms_core_agent import avg_rms_core_agent
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
