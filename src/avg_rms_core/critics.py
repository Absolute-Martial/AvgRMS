from avg_rms_core.contracts import CriticDecision, ToolResult
from avg_rms_core.state import AvgRMSState


class DeterministicCritic:
    def assess(self, state: AvgRMSState, result: ToolResult) -> CriticDecision:
        if result.status == "ok":
            return CriticDecision(outcome="success", summary="Action succeeded.")
        if result.status == "blocked":
            return CriticDecision(outcome="blocked", summary="Action was blocked.")
        if state.attempt_count >= state.max_attempts:
            return CriticDecision(
                outcome="attempts_exhausted",
                summary="Retries exhausted after adapter runtime failures.",
            )
        return CriticDecision(outcome="retry", summary="Retryable adapter runtime failure.")
