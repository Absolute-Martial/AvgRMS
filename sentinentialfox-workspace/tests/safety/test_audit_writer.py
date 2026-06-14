from __future__ import annotations

import json

from sentinentialfox.safety.audit import AuditWriter


def test_audit_writer_appends_masked_jsonl_event(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    writer = AuditWriter(path)

    writer.append(
        event_type="tool_call",
        tool_name="splunk_search",
        payload={"user": "alice@example.com", "query": "search index=main"},
        decision="allowed",
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    event = json.loads(lines[0])
    assert event["event_type"] == "tool_call"
    assert event["tool_name"] == "splunk_search"
    assert event["decision"] == "allowed"
    assert event["payload"] == {
        "user": "[REDACTED_EMAIL]",
        "query": "search index=main",
    }
    assert isinstance(event["timestamp"], str)
