# AvgRMS Core Walking Skeleton Design

Date: 2026-06-14
Scope: Phase 0 executable recon plus Phase 1 shared-core walking skeleton only
Status: Draft for user review

## Goal

Add a new isolated `avg-rms-core` agent to `agent-service-toolkit` that exercises the shared-core loop through the existing FastAPI service and client surfaces. The walking skeleton must run against a deterministic `FakeAdapter`, demonstrate one adapter runtime failure followed by a critic-driven retry, and write an append-only JSONL audit log that records the correction via `correction_of`.

This slice is the foundation for later adapters:

- Slice 2: SIFT adapter
- Slice 3: Splunk adapter

## Scope

Included in this slice:

- executable recon of the actual `agent-service-toolkit` extension points
- new `avg-rms-core` agent under `src/agents/`
- shared-core modules under a new `src/avg_rms_core/` package
- `ToolAdapter` and `ToolResult` contract
- swappable planner and critic interfaces
- deterministic `ScriptedPlanner` as the default path
- optional `LLMPlanner` behind config using the toolkit model stack
- deny-by-default guardrail gate
- deterministic `FakeAdapter`
- append-only JSONL audit logger
- integration through existing `src/service/service.py` and `src/client/client.py`
- automated tests for the scripted path

Explicitly deferred:

- real SIFT and Splunk adapters
- PDF report generation
- model router beyond planner selection
- Streamlit changes
- submission packaging

## Executable Recon Outcome

The design is based on the current toolkit layout, not an invented tree.

Observed integration seams:

- agent registry: `src/agents/agents.py`
- existing graph agent patterns: `src/agents/*.py`
- service invoke and stream entrypoints: `src/service/service.py`
- client invoke and stream calls: `src/client/client.py`
- service bootstrap: `src/run_service.py`

This slice extends those seams without changing the service contract.

## Recommended File Layout

New files:

- `src/avg_rms_core/__init__.py`
- `src/avg_rms_core/contracts.py`
- `src/avg_rms_core/state.py`
- `src/avg_rms_core/planners.py`
- `src/avg_rms_core/critics.py`
- `src/avg_rms_core/guardrails.py`
- `src/avg_rms_core/audit.py`
- `src/avg_rms_core/fake_adapter.py`
- `src/agents/avg_rms_core_agent.py`
- `tests/avg_rms_core/test_planners.py`
- `tests/avg_rms_core/test_guardrails.py`
- `tests/avg_rms_core/test_fake_adapter.py`
- `tests/service/test_avg_rms_core_agent.py`

Modified files:

- `src/agents/agents.py`

No changes are required in `src/service/service.py` or `src/client/client.py` beyond exercising their existing path.

## Architecture

The new agent is implemented as an explicit `StateGraph` so planning, guardrail decisions, execution, observation, retry, and termination remain visible and testable.

Graph shape:

1. `plan`
2. `guardrail_check`
3. `act`
4. `observe`
5. `critic`
6. route to one of:
   - `plan` for retry
   - `finalize_success`
   - `finalize_blocked`
   - `finalize_failure`
   - `finalize_attempts_exhausted`

The graph must always terminate. `finalize_attempts_exhausted` is an explicit terminal node to guarantee bounded completion, especially for the optional LLM path.

## Responsibilities By Component

### `avg-rms-core` agent

- accepts user input from the existing service path
- selects planner mode from `agent_config`
- runs the loop against a chosen adapter
- emits a final assistant message summarizing success, block, or failure

### Planner interface

The planner is swappable and independent of the graph wiring.

Required interface:

- `plan_next(state) -> PlannedAction | FinalDecision`
- `replan_after_result(state) -> PlannedAction | FinalDecision`

Implementations:

- `ScriptedPlanner`
  - default for tests, CI, and reproducible service runs
  - deterministic action ids
  - deterministic correction sequence
- `LLMPlanner`
  - selected by config flag
  - uses the toolkit's existing model stack
  - manually smoke-tested only, not asserted in tests

