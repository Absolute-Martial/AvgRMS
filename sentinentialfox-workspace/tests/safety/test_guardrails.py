from __future__ import annotations

import pytest

from sentinentialfox.safety.guardrails import DestructiveSPLDenied, enforce_safe_spl


def test_enforce_safe_spl_allows_read_only_query() -> None:
    query = 'search index=main error | stats count by host | eval note="delete word in text"'

    assert enforce_safe_spl(query) == query


@pytest.mark.parametrize(
    "query",
    [
        "search index=main | delete",
        "search index=main | collect index=summary",
        "search index=main | outputlookup compromised.csv",
    ],
)
def test_enforce_safe_spl_rejects_destructive_query(query: str) -> None:
    with pytest.raises(DestructiveSPLDenied):
        enforce_safe_spl(query)
