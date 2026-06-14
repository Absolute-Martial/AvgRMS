from avg_rms_core.contracts import Artifact
from avg_rms_core.splunk_adapter import SplunkAdapter, deny_destructive_spl


def test_search_spl_returns_toolresult_with_artifacts():
    adapter = SplunkAdapter(
        base_url="https://example.splunkcloud.com",
        token="token",
        app="search",
        verify_ssl=True,
    )

    result = adapter._normalize_search_result(
        spl="search index=botsv3 sourcetype=wineventlog",
        rows=[{"_time": "2026-06-14T00:00:00Z", "user": "alice@example.com"}],
    )

    assert result.tool == "search_spl"
    assert result.status == "ok"
    assert result.artifacts[0] == Artifact(
        kind="spl_query",
        ref="search index=botsv3 sourcetype=wineventlog",
    )
    assert result.artifacts[1].kind == "spl_event"


def test_deny_destructive_spl_blocks_delete_and_collect():
    assert deny_destructive_spl("| delete") == "blocked"
    assert deny_destructive_spl("search index=main | collect index=prod") == "blocked"
    assert deny_destructive_spl("search index=botsv3 | head 5") == "allowed"
