from __future__ import annotations

from typing import Any


def build_investigation_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    plan = result.get("plan", {})
    investigation = result.get("investigation", {})
    synthesis = result.get("synthesis", {})
    rows = investigation.get("results", []) or []

    return {
        "goal": plan.get("goal", ""),
        "query": investigation.get("query", plan.get("query", "")),
        "status": investigation.get("status", "unknown"),
        "tool_name": investigation.get("tool_name", "splunk.search"),
        "adapter_mode": result.get("adapter_mode", "unknown"),
        "summary": synthesis.get("summary", ""),
        "result_count": len(rows),
        "results": rows,
    }
