from dataclasses import dataclass, field
from typing import Any

from avg_rms_core.contracts import PlannedAction, ToolResult


@dataclass
class AvgRMSState:
    request_text: str
    planner_mode: str = "scripted"
    adapter_mode: str = "fake"
    available_tools: list[str] = field(default_factory=list)
    attempt_count: int = 0
    max_attempts: int = 2
    current_action: PlannedAction | None = None
    action_history: list[PlannedAction] = field(default_factory=list)
    result_history: list[ToolResult] = field(default_factory=list)
    last_result: ToolResult | None = None
    last_block_reason: str | None = None
    final_response: str = ""
    audit_log_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
