from __future__ import annotations

from sentinentialfox.host_bridge import run_investigation
from sentinentialfox.runtime import run_investigation as runtime_run_investigation


def test_runtime_service_legacy_host_bridge_matches_runtime_export() -> None:
    assert runtime_run_investigation is run_investigation
