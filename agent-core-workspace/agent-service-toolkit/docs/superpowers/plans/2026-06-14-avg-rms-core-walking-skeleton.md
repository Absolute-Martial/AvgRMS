# AvgRMS Core Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 1 shared-core walking skeleton as a new `avg-rms-core` agent that runs through the existing service and client path, uses a deterministic scripted planner by default, retries one allow-listed FakeAdapter runtime failure, and records unambiguous audit events with `action_id`, `event_type`, and `correction_of`.

**Architecture:** Add a new isolated LangGraph `StateGraph` agent plus a focused `src/avg_rms_core/` package for contracts, planner/critic interfaces, guardrails, audit logging, state helpers, and the deterministic `FakeAdapter`. Drive development test-first, keep the scripted path byte-reproducible, and leave the LLM planner as an optional config-selected implementation that reuses the toolkit model stack without affecting asserted tests.

**Tech Stack:** Python, LangGraph, FastAPI, Pydantic, pytest, httpx test client, JSONL logging, git

---

## File Structure

Implementation files:

- Create: `src/avg_rms_core/__init__.py`
- Create: `src/avg_rms_core/contracts.py`
- Create: `src/avg_rms_core/state.py`
- Create: `src/avg_rms_core/planners.py`
- Create: `src/avg_rms_core/critics.py`
- Create: `src/avg_rms_core/guardrails.py`
- Create: `src/avg_rms_core/audit.py`
- Create: `src/avg_rms_core/fake_adapter.py`
- Create: `src/agents/avg_rms_core_agent.py`
- Modify: `src/agents/agents.py`

Test files:

- Create: `tests/avg_rms_core/test_planners.py`
- Create: `tests/avg_rms_core/test_guardrails.py`
- Create: `tests/avg_rms_core/test_fake_adapter.py`
- Create: `tests/service/test_avg_rms_core_agent.py`
- Modify if needed: `tests/agents/test_agent_loading.py`

Repo bootstrap files:

- Create: `.gitignore` at `/home/lets-smile/PycharmProjects/AvgRMS/.gitignore`

Plan assumptions:

- Only `agent-core-workspace/agent-service-toolkit` is implementation scope.
- Ignore the planning markdown root, `protocol-sift`, `references`, and root helper scripts in the top-level git bootstrap.
- Do not change `src/service/service.py` or `src/client/client.py` unless an integration gap is proven by tests.

### Task 0: Git Bootstrap And Workspace Hygiene

**Files:**
- Create: `/home/lets-smile/PycharmProjects/AvgRMS/.gitignore`
- Verify: `/home/lets-smile/PycharmProjects/AvgRMS/.git`

- [ ] **Step 1: Create the top-level ignore file that scopes the public repo to the toolkit work**

```gitignore
.idea/
.codex/
.agents/

AvgRMSBest — Phases & Tasks (build roadmap)/
AvgRMSBest — Phases & Tasks (build roadmap).md
cloner

agent-core-workspace/protocol-sift/
agent-core-workspace/references/

*.log
```

- [ ] **Step 2: Verify whether the current `.git` directory is usable**

Run: `git status`
Expected: either a normal status output or `fatal: not a git repository`

- [ ] **Step 3: If git is broken, reinitialize the top-level checkout and set the remote**

```bash
mv .git .git.broken-2026-06-14
git init
git branch -M main
git remote add origin https://github.com/Absolute-Martial/AvgRMS
git status
git remote -v
```

Expected:
- `git status` shows a valid repository
- `git remote -v` lists `https://github.com/Absolute-Martial/AvgRMS`

- [ ] **Step 4: Stage only the scoped implementation surface and ignore set**

```bash
git add .gitignore agent-core-workspace/agent-service-toolkit
git status --short
```

Expected: tracked paths are limited to `.gitignore` and `agent-core-workspace/agent-service-toolkit/...`

- [ ] **Step 5: Commit the repo bootstrap**

```bash
git commit -m "chore: initialize scoped AvgRMS repository"
```

### Task 1: Lock Down Shared Contracts With Failing Tests

**Files:**
- Create: `tests/avg_rms_core/test_planners.py`
- Create: `tests/avg_rms_core/test_guardrails.py`
- Create: `tests/avg_rms_core/test_fake_adapter.py`
- Create: `src/avg_rms_core/contracts.py`
- Create: `src/avg_rms_core/__init__.py`

