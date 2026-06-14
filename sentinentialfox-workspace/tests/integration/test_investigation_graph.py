from __future__ import annotations

from sentinentialfox.investigation import InvestigationGraph as PackageInvestigationGraph
from sentinentialfox.adapters.splunk_stub import StubSplunkAdapter
from sentinentialfox.investigation.graph import InvestigationGraph


def test_investigation_graph_runs_plan_investigate_synthesize_cycle() -> None:
    graph = InvestigationGraph(adapter=StubSplunkAdapter())

    result = graph.run("Investigate suspicious login activity")

    assert result["plan"]["goal"] == "Investigate suspicious login activity"
    assert result["investigation"]["tool_name"] == "splunk.search"
    assert "Aurora" not in result["plan"]["strategy"]
    assert "summary" in result["synthesis"]


def test_investigation_graph_legacy_imports_share_public_class() -> None:
    assert PackageInvestigationGraph is InvestigationGraph
