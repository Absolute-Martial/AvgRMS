import json

from avg_rms_core.audit import JsonlAuditLogger
from avg_rms_core.contracts import AuditEvent
from avg_rms_core.contracts import PlannedAction
from avg_rms_core.guardrails import GuardrailGate


def test_guardrail_blocks_non_allow_listed_tool():
    gate = GuardrailGate(allow_list={"fake.lookup"})
    action = PlannedAction(id="action-001", tool="rm", args={}, reason="bad")

    decision = gate.check(action)

    assert decision.decision == "blocked"
    assert decision.reason == "tool_not_allow_listed"


def test_audit_logger_writes_required_structural_fields(tmp_path):
    logger = JsonlAuditLogger(tmp_path / "audit.jsonl")
    event = AuditEvent(
        ts="2026-06-14T00:00:00Z",
        run_id="run-1",
        thread_id="thread-1",
        planner="scripted",
        planner_reason=None,
        event_type="action_result",
        action_id="action-001",
        tool="fake.lookup",
        args={"target": "alpha"},
        decision="allowed",
        output_hash="hash-1",
        status="error",
        correction_of=None,
        latency_ms=5,
    )

    logger.write(event)
    row = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])

    assert row["event_type"] == "action_result"
    assert row["action_id"] == "action-001"
    assert row["tool"] == "fake.lookup"
    assert row["decision"] == "allowed"
    assert row["status"] == "error"
