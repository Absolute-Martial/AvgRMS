from __future__ import annotations

from sentinentialfox.backends import StubSplunkAdapter as PackageStubSplunkAdapter
from sentinentialfox.adapters.splunk_stub import StubSplunkAdapter


def test_stub_splunk_adapter_returns_tool_result_for_search() -> None:
    adapter = StubSplunkAdapter()

    result = adapter.run_tool("splunk.search", {"query": "search index=main | head 1"})

    assert result.structured_content is not None
    assert result.structured_content["status"] == "ok"
    assert result.structured_content["mode"] == "stub"
    assert result.structured_content["query"] == "search index=main | head 1"


def test_stub_splunk_adapter_blocks_destructive_query() -> None:
    adapter = StubSplunkAdapter()

    result = adapter.run_tool("splunk.search", {"query": "search index=main | delete"})

    assert result.structured_content is not None
    assert result.structured_content["status"] == "blocked"


def test_stub_splunk_adapter_legacy_import_path_matches_backend_export() -> None:
    assert PackageStubSplunkAdapter is StubSplunkAdapter
