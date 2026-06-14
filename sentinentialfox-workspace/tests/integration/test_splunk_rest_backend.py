from __future__ import annotations

from sentinentialfox.backends import SplunkRestBackend as PackageSplunkRestBackend
from sentinentialfox.adapters.splunk_rest_backend import SplunkRestBackend


def test_splunk_rest_backend_reports_missing_configuration() -> None:
    adapter = SplunkRestBackend.from_env({})

    assert adapter.status == "unconfigured"
    assert "SPLUNK" in adapter.reason


def test_splunk_rest_backend_returns_unconfigured_result() -> None:
    adapter = SplunkRestBackend.from_env({})

    result = adapter.run_tool("splunk.search", {"query": "search index=main | head 1"})

    assert result.structured_content is not None
    assert result.structured_content["status"] == "unconfigured"
    assert result.structured_content["mode"] == "rest-backend"


def test_splunk_rest_backend_legacy_import_path_matches_backend_export() -> None:
    assert PackageSplunkRestBackend is SplunkRestBackend
