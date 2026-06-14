from __future__ import annotations

from sentinentialfox.safety.tool_contract import ToolResult


def test_tool_result_preserves_content_and_structured_payload() -> None:
    result = ToolResult(
        content="search completed",
        structured_content={"rows": 3, "status": "ok"},
    )

    assert result.content == "search completed"
    assert result.structured_content == {"rows": 3, "status": "ok"}


def test_tool_result_defaults_structured_payload_to_none() -> None:
    result = ToolResult(content="no payload")

    assert result.structured_content is None
