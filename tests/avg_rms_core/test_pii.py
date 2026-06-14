from avg_rms_core.pii import mask_pii


def test_mask_pii_redacts_email_and_ids():
    masked = mask_pii("alice@example.com accessed account 123456789")

    assert "alice@example.com" not in masked
    assert "123456789" not in masked
    assert "[REDACTED_EMAIL]" in masked
    assert "[REDACTED_ID]" in masked
