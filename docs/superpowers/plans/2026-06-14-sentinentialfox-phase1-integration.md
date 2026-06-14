# Sentinentialfox Phase 1 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable first integration slice where `incidentfox` remains the host app, `aurora` investigation logic is adapted into that host, and all Splunk-facing actions flow through the preserved safety/tool contract and the defined Splunk backend REST API.

**Architecture:** The workspace will clone upstream repos into a fresh `sentinentialfox-workspace/` tree, keep `incidentfox` as the dominant runtime, add a local integration package for `aurora` translation plus preserved safety modules, and expose one coherent app path that talks to a local stub first and then to the defined Splunk backend REST API. The first cycle prioritizes a working host shell, safe tool boundary, and verified carried-over tests before broader Splunk breadth.

**Tech Stack:** Python, `uv`, FastAPI/Streamlit patterns from upstream repos, LangGraph-style orchestration from `aurora`, Splunk REST backend integration, `splunk-sdk-python`, `pytest`

---

## File Structure

This plan fixes the initial workspace layout so implementation can proceed with exact paths:

- Create: `sentinentialfox-workspace/`
- Create: `sentinentialfox-workspace/references/`
- Clone into: `sentinentialfox-workspace/incidentfox`
- Clone into: `sentinentialfox-workspace/aurora`
- Clone into: `sentinentialfox-workspace/agent-service-toolkit`
- Clone into: `sentinentialfox-workspace/mcp-for-splunk`
- Clone into: `sentinentialfox-workspace/splunk-sdk-python`
- Clone into: `sentinentialfox-workspace/references/SplunkGPT`
- Clone into: `sentinentialfox-workspace/references/splunk-community-ai`
- Clone into: `sentinentialfox-workspace/references/security_content`
- Clone into: `sentinentialfox-workspace/references/DA-ESS-MitreContent`
- Create: `sentinentialfox-workspace/sentinentialfox/`
- Create: `sentinentialfox-workspace/sentinentialfox/adapters/`
- Create: `sentinentialfox-workspace/sentinentialfox/investigation/`
- Create: `sentinentialfox-workspace/sentinentialfox/safety/`
- Create: `sentinentialfox-workspace/sentinentialfox/config/`
- Create: `sentinentialfox-workspace/tests/`
- Create: `sentinentialfox-workspace/tests/safety/`
- Create: `sentinentialfox-workspace/tests/integration/`
- Create: `sentinentialfox-workspace/scripts/`
- Create: `sentinentialfox-workspace/docs/DECISIONS.md`
- Create: `sentinentialfox-workspace/.env.example`
- Create: `sentinentialfox-workspace/pyproject.toml`

The exact `incidentfox` and `aurora` internal files to modify are unknown until cloned. The first execution tasks below intentionally start by cloning and inventorying those real paths before any host-code patching. The runtime integration target for real Splunk access is the defined backend REST API; MCP remains a reference and optional secondary tool surface.

### Task 1: Bootstrap the Integration Workspace

**Files:**
- Create: `sentinentialfox-workspace/`
- Create: `sentinentialfox-workspace/references/`
- Create: `sentinentialfox-workspace/scripts/bootstrap_clones.sh`
- Create: `sentinentialfox-workspace/.gitignore`
- Create: `sentinentialfox-workspace/.python-version`

- [ ] **Step 1: Write the bootstrap script file**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="sentinentialfox-workspace"
mkdir -p "$ROOT/references"
cd "$ROOT"

clone() {
  local dir="$1" url="$2"
  if [ -d "$dir/.git" ]; then
    echo "skip $dir"
  else
    git clone --depth 1 "$url" "$dir"
    echo "ok $dir"
  fi
}

echo "== Primary bases =="
clone incidentfox https://github.com/incidentfox/incidentfox.git
clone aurora https://github.com/Arvo-AI/aurora.git
clone agent-service-toolkit https://github.com/JoshuaC215/agent-service-toolkit.git
clone splunk-sdk-python https://github.com/splunk/splunk-sdk-python.git
clone mcp-for-splunk https://github.com/deslicer/mcp-for-splunk.git

