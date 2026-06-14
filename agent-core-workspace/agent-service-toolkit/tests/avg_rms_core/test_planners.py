from avg_rms_core.planners import ScriptedPlanner
from avg_rms_core.state import AvgRMSState


def test_scripted_planner_returns_deterministic_action_ids():
    planner = ScriptedPlanner()
    state = AvgRMSState(request_text="investigate fake incident", max_attempts=2)

    first = planner.plan_next(state)
    state.action_history.append(first)
    second = planner.replan_after_result(state)

    assert first.id == "action-001"
    assert second.id == "action-002"
