from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinentialfox.safety.pii import mask_pii_data


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class AuditWriter:
    path: Path

    def append(
        self,
        *,
        event_type: str,
        tool_name: str,
        payload: dict[str, Any] | None = None,
        decision: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "timestamp": _utc_timestamp(),
            "event_type": event_type,
            "tool_name": tool_name,
            "payload": mask_pii_data(payload or {}),
        }
        if decision is not None:
            event["decision"] = decision

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")

        return event
