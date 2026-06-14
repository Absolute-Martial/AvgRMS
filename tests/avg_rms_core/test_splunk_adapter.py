import ssl

import pytest

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


def test_search_spl_uses_sdk_export_and_masks_output(tmp_path):
    captured = {}
    ca_bundle = tmp_path / "ca.pem"
    ca_bundle.write_text("placeholder", encoding="utf-8")
    fake_context = object()

    class FakeJobs:
        def export(self, query, **params):
            captured["query"] = query
            captured["params"] = params
            return object()

    class FakeService:
        jobs = FakeJobs()

    def fake_connect(**kwargs):
        captured["connect_kwargs"] = kwargs
        return FakeService()

    def fake_reader(_stream):
        return iter(
            [
                {"_time": "2026-06-14T00:00:00Z", "user": "alice@example.com"},
                {"_time": "2026-06-14T00:00:01Z", "account_id": "123456789"},
            ]
        )

    original_context_factory = ssl.create_default_context
    ssl.create_default_context = lambda cafile=None: fake_context
    try:
        adapter = SplunkAdapter(
            host="example.splunkcloud.com",
            port=8089,
            token="token",
            verify=str(ca_bundle),
            connect_fn=fake_connect,
            results_reader_cls=fake_reader,
        )

        result = adapter.search_spl("search index=botsv3 sourcetype=wineventlog | head 5")
    finally:
        ssl.create_default_context = original_context_factory

    assert captured["connect_kwargs"]["bearerToken"] == "token"
    assert captured["connect_kwargs"]["host"] == "example.splunkcloud.com"
    assert captured["connect_kwargs"]["port"] == 8089
    assert captured["connect_kwargs"]["context"] is fake_context
    assert captured["params"]["output_mode"] == "json"
    assert captured["params"]["segmentation"] == "none"
    assert result.tool == "search_spl"
    assert "alice@example.com" not in result.stdout
    assert "123456789" not in result.stdout
    assert result.output_hash


def test_search_spl_validates_read_only_before_connect():
    called = {"connect": False}

    def fake_connect(**kwargs):
        called["connect"] = True
        raise AssertionError("connect should not be called")

    adapter = SplunkAdapter(
        host="example.splunkcloud.com",
        token="token",
        connect_fn=fake_connect,
    )

    with pytest.raises(ValueError, match="read-only"):
        adapter.search_spl("search index=botsv3 | collect index=prod")

    assert called["connect"] is False


def test_build_connection_kwargs_uses_ca_bundle_context(tmp_path):
    ca_bundle = tmp_path / "ca.pem"
    ca_bundle.write_text("placeholder", encoding="utf-8")
    fake_context = object()
    original_context_factory = ssl.create_default_context
    ssl.create_default_context = lambda cafile=None: fake_context
    try:
        adapter = SplunkAdapter(
            host="example.splunkcloud.com",
            token="token",
            verify=str(ca_bundle),
        )

        kwargs = adapter._connection_kwargs()
    finally:
        ssl.create_default_context = original_context_factory

    assert kwargs["verify"] is True
    assert kwargs["context"] is fake_context
    assert kwargs["bearerToken"] == "token"
