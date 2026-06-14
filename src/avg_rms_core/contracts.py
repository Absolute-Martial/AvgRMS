from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Artifact:
    kind: str
    ref: str
    detail: str = ""


@dataclass
class ToolResult:
    tool: str
    args: dict[str, Any]
    stdout: str
    artifacts: list[Artifact] = field(default_factory=list)
    output_hash: str = ""
    confidence: str = "confirmed"
    status: str = "ok"
    error: str = ""


@dataclass
class PlannedAction:
    id: str
    tool: str
    args: dict[str, Any]
    reason: str


@dataclass
class GuardrailDecision:
    action_id: str
    tool: str
    decision: str
    reason: str


@dataclass
class CriticDecision:
    outcome: str
    summary: str


@dataclass
class FinalDecision:
    status: str
    summary: str


@dataclass
class AuditEvent:
    ts: str
    run_id: str
    thread_id: str
    planner: str
    planner_reason: str | None
    event_type: str
    action_id: str
    tool: str
    args: dict[str, Any]
    decision: str
    output_hash: str
    status: str
    correction_of: str | None
    latency_ms: int


class ToolAdapter(Protocol):
    name: str

    def list_tools(self) -> list[dict[str, Any]]: ...

    def run_tool(self, tool: str, args: dict[str, Any]) -> ToolResult: ...
