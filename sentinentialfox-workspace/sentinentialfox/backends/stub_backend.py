from __future__ import annotations

import json

from sentinentialfox.safety.guardrails import DestructiveSPLDenied, enforce_safe_spl
from sentinentialfox.safety.tool_contract import ToolResult


class StubSplunkAdapter:
    def list_tools(self) -> list[str]:
        return ["splunk.search"]

    def run_tool(self, name: str, args: dict[str, str]) -> ToolResult:
        query = args.get("query", "")
        try:
            safe_query = enforce_safe_spl(query)
        except DestructiveSPLDenied as exc:
            return ToolResult(
                content="blocked",
                structured_content={
                    "tool_name": name,
                    "status": "blocked",
                    "mode": "stub",
                    "query": query,
                    "error": str(exc),
                },
            )

        payload = {
            "tool_name": name,
            "status": "ok",
            "mode": "stub",
            "query": safe_query,
            "results": [
                {
                    "_time": "2026-06-14T00:00:00Z",
                    "host": "demo-host",
                    "message": "Suspicious login event",
                }
            ],
            "count": 1,
        }
        return ToolResult(content=json.dumps(payload, sort_keys=True), structured_content=payload)