### Critic interface

The critic is also swappable.

Required interface:

- `assess(state, result) -> CriticDecision`

The scripted path uses a deterministic critic that classifies:

- adapter runtime error as retryable
- guardrail block as blocked
- successful result as terminal success
- repeated retryable failures past the attempt cap as attempts exhausted

### Guardrail gate

The gate is architectural-first and deny-by-default.

Initial behavior:

- deny any tool that is not explicitly allow-listed
- perform deterministic argument validation
- do not treat the scripted forced failure as a guardrail event
- audit every decision, including blocked actions

Blocked actions stay distinct from adapter runtime failures:

- guardrail-blocked path: `guardrail_check -> finalize_blocked` or `guardrail_check -> plan` only if a future planner explicitly rewrites the action
- adapter runtime error path: `act -> observe -> critic -> plan`

For Slice 1, the scripted planner does not rewrite blocked actions. A blocked action finalizes immediately with an audited blocked decision.

### Tool adapter boundary

The adapter contract remains domain-agnostic so later SIFT and Splunk adapters can drop in without changing graph semantics.

Required interface:

```python
class ToolAdapter(Protocol):
    name: str

    def list_tools(self) -> list[dict]: ...

    def run_tool(self, tool: str, args: dict) -> ToolResult: ...
```

### FakeAdapter

The walking skeleton runs only against `FakeAdapter`.

Required behavior:

- exposes an allow-listed tool set
- returns byte-reproducible stdout
- uses deterministic action outcomes for the scripted path
- includes one forced adapter runtime error on the first scripted action
- returns success on the scripted retry path

The forced failure must be an allow-listed adapter runtime error, not a guardrail block.

### Audit logger

The logger writes append-only JSONL, one event per decision or action result.

The log is created during the run and referenced from state. The path may be overridden via `agent_config`.

## Contracts

The walking skeleton keeps `artifacts` and `confidence` in the result contract for parity with future real adapters.

### `Artifact`

```python
@dataclass
class Artifact:
    kind: str
    ref: str
    detail: str = ""
```

### `ToolResult`

```python
@dataclass
class ToolResult:
    tool: str
    args: dict
    stdout: str
    artifacts: list[Artifact] = field(default_factory=list)
    output_hash: str = ""
    confidence: str = "confirmed"
    status: str = "ok"
    error: str = ""
```

### `PlannedAction`

```python
@dataclass
class PlannedAction:
    id: str
    tool: str
    args: dict
    reason: str
```

### `CriticDecision`

```python
@dataclass
class CriticDecision:
    outcome: str
    summary: str
```

Allowed `outcome` values:

- `success`
- `retry`
- `blocked`
- `failure`
- `attempts_exhausted`

### `AuditEvent`

```python
@dataclass
class AuditEvent:
    ts: str
    run_id: str
    thread_id: str
    planner: str
    tool: str
    args: dict
    decision: str
    output_hash: str
    status: str
    correction_of: str | None
    latency_ms: int
```

### `FinalDecision`

```python
@dataclass
class FinalDecision:
    status: str
    summary: str
```

Required event field expectations for tests:

- `ts`
- `run_id`
- `thread_id`
- `planner`
- `tool`
- `args`
- `decision`
- `output_hash`
- `status`
- `correction_of`
- `latency_ms`

## State Model

The graph state should stay minimal and explicit.

Required state fields:

- `request_text`
- `planner_mode`
- `adapter_mode`
- `available_tools`
- `attempt_count`
- `max_attempts`
- `current_action`
- `action_history`
- `result_history`
- `last_result`
- `last_block_reason`
- `final_response`
- `audit_log_path`

The state is responsible for carrying only loop data. It does not introduce report generation or long-term domain memory in this slice.

## Control Flow

### Success path

1. `plan` creates an allow-listed action
2. `guardrail_check` allows it and audits the allow decision if needed by implementation
3. `act` runs the adapter
4. `observe` stores the `ToolResult`
5. `critic` classifies the result as success
6. `finalize_success` returns the final assistant message