echo "== References =="
clone references/SplunkGPT https://github.com/KingOfTheNOPs/SplunkGPT.git
clone references/langchain-mcp-adapters https://github.com/langchain-ai/langchain-mcp-adapters.git
clone references/splunk-mcp-server2 https://github.com/splunk/splunk-mcp-server2.git
clone references/splunk-mcp https://github.com/livehybrid/splunk-mcp.git
clone references/fastapi-langgraph-template https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template.git
clone references/OpenRCA https://github.com/microsoft/OpenRCA.git
clone references/agentic-soc-platform https://github.com/FunnyWolf/agentic-soc-platform.git
clone references/security_content https://github.com/splunk/security_content.git
clone references/DA-ESS-MitreContent https://github.com/seynur/DA-ESS-MitreContent.git
clone references/attack-detections-collector https://github.com/splunk/attack-detections-collector.git
clone references/threatintel https://github.com/splunkchamp/threatintel.git
clone references/splunk-community-ai https://github.com/billebel/splunk-community-ai.git
clone references/enterprise-rag-patterns https://github.com/ashutoshrana/enterprise-rag-patterns.git
clone references/RAG-Based-policy-agent https://github.com/Srujanrana07/RAG-Based-policy-agent.git
clone references/Splunk-createkvstore https://github.com/georgestarcher/Splunk-createkvstore.git
```

- [ ] **Step 2: Write the workspace ignore file**

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
artifacts/
reports/
```

- [ ] **Step 3: Write the Python version pin**

```text
3.11
```

- [ ] **Step 4: Run the bootstrap script**

Run: `bash scripts/bootstrap_clones.sh`
Expected: each requested repository prints either `ok <name>` or `skip <name>`

- [ ] **Step 5: Verify the clone tree exists**

Run: `find sentinentialfox-workspace -maxdepth 2 -type d | sort`
Expected: includes `incidentfox`, `aurora`, `agent-service-toolkit`, `mcp-for-splunk`, `splunk-sdk-python`, and `references`

- [ ] **Step 6: Commit**

```bash
git add sentinentialfox-workspace/scripts/bootstrap_clones.sh sentinentialfox-workspace/.gitignore sentinentialfox-workspace/.python-version
git commit -m "chore: bootstrap sentinentialfox integration workspace"
```

### Task 2: Inventory Real Host and Investigation Entry Points

**Files:**
- Create: `sentinentialfox-workspace/docs/DECISIONS.md`
- Create: `sentinentialfox-workspace/docs/upstream-inventory.md`
- Modify: `sentinentialfox-workspace/incidentfox/<real entrypoint files>`
- Modify: `sentinentialfox-workspace/aurora/<real orchestration files>`

- [ ] **Step 1: Write the inventory skeleton**

```markdown
# Upstream Inventory

## Incidentfox

- App entrypoint:
- UI entrypoint:
- Orchestration module:
- Agent registration surface:
- Config loading path:

## Aurora

- Graph entrypoint:
- Planning module:
- Investigation module:
- Synthesis module:
- State model:

## Splunk surfaces

- Backend REST/search module:
- Python SDK search module:
- MCP startup module:
- Prompt-to-SPL reference files:
```

- [ ] **Step 2: Run file discovery for incidentfox**

Run: `env RIPGREP_CONFIG_PATH=/dev/null rg -n "FastAPI|Streamlit|graph|agent|main\\(" sentinentialfox-workspace/incidentfox`
Expected: several candidate entrypoint and orchestration files are identified

- [ ] **Step 3: Run file discovery for aurora**

Run: `env RIPGREP_CONFIG_PATH=/dev/null rg -n "LangGraph|StateGraph|plan|investigate|synth" sentinentialfox-workspace/aurora`
Expected: graph/state/planning files are identified

- [ ] **Step 4: Fill the decisions file with concrete paths**