- [ ] **Step 1: Write the failing planner contract test for deterministic action ids**

```python
from avg_rms_core.planners import ScriptedPlanner
from avg_rms_core.state import AvgRMSState


def test_scripted_planner_returns_deterministic_action_ids():
    planner = ScriptedPlanner()
    state = AvgRMSState(request_text="investigate fake incident", max_attempts=2)

    first = planner.plan_next(state)
    state.action_history.append(first)
    second = planner.replan_after_result(state)

    assert first.id == "action-001"
    assert second.id == "action-002"
```

- [ ] **Step 2: Write the failing guardrail contract test for blocked tools**

```python
from avg_rms_core.contracts import PlannedAction
from avg_rms_core.guardrails import GuardrailGate


def test_guardrail_blocks_non_allow_listed_tool():
    gate = GuardrailGate(allow_list={"fake.lookup"})
    action = PlannedAction(id="action-001", tool="rm", args={}, reason="bad")

    decision = gate.check(action)

    assert decision.decision == "blocked"
    assert decision.reason == "tool_not_allow_listed"
```

- [ ] **Step 3: Write the failing fake adapter contract test for fixed stdout and hashes**

```python
from avg_rms_core.fake_adapter import FakeAdapter


def test_fake_adapter_success_is_byte_reproducible():
    adapter = FakeAdapter(mode="success")

    first = adapter.run_tool("fake.lookup", {"target": "alpha"})
    second = adapter.run_tool("fake.lookup", {"target": "alpha"})

    assert first.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert second.stdout == "FAKE_LOOKUP_OK target=alpha\n"
    assert first.output_hash == second.output_hash
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest tests/avg_rms_core/test_planners.py tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py -v`
Expected: FAIL with import errors because `avg_rms_core` modules do not exist yet

- [ ] **Step 5: Create the contract module and package exports**

```python
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Artifact:
    kind: str
    ref: str
    detail: str = ""


@dataclass
class ToolResult:
    tool: str
    args: dict[str, Any]
    stdout: str
    artifacts: list[Artifact] = field(default_factory=list)
    output_hash: str = ""
    confidence: str = "confirmed"
    status: str = "ok"
    error: str = ""


@dataclass
class PlannedAction:
    id: str
    tool: str
    args: dict[str, Any]
    reason: str


@dataclass
class GuardrailDecision:
    action_id: str
    tool: str
    decision: str
    reason: str


@dataclass
class CriticDecision:
    outcome: str
    summary: str


@dataclass
class FinalDecision:
    status: str
    summary: str


@dataclass
class AuditEvent:
    ts: str
    run_id: str
    thread_id: str
    planner: str
    event_type: str
    action_id: str
    tool: str
    args: dict[str, Any]
    decision: str
    output_hash: str
    status: str
    correction_of: str | None
    latency_ms: int


class ToolAdapter(Protocol):
    name: str

    def list_tools(self) -> list[dict[str, Any]]: ...

    def run_tool(self, tool: str, args: dict[str, Any]) -> ToolResult: ...
```

- [ ] **Step 6: Export the contract symbols from the package**

```python
from avg_rms_core.contracts import (
    Artifact,
    AuditEvent,
    CriticDecision,
    FinalDecision,
    GuardrailDecision,
    PlannedAction,
    ToolAdapter,
    ToolResult,
)

__all__ = [
    "Artifact",
    "AuditEvent",
    "CriticDecision",
    "FinalDecision",
    "GuardrailDecision",
    "PlannedAction",
    "ToolAdapter",
    "ToolResult",
]
```

- [ ] **Step 7: Run the contract tests again**

Run: `pytest tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py -v`
Expected: FAIL with missing `GuardrailGate` and `FakeAdapter`, proving the tests are now reaching the next missing units

- [ ] **Step 8: Commit the contract baseline**

```bash
git add src/avg_rms_core/__init__.py src/avg_rms_core/contracts.py tests/avg_rms_core/test_planners.py tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py
git commit -m "test: define avg rms core contracts"
```

### Task 2: Implement State, Scripted Planner, And Critic

**Files:**
- Create: `src/avg_rms_core/state.py`
- Create: `src/avg_rms_core/planners.py`
- Create: `src/avg_rms_core/critics.py`
- Modify: `tests/avg_rms_core/test_planners.py`

- [ ] **Step 1: Extend the planner tests to cover correction and attempts exhausted**

