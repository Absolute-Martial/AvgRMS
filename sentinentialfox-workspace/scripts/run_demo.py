from __future__ import annotations

from pathlib import Path
import sys

from sentinentialfox.host_bridge import run_investigation
from sentinentialfox.safety.audit import AuditWriter


def run_demo(prompt: str, audit_path: Path) -> dict:
    result = run_investigation(prompt)
    writer = AuditWriter(audit_path)
    writer.append(
        event_type="investigation_run",
        tool_name=result["investigation"]["tool_name"],
        payload={
            "prompt": prompt,
            "adapter_mode": result["adapter_mode"],
            "status": result["investigation"]["status"],
            "query": result["investigation"]["query"],
        },
        decision="demo",
    )
    return result


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Investigate suspicious login activity"
    output = run_demo(prompt, Path("artifacts/demo-audit.jsonl"))
    print(output["synthesis"]["summary"])