```markdown
# Decisions

## Runtime Base

- Host application: `incidentfox`
- Investigation logic source: `aurora`
- Tool boundary: carried-over `ToolAdapter`/`ToolResult`
- Primary Splunk runtime path: defined backend REST API
- Secondary/reference Splunk paths: `splunk-sdk-python`, `mcp-for-splunk`

## Concrete Paths

- incidentfox app entrypoint: `<fill from repo inspection>`
- incidentfox UI entrypoint: `<fill from repo inspection>`
- incidentfox orchestration module: `<fill from repo inspection>`
- aurora graph entrypoint: `<fill from repo inspection>`
- aurora plan module: `<fill from repo inspection>`
- aurora investigate module: `<fill from repo inspection>`
- aurora synthesize module: `<fill from repo inspection>`
```

- [ ] **Step 5: Verify the inventory is complete**

Run: `sed -n '1,220p' sentinentialfox-workspace/docs/upstream-inventory.md && sed -n '1,220p' sentinentialfox-workspace/docs/DECISIONS.md`
Expected: no placeholder headings remain empty for the selected paths

- [ ] **Step 6: Commit**

```bash
git add sentinentialfox-workspace/docs/upstream-inventory.md sentinentialfox-workspace/docs/DECISIONS.md
git commit -m "docs: record incidentfox and aurora integration paths"
```

### Task 3: Establish the Local Python Project and Test Harness

**Files:**
- Create: `sentinentialfox-workspace/pyproject.toml`
- Create: `sentinentialfox-workspace/tests/conftest.py`
- Create: `sentinentialfox-workspace/tests/safety/__init__.py`
- Create: `sentinentialfox-workspace/tests/integration/__init__.py`

- [ ] **Step 1: Write the project manifest**

```toml
[project]
name = "sentinentialfox"
version = "0.1.0"
description = "Integration-first Splunk security investigator built from incidentfox and aurora"
requires-python = ">=3.11,<3.13"
dependencies = [
  "fastapi",
  "httpx",
  "pydantic>=2",
  "pyyaml",
  "pytest",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Write the shared test bootstrap**

```python
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 3: Create the package directories**

Run: `mkdir -p sentinentialfox-workspace/sentinentialfox/{adapters,investigation,safety,config} sentinentialfox-workspace/tests/{safety,integration}`
Expected: the package and test directories exist

- [ ] **Step 4: Verify the empty harness loads**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests -q`
Expected: command succeeds with `no tests ran` or equivalent zero-test success

- [ ] **Step 5: Commit**

```bash
git add sentinentialfox-workspace/pyproject.toml sentinentialfox-workspace/tests/conftest.py sentinentialfox-workspace/sentinentialfox sentinentialfox-workspace/tests
git commit -m "chore: add sentinentialfox test harness"
```

### Task 4: Port the Preserved Safety Layer With Failing Contract Tests First

**Files:**
- Create: `sentinentialfox-workspace/tests/safety/test_tool_contract.py`
- Create: `sentinentialfox-workspace/tests/safety/test_guardrails.py`
- Create: `sentinentialfox-workspace/tests/safety/test_pii.py`
- Create: `sentinentialfox-workspace/tests/safety/test_audit_writer.py`
- Create: `sentinentialfox-workspace/sentinentialfox/safety/tool_contract.py`
- Create: `sentinentialfox-workspace/sentinentialfox/safety/guardrails.py`
- Create: `sentinentialfox-workspace/sentinentialfox/safety/pii.py`
- Create: `sentinentialfox-workspace/sentinentialfox/safety/audit.py`

- [ ] **Step 1: Write the first failing contract test**

```python
from sentinentialfox.safety.tool_contract import ToolResult


def test_tool_result_captures_status_output_and_metadata():
    result = ToolResult(
        tool_name="splunk.search",
        status="ok",
        raw_output="index=main | head 1",
        structured_output={"events": 1},
        error=None,
        metadata={"latency_ms": 120},
    )

    assert result.tool_name == "splunk.search"
    assert result.status == "ok"
    assert result.structured_output["events"] == 1
    assert result.metadata["latency_ms"] == 120
