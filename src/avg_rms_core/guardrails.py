from avg_rms_core.contracts import GuardrailDecision, PlannedAction


class GuardrailGate:
    def __init__(self, allow_list: set[str]) -> None:
        self.allow_list = allow_list

    def check(self, action: PlannedAction) -> GuardrailDecision:
        if action.tool not in self.allow_list:
            return GuardrailDecision(
                action_id=action.id,
                tool=action.tool,
                decision="blocked",
                reason="tool_not_allow_listed",
            )
        return GuardrailDecision(
            action_id=action.id,
            tool=action.tool,
            decision="allowed",
            reason="tool_allow_listed",
        )
