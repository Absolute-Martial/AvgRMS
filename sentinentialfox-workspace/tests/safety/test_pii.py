from __future__ import annotations

from sentinentialfox.safety.pii import mask_pii_data


def test_mask_pii_data_redacts_nested_values() -> None:
    payload = {
        "user": "alice@example.com",
        "ip": "10.24.8.9",
        "profile": {
            "phone": "+1 415-555-2671",
            "ssn": "123-45-6789",
        },
        "events": ["notify bob@example.com"],
    }

    masked = mask_pii_data(payload)

    assert masked == {
        "user": "[REDACTED_EMAIL]",
        "ip": "[REDACTED_IP]",
        "profile": {
            "phone": "[REDACTED_PHONE]",
            "ssn": "[REDACTED_SSN]",
        },
        "events": ["notify [REDACTED_EMAIL]"],
    }


def test_mask_pii_data_leaves_non_string_scalars_unchanged() -> None:
    payload = {"count": 4, "ok": True, "nested": [None, 3.14]}

    assert mask_pii_data(payload) == payload
