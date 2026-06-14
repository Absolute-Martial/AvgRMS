from __future__ import annotations

from typing import Any, Protocol


class SearchToolRunner(Protocol):
    def run_tool(self, name: str, args: dict[str, Any]) -> Any:
        ...


class InvestigationService:
    def __init__(self, adapter: SearchToolRunner) -> None:
        self.adapter = adapter

    def plan_node(self, prompt: str) -> dict[str, str]:
        return {
            "goal": prompt,
            "strategy": "Use the local search backend through a safe tool boundary.",
            "query": "search index=main | head 1",
        }

    def investigate_node(self, plan: dict[str, str]) -> dict[str, Any]:
        result = self.adapter.run_tool("splunk.search", {"query": plan["query"]})
        payload = result.structured_content or {}
        return {
            "tool_name": payload.get("tool_name", "splunk.search"),
            "status": payload.get("status", "unknown"),
            "mode": payload.get("mode", "unknown"),
            "query": payload.get("query", plan["query"]),
            "results": payload.get("results", []),
            "raw_output": result.content,
        }

    def synthesize_node(self, prompt: str, investigation: dict[str, Any]) -> dict[str, str]:
        summary = (
            f"Prompt '{prompt}' executed via {investigation['mode']} "
            f"with status {investigation['status']} against {investigation['tool_name']}."
        )
        return {"summary": summary}

    def run(self, prompt: str) -> dict[str, dict[str, Any]]:
        plan = self.plan_node(prompt)
        investigation = self.investigate_node(plan)
        synthesis = self.synthesize_node(prompt, investigation)
        return {
            "plan": plan,
            "investigation": investigation,
            "synthesis": synthesis,
        }