```python
from avg_rms_core.contracts import CriticDecision, PlannedAction, ToolResult
from avg_rms_core.planners import ScriptedPlanner
from avg_rms_core.state import AvgRMSState


def test_scripted_planner_retry_after_runtime_error():
    planner = ScriptedPlanner()
    state = AvgRMSState(request_text="investigate fake incident", max_attempts=2)

    first = planner.plan_next(state)
    state.action_history.append(first)
    state.last_result = ToolResult(
        tool="fake.lookup",
        args={"target": "alpha"},
        stdout="FAKE_LOOKUP_ERROR target=alpha\n",
        output_hash="hash-1",
        status="error",
        error="simulated runtime error",
    )

    second = planner.replan_after_result(state)

    assert second.id == "action-002"
    assert second.tool == "fake.lookup"
    assert second.args == {"target": "alpha", "retry": 1}
```

- [ ] **Step 2: Add the attempts-exhausted critic test with deterministic vocabulary**

```python
from avg_rms_core.critics import DeterministicCritic
from avg_rms_core.contracts import ToolResult
from avg_rms_core.state import AvgRMSState


def test_deterministic_critic_marks_attempts_exhausted():
    critic = DeterministicCritic()
    state = AvgRMSState(request_text="investigate", max_attempts=1, attempt_count=1)
    result = ToolResult(
        tool="fake.lookup",
        args={"target": "alpha"},
        stdout="FAKE_LOOKUP_ERROR target=alpha\n",
        output_hash="hash-1",
        status="error",
        error="simulated runtime error",
    )

    decision = critic.assess(state, result)

    assert decision.outcome == "attempts_exhausted"
```

- [ ] **Step 3: Run planner tests to confirm they fail**

Run: `pytest tests/avg_rms_core/test_planners.py -v`
Expected: FAIL with missing `AvgRMSState`, `ScriptedPlanner`, or `DeterministicCritic`

- [ ] **Step 4: Implement the state container**

```python
from dataclasses import dataclass, field
from typing import Any

from avg_rms_core.contracts import PlannedAction, ToolResult


@dataclass
class AvgRMSState:
    request_text: str
    planner_mode: str = "scripted"
    adapter_mode: str = "fake"
    available_tools: list[str] = field(default_factory=list)
    attempt_count: int = 0
    max_attempts: int = 2
    current_action: PlannedAction | None = None
    action_history: list[PlannedAction] = field(default_factory=list)
    result_history: list[ToolResult] = field(default_factory=list)
    last_result: ToolResult | None = None
    last_block_reason: str | None = None
    final_response: str = ""
    audit_log_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 5: Implement the swappable planner interface and deterministic scripted planner**

```python
from dataclasses import dataclass
from typing import Protocol

from avg_rms_core.contracts import FinalDecision, PlannedAction
from avg_rms_core.state import AvgRMSState


class Planner(Protocol):
    def plan_next(self, state: AvgRMSState) -> PlannedAction | FinalDecision: ...

    def replan_after_result(self, state: AvgRMSState) -> PlannedAction | FinalDecision: ...


@dataclass
class ScriptedPlanner:
    def plan_next(self, state: AvgRMSState) -> PlannedAction | FinalDecision:
        return PlannedAction(
            id="action-001",
            tool="fake.lookup",
            args={"target": "alpha"},
            reason="initial lookup",
        )

    def replan_after_result(self, state: AvgRMSState) -> PlannedAction | FinalDecision:
        if state.attempt_count >= state.max_attempts:
            return FinalDecision(
                status="attempts_exhausted",
                summary="Retries exhausted after adapter runtime failures.",
            )
        return PlannedAction(
            id="action-002",
            tool="fake.lookup",
            args={"target": "alpha", "retry": 1},
            reason="retry after adapter runtime failure",
        )
```

- [ ] **Step 6: Implement the critic with aligned status vocabulary**

```python
from avg_rms_core.contracts import CriticDecision, ToolResult
from avg_rms_core.state import AvgRMSState


class DeterministicCritic:
    def assess(self, state: AvgRMSState, result: ToolResult) -> CriticDecision:
        if result.status == "ok":
            return CriticDecision(outcome="success", summary="Action succeeded.")
        if result.status == "blocked":
            return CriticDecision(outcome="blocked", summary="Action was blocked.")
        if state.attempt_count >= state.max_attempts:
            return CriticDecision(
                outcome="attempts_exhausted",
                summary="Retries exhausted after adapter runtime failures.",
            )
        return CriticDecision(outcome="retry", summary="Retryable adapter runtime failure.")
