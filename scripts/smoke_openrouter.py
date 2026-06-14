import asyncio
import os
import sys
from pathlib import Path

from avg_rms_core.planners import LLMPlanner
from avg_rms_core.state import AvgRMSState


def _hero_prompt(argv: list[str]) -> str:
    if len(argv) < 2:
        raise SystemExit('usage: OPENROUTER_API_KEY=... PYTHONPATH=src .venv/bin/python -m scripts.smoke_openrouter "<hero prompt>"')
    return argv[1]


async def _main(prompt: str) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")

    planner = LLMPlanner()
    state = AvgRMSState(request_text=prompt, planner_mode="llm", adapter_mode="splunk")
    config = {
        "configurable": {
            "openrouter_api_key": api_key,
        }
    }
    action = await planner.plan_action(state, config, "action-001")
    raw_output = planner.last_raw_output or ""

    lines = [
        f"hero_prompt={prompt}",
        f"generated_spl={action.args['spl']}",
        "raw_tool_call=",
        raw_output,
    ]
    payload = "\n".join(lines).strip() + "\n"
    print(payload)

    evidence_path = Path("docs/evidence/real_openrouter_call.txt")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(payload, encoding="utf-8")
    print(f"saved_evidence={evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main(_hero_prompt(sys.argv))))