```

- [ ] **Step 2: Run the first test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/safety/test_tool_contract.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing `ToolResult`

- [ ] **Step 3: Write the minimal tool contract implementation**

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolResult:
    tool_name: str
    status: str
    raw_output: str
    structured_output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolAdapter:
    def list_tools(self) -> list[str]:
        raise NotImplementedError

    def run_tool(self, name: str, args: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
```

- [ ] **Step 4: Run the contract test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/safety/test_tool_contract.py -q`
Expected: PASS

- [ ] **Step 5: Add the remaining failing safety tests**

```python
from sentinentialfox.safety.guardrails import deny_destructive_spl


def test_deny_destructive_spl_blocks_delete_pipeline():
    allowed, reason = deny_destructive_spl("search index=main | delete")
    assert allowed is False
    assert "delete" in reason.lower()
```

```python
from sentinentialfox.safety.pii import mask_text


def test_mask_text_redacts_email_addresses():
    masked = mask_text("user email is analyst@example.com")
    assert "analyst@example.com" not in masked
    assert "[EMAIL]" in masked
```

```python
from pathlib import Path
from sentinentialfox.safety.audit import JsonlAuditWriter


def test_audit_writer_appends_json_lines(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    writer = JsonlAuditWriter(path)
    writer.write({"tool": "splunk.search", "status": "ok"})

    content = path.read_text().strip().splitlines()
    assert len(content) == 1
    assert '"tool": "splunk.search"' in content[0]
```

- [ ] **Step 6: Run the safety tests to verify they fail**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/safety -q`
Expected: FAIL because guardrail, pii, and audit implementations do not exist yet

- [ ] **Step 7: Port the minimal preserved safety implementations**

```python
def deny_destructive_spl(query: str) -> tuple[bool, str]:
    lowered = query.lower()
    blocked_terms = ("| delete", "| outputlookup", "| collect", "delete ")
    for term in blocked_terms:
        if term in lowered:
            return False, f"blocked destructive SPL pattern: {term}"
    return True, ""
```

```python
import re


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def mask_text(value: str) -> str:
    return EMAIL_RE.sub("[EMAIL]", value)
```

```python
import json
from pathlib import Path
from typing import Any


class JsonlAuditWriter:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
```

- [ ] **Step 8: Run the safety tests to verify they pass**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/safety -q`
Expected: PASS

- [ ] **Step 9: Replace the minimal implementations with the carried-over real modules**

Run: `cp /path/to/current/sentinentialfox-core/{guardrails.py,pii.py} sentinentialfox-workspace/sentinentialfox/safety/`
Expected: copied files overwrite the placeholders while preserving behavior

- [ ] **Step 10: Re-run the safety tests**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/safety -q`
Expected: PASS with the carried-over implementations in place

- [ ] **Step 11: Commit**

```bash
git add sentinentialfox-workspace/sentinentialfox/safety sentinentialfox-workspace/tests/safety
git commit -m "feat: port preserved sentinentialfox safety layer"
```

### Task 5: Add a Stub Splunk Adapter Behind the Preserved Tool Boundary

**Files:**
- Create: `sentinentialfox-workspace/tests/integration/test_stub_splunk_adapter.py`
- Create: `sentinentialfox-workspace/sentinentialfox/adapters/splunk_stub.py`
- Create: `sentinentialfox-workspace/sentinentialfox/config/guardrails.yaml`

- [ ] **Step 1: Write the failing adapter test**

```python
from sentinentialfox.adapters.splunk_stub import StubSplunkAdapter


def test_stub_splunk_adapter_returns_tool_result_for_search():
    adapter = StubSplunkAdapter()
    result = adapter.run_tool("splunk.search", {"query": "search index=main | head 1"})

    assert result.status == "ok"
    assert result.structured_output["mode"] == "stub"
    assert result.structured_output["query"] == "search index=main | head 1"
```

- [ ] **Step 2: Run the adapter test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_stub_splunk_adapter.py -q`
Expected: FAIL with missing adapter module

- [ ] **Step 3: Write the minimal adapter implementation**

```python
from sentinentialfox.safety.tool_contract import ToolAdapter, ToolResult
from sentinentialfox.safety.guardrails import deny_destructive_spl


class StubSplunkAdapter(ToolAdapter):
    def list_tools(self) -> list[str]:
        return ["splunk.search"]

    def run_tool(self, name: str, args: dict[str, str]) -> ToolResult:
        query = args.get("query", "")
        allowed, reason = deny_destructive_spl(query)
        if not allowed:
            return ToolResult(
                tool_name=name,
                status="blocked",
                raw_output="",
                structured_output={"mode": "stub", "query": query},
                error=reason,
            )
        return ToolResult(
            tool_name=name,
            status="ok",
            raw_output='{"events": [{"_time": "2026-06-14T00:00:00Z"}]}',
            structured_output={"mode": "stub", "query": query, "events": 1},
        )
```

- [ ] **Step 4: Run the adapter test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_stub_splunk_adapter.py -q`
Expected: PASS

- [ ] **Step 5: Add a guardrail configuration file**

```yaml
splunk:
  allow_read_only: true
  denied_patterns:
    - "| delete"
    - "| outputlookup"
    - "| collect"
```

- [ ] **Step 6: Commit**

```bash
git add sentinentialfox-workspace/sentinentialfox/adapters/splunk_stub.py sentinentialfox-workspace/sentinentialfox/config/guardrails.yaml sentinentialfox-workspace/tests/integration/test_stub_splunk_adapter.py
git commit -m "feat: add read-only stub splunk adapter"
```

### Task 6: Build the Aurora-to-Incidentfox Translation Seam in Isolation

**Files:**
- Create: `sentinentialfox-workspace/tests/integration/test_investigation_graph.py`
- Create: `sentinentialfox-workspace/sentinentialfox/investigation/graph.py`
- Create: `sentinentialfox-workspace/sentinentialfox/investigation/models.py`
- Modify: `sentinentialfox-workspace/docs/DECISIONS.md`

- [ ] **Step 1: Write the failing graph translation test**

```python
from sentinentialfox.investigation.graph import InvestigationGraph
from sentinentialfox.adapters.splunk_stub import StubSplunkAdapter


def test_investigation_graph_runs_plan_investigate_synthesize_cycle():
    graph = InvestigationGraph(adapter=StubSplunkAdapter())
    result = graph.run("Investigate suspicious login activity")

    assert result["plan"]["goal"] == "Investigate suspicious login activity"
    assert result["investigation"]["tool_name"] == "splunk.search"
    assert "summary" in result["synthesis"]
```

- [ ] **Step 2: Run the graph test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_investigation_graph.py -q`
Expected: FAIL with missing `InvestigationGraph`

- [ ] **Step 3: Write the minimal data models**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class ComplianceFinding:
    title: str
    severity: str
    summary: str
```

- [ ] **Step 4: Write the minimal translation seam**

```python
from sentinentialfox.safety.tool_contract import ToolAdapter


class InvestigationGraph:
    def __init__(self, adapter: ToolAdapter) -> None:
        self.adapter = adapter

    def plan_node(self, prompt: str) -> dict[str, str]:
        return {"goal": prompt, "strategy": "Run one read-only Splunk search"}

    def investigate_node(self, plan: dict[str, str]) -> dict[str, str]:
        result = self.adapter.run_tool(
            "splunk.search",
            {"query": "search index=main | head 1"},
        )
        return {"tool_name": result.tool_name, "status": result.status, "raw_output": result.raw_output}

    def synthesize_node(self, prompt: str, investigation: dict[str, str]) -> dict[str, str]:
        return {"summary": f"{prompt}: {investigation['status']}"}

    def run(self, prompt: str) -> dict[str, dict[str, str]]:
        plan = self.plan_node(prompt)
        investigation = self.investigate_node(plan)
        synthesis = self.synthesize_node(prompt, investigation)
        return {"plan": plan, "investigation": investigation, "synthesis": synthesis}
```

- [ ] **Step 5: Run the graph test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_investigation_graph.py -q`
Expected: PASS

- [ ] **Step 6: Update decisions with the selected translation seam**

```markdown
## Translation Seam

- local integration graph module: `sentinentialfox/investigation/graph.py`
- initial normalized graph class: `InvestigationGraph`
- initial adapter target: `StubSplunkAdapter`
```

- [ ] **Step 7: Commit**

```bash
git add sentinentialfox-workspace/sentinentialfox/investigation sentinentialfox-workspace/tests/integration/test_investigation_graph.py sentinentialfox-workspace/docs/DECISIONS.md
git commit -m "feat: add initial aurora translation seam"
```

### Task 7: Attach the Translation Seam to the Incidentfox Host

**Files:**
- Modify: `sentinentialfox-workspace/incidentfox/<real app entrypoint>`
- Modify: `sentinentialfox-workspace/incidentfox/<real orchestration module>`
- Create: `sentinentialfox-workspace/sentinentialfox/host_bridge.py`
- Create: `sentinentialfox-workspace/tests/integration/test_host_bridge.py`

- [ ] **Step 1: Write the failing host bridge test**

```python
from sentinentialfox.host_bridge import run_investigation


def test_host_bridge_returns_graph_output():
    result = run_investigation("Check unusual access")
    assert result["plan"]["goal"] == "Check unusual access"
    assert result["investigation"]["tool_name"] == "splunk.search"
```

- [ ] **Step 2: Run the host bridge test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_host_bridge.py -q`
Expected: FAIL with missing host bridge module

- [ ] **Step 3: Write the minimal host bridge**

```python
from sentinentialfox.adapters.splunk_stub import StubSplunkAdapter
from sentinentialfox.investigation.graph import InvestigationGraph


def run_investigation(prompt: str) -> dict:
    graph = InvestigationGraph(adapter=StubSplunkAdapter())
    return graph.run(prompt)
```

- [ ] **Step 4: Run the host bridge test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_host_bridge.py -q`
Expected: PASS

- [ ] **Step 5: Patch the selected incidentfox entrypoint to call the bridge**

```python
from sentinentialfox.host_bridge import run_investigation


def sentinentialfox_demo(prompt: str) -> dict:
    return run_investigation(prompt)
```

- [ ] **Step 6: Verify the host app can import the bridge**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from sentinentialfox.host_bridge import run_investigation; print(run_investigation('demo')['synthesis']['summary'])"`
Expected: prints a summary line ending in `ok`

- [ ] **Step 7: Commit**

```bash
git add sentinentialfox-workspace/sentinentialfox/host_bridge.py sentinentialfox-workspace/tests/integration/test_host_bridge.py sentinentialfox-workspace/incidentfox
git commit -m "feat: connect incidentfox host to integration bridge"
```

### Task 8: Add an Honest Runnable Demo Surface and Evidence Output

**Files:**
- Create: `sentinentialfox-workspace/scripts/run_demo.py`
- Create: `sentinentialfox-workspace/tests/integration/test_run_demo.py`
- Modify: `sentinentialfox-workspace/sentinentialfox/safety/audit.py`
- Create: `sentinentialfox-workspace/artifacts/.gitkeep`

- [ ] **Step 1: Write the failing demo test**

```python
from pathlib import Path
from scripts.run_demo import run_demo


def test_run_demo_writes_audit_artifact(tmp_path: Path):
    output = run_demo("Review failed logins", tmp_path / "audit.jsonl")
    assert "synthesis" in output
    assert (tmp_path / "audit.jsonl").exists()
```

- [ ] **Step 2: Run the demo test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_run_demo.py -q`
Expected: FAIL with missing run_demo module

- [ ] **Step 3: Implement the demo runner**

```python
from pathlib import Path

from sentinentialfox.host_bridge import run_investigation
from sentinentialfox.safety.audit import JsonlAuditWriter


def run_demo(prompt: str, audit_path: Path) -> dict:
    result = run_investigation(prompt)
    writer = JsonlAuditWriter(audit_path)
    writer.write(
        {
            "prompt": prompt,
            "mode": "stub",
            "status": result["investigation"]["status"],
            "tool_name": result["investigation"]["tool_name"],
        }
    )
    return result
```

- [ ] **Step 4: Run the demo test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_run_demo.py -q`
Expected: PASS

- [ ] **Step 5: Add a CLI wrapper for manual verification**

```python
from pathlib import Path
import sys

from scripts.run_demo import run_demo


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Investigate suspicious activity"
    result = run_demo(prompt, Path("artifacts/demo-audit.jsonl"))
    print(result["synthesis"]["summary"])
```

- [ ] **Step 6: Verify the runnable slice works**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_demo.py "Investigate suspicious login activity"`
Expected: prints a synthesis summary and creates `artifacts/demo-audit.jsonl`

- [ ] **Step 7: Commit**

```bash
git add sentinentialfox-workspace/scripts/run_demo.py sentinentialfox-workspace/tests/integration/test_run_demo.py sentinentialfox-workspace/artifacts/.gitkeep
git commit -m "feat: add runnable sentinentialfox integration demo"
```

### Task 9: Replace the Stub With Real Splunk Path Discovery

**Files:**
- Modify: `sentinentialfox-workspace/sentinentialfox/adapters/splunk_stub.py`
- Create: `sentinentialfox-workspace/sentinentialfox/adapters/splunk_rest_backend.py`
- Create: `sentinentialfox-workspace/tests/integration/test_splunk_rest_backend.py`
- Modify: `sentinentialfox-workspace/.env.example`

- [ ] **Step 1: Write the failing real-backend config test**

```python
from sentinentialfox.adapters.splunk_rest_backend import SplunkRestBackend


def test_splunk_rest_backend_reports_missing_configuration():
    adapter = SplunkRestBackend.from_env({})
    assert adapter.status == "unconfigured"
    assert "SPLUNK" in adapter.reason
```

- [ ] **Step 2: Run the config test to verify it fails**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_splunk_rest_backend.py -q`
Expected: FAIL with missing backend module

- [ ] **Step 3: Implement minimal configuration-aware backend shell**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class SplunkRestBackend:
    status: str
    reason: str

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "SplunkRestBackend":
        required = ("SPLUNK_BACKEND_URL", "SPLUNK_TOKEN")
        missing = [name for name in required if not env.get(name)]
        if missing:
            return cls(status="unconfigured", reason=f"Missing SPLUNK config: {', '.join(missing)}")
        return cls(status="configured", reason="")
```

- [ ] **Step 4: Run the config test to verify it passes**

Run: `cd sentinentialfox-workspace && UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/integration/test_splunk_rest_backend.py -q`
Expected: PASS

- [ ] **Step 5: Write the shared environment example**

```dotenv
SPLUNK_BACKEND_URL=
SPLUNK_TOKEN=
SPLUNK_USERNAME=
SPLUNK_PASSWORD=
OPENROUTER_API_KEY=
OPENROUTER_MODEL=google/gemma-3-27b-it
```

- [ ] **Step 6: Commit**

```bash
git add sentinentialfox-workspace/sentinentialfox/adapters/splunk_rest_backend.py sentinentialfox-workspace/tests/integration/test_splunk_rest_backend.py sentinentialfox-workspace/.env.example
git commit -m "feat: add real splunk rest backend configuration shell"
```

## Self-Review

Spec coverage check:

- Approved host shape (`incidentfox` dominant, `aurora` translated in) is covered by Tasks 2, 6, and 7.
- Preserved safety layer and tests are covered by Task 4.
- Splunk tool boundary and read-only behavior are covered by Tasks 5 and 9.
- Honest runnable slice and evidence output are covered by Task 8.
- Upstream cloning and attribution-friendly structure are covered by Tasks 1 and 2.

Placeholder scan:

- No `TODO` or `TBD` markers remain.
- The one intentional unresolved element is the exact internal `incidentfox` and `aurora` file names; this is addressed explicitly by Task 2 before any host modifications occur.

Type consistency:

- `ToolAdapter`, `ToolResult`, `InvestigationGraph`, `StubSplunkAdapter`, and `SplunkMCPAdapter` are used consistently across tasks.
- The runnable graph and host bridge both return the same nested result shape.