```

- [ ] **Step 7: Stub the optional `LLMPlanner` behind the same interface**

```python
from core import get_model, settings


class LLMPlanner:
    async def plan_with_model(self, prompt: str, model_name: str | None = None) -> str:
        model = get_model(model_name or settings.DEFAULT_MODEL)
        response = await model.ainvoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
```

- [ ] **Step 8: Run the planner tests and make them pass**

Run: `pytest tests/avg_rms_core/test_planners.py -v`
Expected: PASS

- [ ] **Step 9: Commit the planner and critic layer**

```bash
git add src/avg_rms_core/state.py src/avg_rms_core/planners.py src/avg_rms_core/critics.py tests/avg_rms_core/test_planners.py
git commit -m "feat: add deterministic planner and critic"
```

### Task 3: Implement Guardrails, Audit Logging, And FakeAdapter Modes

**Files:**
- Create: `src/avg_rms_core/guardrails.py`
- Create: `src/avg_rms_core/audit.py`
- Create: `src/avg_rms_core/fake_adapter.py`
- Modify: `tests/avg_rms_core/test_guardrails.py`
- Modify: `tests/avg_rms_core/test_fake_adapter.py`

- [ ] **Step 1: Extend the fake adapter tests to cover fail-once and always-fail modes**

```python
from avg_rms_core.fake_adapter import FakeAdapter


def test_fake_adapter_fails_once_then_succeeds():
    adapter = FakeAdapter(mode="fail_once")

    first = adapter.run_tool("fake.lookup", {"target": "alpha"})
    second = adapter.run_tool("fake.lookup", {"target": "alpha", "retry": 1})

    assert first.status == "error"
    assert first.error == "simulated runtime error"
    assert second.status == "ok"


def test_fake_adapter_always_fail_mode_is_deterministic():
    adapter = FakeAdapter(mode="always_fail")

    result = adapter.run_tool("fake.lookup", {"target": "alpha"})

    assert result.status == "error"
    assert result.stdout == "FAKE_LOOKUP_ERROR target=alpha\n"
```

- [ ] **Step 2: Add the audit structural-field assertion test**

```python
import json

from avg_rms_core.audit import JsonlAuditLogger
from avg_rms_core.contracts import AuditEvent


def test_audit_logger_writes_required_structural_fields(tmp_path):
    logger = JsonlAuditLogger(tmp_path / "audit.jsonl")
    event = AuditEvent(
        ts="2026-06-14T00:00:00Z",
        run_id="run-1",
        thread_id="thread-1",
        planner="scripted",
        event_type="action_result",
        action_id="action-001",
        tool="fake.lookup",
        args={"target": "alpha"},
        decision="allowed",
        output_hash="hash-1",
        status="error",
        correction_of=None,
        latency_ms=5,
    )

    logger.write(event)
    row = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])

    assert row["event_type"] == "action_result"
    assert row["action_id"] == "action-001"
    assert row["tool"] == "fake.lookup"
    assert row["decision"] == "allowed"
    assert row["status"] == "error"
```

- [ ] **Step 3: Run the guardrail and adapter tests to confirm they fail**

Run: `pytest tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py -v`
Expected: FAIL with missing `GuardrailGate`, `JsonlAuditLogger`, or `FakeAdapter`

- [ ] **Step 4: Implement the guardrail gate with explicit allow auditing semantics**

```python
from avg_rms_core.contracts import GuardrailDecision, PlannedAction


class GuardrailGate:
    def __init__(self, allow_list: set[str]) -> None:
        self.allow_list = allow_list

    def check(self, action: PlannedAction) -> GuardrailDecision:
        if action.tool not in self.allow_list:
            return GuardrailDecision(
                action_id=action.id,
                tool=action.tool,
                decision="blocked",
                reason="tool_not_allow_listed",
            )
        return GuardrailDecision(
            action_id=action.id,
            tool=action.tool,
            decision="allowed",
            reason="tool_allow_listed",
        )
```

- [ ] **Step 5: Implement append-only JSONL audit logging**

```python
import json
from dataclasses import asdict
from pathlib import Path

from avg_rms_core.contracts import AuditEvent


class JsonlAuditLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: AuditEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
```

- [ ] **Step 6: Implement the deterministic fake adapter modes**

```python
import hashlib

