from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_demo import run_demo


def test_run_demo_writes_audit_artifact(tmp_path: Path) -> None:
    output = run_demo("Review failed logins", tmp_path / "audit.jsonl")

    assert "synthesis" in output
    assert (tmp_path / "audit.jsonl").exists()
