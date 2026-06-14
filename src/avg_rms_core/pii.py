import re


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ID_RE = re.compile(r"\b\d{6,}\b")


def mask_pii(text: str) -> str:
    masked = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return ID_RE.sub("[REDACTED_ID]", masked)
