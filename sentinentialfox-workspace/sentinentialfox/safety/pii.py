from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d .-]{7,}\d)(?!\w)")
_IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def mask_pii_text(value: str) -> str:
    masked = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    masked = _SSN_PATTERN.sub("[REDACTED_SSN]", masked)
    masked = _IPV4_PATTERN.sub("[REDACTED_IP]", masked)
    masked = _PHONE_PATTERN.sub("[REDACTED_PHONE]", masked)
    return masked


def mask_pii_data(value: Any) -> Any:
    if isinstance(value, str):
        return mask_pii_text(value)
    if isinstance(value, Mapping):
        return {key: mask_pii_data(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [mask_pii_data(item) for item in value]
    return value