### Scripted correction path

1. `plan` emits deterministic action id `action-001`
2. `guardrail_check` allows the action
3. `act` calls an allow-listed `FakeAdapter` tool
4. `FakeAdapter` returns deterministic runtime failure
5. `observe` stores the failed result
6. `critic` classifies the result as `retry`
7. `plan` emits deterministic retry id `action-002`
8. `guardrail_check` allows the retry
9. `act` returns deterministic success
10. `observe` stores the successful result
11. `critic` classifies the result as `success`
12. `finalize_success` returns a summary mentioning failure then recovery

Audit expectation:

- first action event has `correction_of = null`
- second action event has `correction_of = "action-001"`

### Guardrail blocked path

1. `plan` emits a non-allow-listed tool
2. `guardrail_check` blocks the action
3. a blocked audit event is written with `decision = "blocked"`
4. `finalize_blocked` returns a blocked summary

This route is separate from adapter runtime failure and is tested independently.

### Attempts exhausted path

1. retryable failures continue until `attempt_count >= max_attempts`
2. `critic` returns `attempts_exhausted`
3. `finalize_attempts_exhausted` returns a bounded failure summary

This terminal node is required so the graph always terminates, including on the optional LLM path.

## Config Surface

The agent uses the existing `agent_config` field already supported by the service and client.

Supported config keys:

- `planner_mode`
  - `scripted` default
  - `llm`
- `adapter_mode`
  - `fake` default
- `max_attempts`
  - integer, default `2`
- `audit_log_dir`
  - optional override for JSONL output location

No new global settings are introduced for Slice 1.

## Integration Details

### Agent registration

Register `avg-rms-core` in `src/agents/agents.py` with a description that reflects the walking skeleton and fake adapter usage.

### Service path

The existing `/{agent_id}/invoke` and `/{agent_id}/stream` routes remain unchanged. The new agent must work through `get_agent(agent_id)` like the existing registry entries.

### Client path

The existing `AgentClient.invoke()` and `AgentClient.ainvoke()` remain unchanged. Tests and manual runs select the agent by id and pass planner and adapter settings via `agent_config`.

## Testing Strategy

### Unit tests

- `ScriptedPlanner` returns deterministic action ids and retry sequence
- `GuardrailGate` denies non-allow-listed tools
- `FakeAdapter` produces deterministic stdout, deterministic hashes, and a forced runtime failure followed by success

### Integration tests

Through the existing service test path:

- one prompt drives the scripted planner through failure then correction
- final response summarizes recovery
- audit log contains all required `AuditEvent` fields
- second action event sets `correction_of` to the first action id

### Deny test

Required separate test:

- non-allow-listed tool
- `decision = "blocked"`
- blocked event is audited

### LLM path validation

Manual smoke run only:

- `planner_mode = llm`
- loop completes at least once end to end
- no test assertion depends on LLM behavior

## Reproducibility Requirements

The scripted path must be byte-reproducible.

Required controls:

- fixed `FakeAdapter.stdout`
- deterministic action ids
- deterministic retry order
- stable `output_hash` for scripted results

Tests assert reproducibility only on the scripted path.

## Done-When Criteria

This slice is complete when all of the following are true:

- `avg-rms-core` is registered as a new agent
- one prompt can invoke it through the existing service and client path
- the default scripted path runs against `FakeAdapter`
- the first scripted action fails due to an allow-listed adapter runtime error
- the critic emits a retry
- the second scripted action succeeds
- the audit log records both events
- the second event sets `correction_of` to the first action id
- a non-allow-listed tool is blocked and audited in a dedicated test
- attempts exhausted terminates through an explicit terminal node
- the optional `LLMPlanner` runs the same loop manually at least once

## Sequence After This Slice

- Slice 2: implement the SIFT adapter behind the same adapter contract
- Slice 3: implement the Splunk adapter behind the same adapter contract
