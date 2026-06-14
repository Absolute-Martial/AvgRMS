from __future__ import annotations

import os
from typing import Any

from sentinentialfox.backends import SplunkRestBackend, StubSplunkAdapter
from sentinentialfox.investigation.graph import InvestigationGraph


def select_backend() -> tuple[Any, str]:
    backend = SplunkRestBackend.from_env(dict(os.environ))
    if backend.is_configured():
        return backend, "rest-backend"
    return StubSplunkAdapter(), "stub"


def run_investigation(prompt: str) -> dict[str, Any]:
    adapter, adapter_mode = select_backend()
    graph = InvestigationGraph(adapter=adapter)
    result = graph.run(prompt)
    result["adapter_mode"] = adapter_mode
    return result
