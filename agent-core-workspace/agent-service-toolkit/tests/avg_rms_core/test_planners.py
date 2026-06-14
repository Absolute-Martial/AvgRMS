from avg_rms_core.planners import ScriptedPlanner
from avg_rms_core.state import AvgRMSState
from avg_rms_core.critics import DeterministicCritic
from avg_rms_core.contracts import ToolResult


def test_scripted_planner_returns_deterministic_action_ids():
    planner = ScriptedPlanner()
    state = AvgRMSState(request_text="investigate fake incident", max_attempts=2)

    first = planner.plan_next(state)
    state.action_history.append(first)
    second = planner.replan_after_result(state)

    assert first.id == "action-001"
    assert second.id == "action-002"


def test_scripted_planner_retry_after_runtime_error():
    planner = ScriptedPlanner()
    state = AvgRMSState(request_text="investigate fake incident", max_attempts=2)

    first = planner.plan_next(state)
    state.action_history.append(first)
    state.last_result = ToolResult(
        tool="fake.lookup",
        args={"target": "alpha"},
        stdout="FAKE_LOOKUP_ERROR target=alpha\n",
        output_hash="hash-1",
        status="error",
        error="simulated runtime error",
    )

    second = planner.replan_after_result(state)

    assert second.id == "action-002"
    assert second.tool == "fake.lookup"
    assert second.args == {"target": "alpha", "retry": 1}


def test_deterministic_critic_marks_attempts_exhausted():
    critic = DeterministicCritic()
    state = AvgRMSState(request_text="investigate", max_attempts=1, attempt_count=1)
    result = ToolResult(
        tool="fake.lookup",
        args={"target": "alpha"},
        stdout="FAKE_LOOKUP_ERROR target=alpha\n",
        output_hash="hash-1",
        status="error",
        error="simulated runtime error",
    )

    decision = critic.assess(state, result)

    assert decision.outcome == "attempts_exhausted"
