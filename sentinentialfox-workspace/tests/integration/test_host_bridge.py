from __future__ import annotations

from sentinentialfox.host_bridge import run_investigation


def test_host_bridge_returns_graph_output() -> None:
    result = run_investigation("Check unusual access")

    assert result["plan"]["goal"] == "Check unusual access"
    assert result["investigation"]["tool_name"] == "splunk.search"
    assert result["adapter_mode"] in {"stub", "rest-backend"}
