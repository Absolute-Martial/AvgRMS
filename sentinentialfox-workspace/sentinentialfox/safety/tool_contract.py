from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class ToolResult:
    content: str
    structured_content: dict[str, Any] | None = None