from avg_rms_core.contracts import ToolResult


class FakeAdapter:
    name = "fake"

    def __init__(self, mode: str = "fail_once") -> None:
        self.mode = mode
        self.calls = 0

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": "fake.lookup"}]

    def run_tool(self, tool: str, args: dict) -> ToolResult:
        self.calls += 1
        target = args["target"]
        if self.mode == "always_fail" or (self.mode == "fail_once" and self.calls == 1):
            stdout = f"FAKE_LOOKUP_ERROR target={target}\n"
            return ToolResult(
                tool=tool,
                args=args,
                stdout=stdout,
                output_hash=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
                status="error",
                error="simulated runtime error",
            )
        stdout = f"FAKE_LOOKUP_OK target={target}\n"
        return ToolResult(
            tool=tool,
            args=args,
            stdout=stdout,
            output_hash=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            status="ok",
        )
```

- [ ] **Step 7: Run the unit tests and make them pass**

Run: `pytest tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py -v`
Expected: PASS

- [ ] **Step 8: Commit the infrastructure layer**

```bash
git add src/avg_rms_core/guardrails.py src/avg_rms_core/audit.py src/avg_rms_core/fake_adapter.py tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py
git commit -m "feat: add guardrails audit and fake adapter"
```

### Task 4: Build The LangGraph Agent And Register It

**Files:**
- Create: `src/agents/avg_rms_core_agent.py`
- Modify: `src/agents/agents.py`
- Modify: `tests/agents/test_agent_loading.py`

- [ ] **Step 1: Add the failing agent loading test**

```python
from agents.agents import get_agent


def test_get_agent_avg_rms_core():
    agent = get_agent("avg-rms-core")
    assert agent is not None
```

- [ ] **Step 2: Run the agent loading test and verify it fails**

Run: `pytest tests/agents/test_agent_loading.py::test_get_agent_avg_rms_core -v`
Expected: FAIL with `KeyError: 'avg-rms-core'`

- [ ] **Step 3: Implement the LangGraph walking skeleton agent**

```python
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from avg_rms_core.audit import JsonlAuditLogger
from avg_rms_core.contracts import AuditEvent
from avg_rms_core.critics import DeterministicCritic
from avg_rms_core.fake_adapter import FakeAdapter
from avg_rms_core.guardrails import GuardrailGate
from avg_rms_core.planners import ScriptedPlanner
from avg_rms_core.state import AvgRMSState


def _initial_state(inputs: dict[str, list[BaseMessage]], config: RunnableConfig) -> AvgRMSState:
    message = inputs["messages"][-1].content
    configurable = config["configurable"]
    return AvgRMSState(
        request_text=message,
        planner_mode=configurable.get("planner_mode", "scripted"),
        adapter_mode=configurable.get("adapter_mode", "fake"),
        max_attempts=int(configurable.get("max_attempts", 2)),
        audit_log_path=str(Path(configurable.get("audit_log_dir", "data")) / "avg_rms_core.audit.jsonl"),
    )


def _ts() -> str:
    return datetime.now(UTC).isoformat()


builder = StateGraph(AvgRMSState)
avg_rms_core_agent = builder.compile()
```

- [ ] **Step 4: Flesh out the graph nodes before compiling**

```python
def plan(state: AvgRMSState) -> dict:
    planner = ScriptedPlanner()
    action = planner.plan_next(state) if not state.action_history else planner.replan_after_result(state)
    state.current_action = action
    state.action_history.append(action)
    return {"current_action": action, "action_history": state.action_history}


def guardrail_check(state: AvgRMSState, config: RunnableConfig) -> dict:
    logger = JsonlAuditLogger(Path(state.audit_log_path))
    decision = GuardrailGate({"fake.lookup"}).check(state.current_action)
    logger.write(
        AuditEvent(
            ts=_ts(),
            run_id=str(config["run_id"]),
            thread_id=config["configurable"]["thread_id"],
            planner=state.planner_mode,
            event_type="guardrail_decision",
            action_id=state.current_action.id,
            tool=state.current_action.tool,
            args=state.current_action.args,
            decision=decision.decision,
            output_hash="",
            status=decision.decision,
            correction_of=state.action_history[-2].id if len(state.action_history) > 1 else None,
            latency_ms=0,
        )
    )
    state.last_block_reason = None if decision.decision == "allowed" else decision.reason
    return {"last_block_reason": state.last_block_reason}
