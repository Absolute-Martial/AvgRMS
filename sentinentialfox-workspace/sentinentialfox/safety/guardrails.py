from __future__ import annotations

import re


DESTRUCTIVE_SPL_COMMANDS = ("delete", "collect", "outputlookup")
_DESTRUCTIVE_SPL_PATTERN = re.compile(
    r"(?:^|\|)\s*(?P<command>delete|collect|outputlookup)\b",
    re.IGNORECASE,
)


class DestructiveSPLDenied(ValueError):
    """Raised when an SPL query includes a destructive command."""


def enforce_safe_spl(query: str) -> str:
    match = _DESTRUCTIVE_SPL_PATTERN.search(query)
    if match:
        command = match.group("command").lower()
        raise DestructiveSPLDenied(f"Destructive SPL command denied: {command}")
    return query
