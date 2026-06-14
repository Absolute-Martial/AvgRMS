from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ComplianceFinding:
    title: str
    severity: str
    summary: str