```

- [ ] **Step 5: Add act, observe, critic, and terminal nodes**

```python
def act(state: AvgRMSState, config: RunnableConfig) -> dict:
    adapter = FakeAdapter(mode=config["configurable"].get("fake_adapter_mode", "fail_once"))
    result = adapter.run_tool(state.current_action.tool, state.current_action.args)
    state.last_result = result
    state.result_history.append(result)
    state.attempt_count += 1
    return {"last_result": result, "result_history": state.result_history, "attempt_count": state.attempt_count}


def finalize_success(state: AvgRMSState) -> dict:
    state.final_response = "Recovered after one adapter runtime failure and completed the lookup."
    return {"messages": [AIMessage(content=state.final_response)]}


def finalize_blocked(state: AvgRMSState) -> dict:
    state.final_response = f"Blocked by guardrail: {state.last_block_reason}"
    return {"messages": [AIMessage(content=state.final_response)]}


def finalize_attempts_exhausted(state: AvgRMSState) -> dict:
    state.final_response = "Retries exhausted after adapter runtime failures."
    return {"messages": [AIMessage(content=state.final_response)]}
```

- [ ] **Step 6: Register the agent in the registry**

```python
from agents.avg_rms_core_agent import avg_rms_core_agent

agents["avg-rms-core"] = Agent(
    description="AvgRMS shared-core walking skeleton using the fake adapter.",
    graph_like=avg_rms_core_agent,
)
```

- [ ] **Step 7: Run the loading tests and make them pass**

Run: `pytest tests/agents/test_agent_loading.py -v`
Expected: PASS

- [ ] **Step 8: Commit the new agent registration**

```bash
git add src/agents/avg_rms_core_agent.py src/agents/agents.py tests/agents/test_agent_loading.py
git commit -m "feat: add avg rms core graph agent"
```

### Task 5: Add Service-Level End-To-End Tests For Success, Blocked, And Attempts Exhausted

**Files:**
- Create: `tests/service/test_avg_rms_core_agent.py`

- [ ] **Step 1: Write the end-to-end scripted correction test through FastAPI**

```python
import json


