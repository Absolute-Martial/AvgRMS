from avg_rms_core.contracts import PlannedAction
from avg_rms_core.guardrails import GuardrailGate


def test_guardrail_blocks_non_allow_listed_tool():
    gate = GuardrailGate(allow_list={"fake.lookup"})
    action = PlannedAction(id="action-001", tool="rm", args={}, reason="bad")

    decision = gate.check(action)

    assert decision.decision == "blocked"
    assert decision.reason == "tool_not_allow_listed"
