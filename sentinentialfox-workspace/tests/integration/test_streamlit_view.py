from __future__ import annotations

from sentinentialfox.presentation.streamlit_view import build_investigation_snapshot


def test_build_investigation_snapshot_extracts_display_fields() -> None:
    result = {
        "adapter_mode": "stub",
        "plan": {
            "goal": "Investigate unusual access",
            "query": "search index=main | head 1",
        },
        "investigation": {
            "status": "ok",
            "tool_name": "splunk.search",
            "results": [{"host": "demo-host"}],
        },
        "synthesis": {"summary": "Investigation complete"},
    }

    snapshot = build_investigation_snapshot(result)

    assert snapshot["goal"] == "Investigate unusual access"
    assert snapshot["adapter_mode"] == "stub"
    assert snapshot["tool_name"] == "splunk.search"
    assert snapshot["result_count"] == 1
    assert snapshot["summary"] == "Investigation complete"