def test_avg_rms_core_retries_after_adapter_runtime_failure(test_client, tmp_path):
    response = test_client.post(
        "/avg-rms-core/invoke",
        json={
            "message": "investigate fake incident",
            "agent_config": {
                "planner_mode": "scripted",
                "adapter_mode": "fake",
                "fake_adapter_mode": "fail_once",
                "audit_log_dir": str(tmp_path),
            },
        },
    )

    assert response.status_code == 200
    assert "Recovered after one adapter runtime failure" in response.json()["content"]

    rows = [json.loads(line) for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert action_rows[0]["action_id"] == "action-001"
    assert action_rows[1]["action_id"] == "action-002"
    assert action_rows[1]["correction_of"] == "action-001"
```

- [ ] **Step 2: Write the blocked-tool audit test**

```python
import json


def test_avg_rms_core_blocks_non_allow_listed_tool(test_client, tmp_path):
    response = test_client.post(
        "/avg-rms-core/invoke",
        json={
            "message": "investigate fake incident",
            "agent_config": {
                "planner_mode": "scripted",
                "scripted_tool_name": "rm",
                "audit_log_dir": str(tmp_path),
            },
        },
    )

    assert response.status_code == 200
    assert "Blocked by guardrail" in response.json()["content"]

    rows = [json.loads(line) for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()]
    blocked = [row for row in rows if row["event_type"] == "guardrail_decision"]

    assert blocked[-1]["decision"] == "blocked"
    assert blocked[-1]["action_id"] == "action-001"
```

- [ ] **Step 3: Write the deterministic attempts-exhausted test**

```python
import json


def test_avg_rms_core_attempts_exhausted_with_max_attempts_one(test_client, tmp_path):
    response = test_client.post(
        "/avg-rms-core/invoke",
        json={
            "message": "investigate fake incident",
            "agent_config": {
                "planner_mode": "scripted",
                "fake_adapter_mode": "always_fail",
                "max_attempts": 1,
                "audit_log_dir": str(tmp_path),
            },
        },
    )

    assert response.status_code == 200
    assert "Retries exhausted" in response.json()["content"]

    rows = [json.loads(line) for line in (tmp_path / "avg_rms_core.audit.jsonl").read_text().splitlines()]
    action_rows = [row for row in rows if row["event_type"] == "action_result"]

    assert len(action_rows) == 1
    assert action_rows[0]["action_id"] == "action-001"
    assert action_rows[0]["status"] == "error"
```

- [ ] **Step 4: Add the structural reproducibility assertion helper**

```python
def assert_structural_event_fields(row: dict, expected: dict) -> None:
    comparable = {
        key: value
        for key, value in row.items()
        if key not in {"ts", "latency_ms"}
    }
    assert comparable == expected
```

- [ ] **Step 5: Run the new service tests and verify they fail before final implementation wiring**

Run: `pytest tests/service/test_avg_rms_core_agent.py -v`
Expected: FAIL until the graph writes `action_result` events and supports blocked or always-fail config paths

- [ ] **Step 6: Finish the graph wiring to satisfy the service tests**

```python
logger.write(
    AuditEvent(
        ts=_ts(),
        run_id=str(config["run_id"]),
        thread_id=config["configurable"]["thread_id"],
        planner=state.planner_mode,
        event_type="action_result",
        action_id=state.current_action.id,
        tool=state.current_action.tool,
        args=state.current_action.args,
        decision="allowed",
        output_hash=result.output_hash,
        status=result.status,
        correction_of=state.action_history[-2].id if len(state.action_history) > 1 else None,
        latency_ms=0,
    )
)
```

- [ ] **Step 7: Run the focused service and unit suite**

Run: `pytest tests/avg_rms_core/test_planners.py tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py tests/service/test_avg_rms_core_agent.py tests/agents/test_agent_loading.py -v`
Expected: PASS

- [ ] **Step 8: Commit the tested walking skeleton**

```bash
git add tests/service/test_avg_rms_core_agent.py src/agents/avg_rms_core_agent.py src/avg_rms_core
git commit -m "feat: implement avg rms core walking skeleton"
```

### Task 6: Manual LLM Smoke Run And Final Verification

**Files:**
- Verify only: `src/avg_rms_core/planners.py`
- Verify only: `src/agents/avg_rms_core_agent.py`

- [ ] **Step 1: Run the full focused automated suite**

Run: `pytest tests/avg_rms_core/test_planners.py tests/avg_rms_core/test_guardrails.py tests/avg_rms_core/test_fake_adapter.py tests/service/test_avg_rms_core_agent.py tests/agents/test_agent_loading.py -v`
Expected: PASS

- [ ] **Step 2: Start the service locally**

Run: `python src/run_service.py`
Expected: FastAPI service starts without agent loading errors

- [ ] **Step 3: In a second shell, smoke-test the optional LLM planner path**

```bash
python - <<'PY'
from client import AgentClient

client = AgentClient(base_url="http://0.0.0.0:8080", agent="avg-rms-core", get_info=False)
response = client.invoke(
    "investigate fake incident",
    agent_config={
        "planner_mode": "llm",
        "adapter_mode": "fake",
        "fake_adapter_mode": "fail_once",
    },
)
print(response.content)
PY
```

Expected: the loop completes once end-to-end without crashing; exact text is not asserted

- [ ] **Step 4: Verify git status is clean enough for public submission history**

Run: `git status --short`
Expected: either clean or only intentional tracked changes

- [ ] **Step 5: Commit the verification pass**

```bash
git add docs/superpowers/specs/2026-06-14-avg-rms-core-walking-skeleton-design.md docs/superpowers/plans/2026-06-14-avg-rms-core-walking-skeleton.md
git commit -m "docs: add avg rms core spec and implementation plan"
```

## Self-Review

Spec coverage:

- `action_id` and `event_type` added to the audit contract and explicitly asserted in tests
- deterministic `attempts_exhausted` path covered via `always_fail` plus `max_attempts=1`
- reproducibility assertions explicitly exclude `ts` and `latency_ms`
- critic and final-decision vocabulary aligned on `success`, `blocked`, `failure`, and `attempts_exhausted`
- allow decisions are explicitly audited before action execution
- separate blocked and adapter-runtime-error routes remain distinct

Placeholder scan:

- No `TODO`, `TBD`, or undefined “handle appropriately” steps remain
- Every task contains concrete files, commands, and code snippets

Type consistency:

- `AuditEvent` uses `action_id`, `event_type`, and `correction_of` consistently
- `CriticDecision.outcome` and `FinalDecision.status` share the same status vocabulary
- `FakeAdapter` modes are named `success`, `fail_once`, and `always_fail` consistently across tasks
