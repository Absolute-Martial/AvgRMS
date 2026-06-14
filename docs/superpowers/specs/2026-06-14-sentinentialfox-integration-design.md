# Sentinentialfox Integration Design

## Goal

Build `sentinentialfox` as an agentic Splunk security investigator for the Splunk Agentic Ops Hackathon by integrating existing open-source projects rather than rebuilding their capabilities from scratch. The runtime should be dominated by `incidentfox` as the host application and UI base, while adapting `aurora`'s investigation flow into `incidentfox`'s orchestration model. The resulting system must keep the existing safety-layer behavior unchanged for the carried-over modules: `ToolAdapter`/`ToolResult`, `guardrails.py`, `pii.py`, and the JSONL audit writer.

## Source Of Truth

The current source of truth is the user's integration brief from June 14, 2026 plus the clarified decisions made during this design pass:

- Fresh integration workspace.
- `incidentfox` is the dominant host application.
- `aurora` logic is adapted into `incidentfox`; it is not reimplemented from scratch.
- Upstream projects should stay recognizable and reusable; custom code should be glue and translation, not handwritten clones of upstream behavior.
- `SplunkGPT` may be used directly in this project because the user explicitly stated it is their own offline project and they are managing that risk.
- Splunk access remains read-only unless explicitly approved otherwise.

## Scope

This design covers the first implementation cycle needed to produce a coherent, runnable integration base. It does not claim that the full hackathon feature set will be complete in the first cycle. The immediate objective is to connect the major upstream systems in a way that keeps the application runnable and makes later Splunk-specific expansion straightforward.

Included in scope:

- Cloning and preserving the named upstream repositories in a fresh workspace layout.
- Inspecting the real `incidentfox` and `aurora` code layout before fixing module boundaries.
- Retargeting `incidentfox` from its existing infrastructure assumptions toward Splunk investigation workflows.
- Translating `aurora`'s `plan -> investigate -> synthesize` logic into `incidentfox`'s orchestration model.
- Porting the existing core safety modules unchanged in behavior, along with their tests.
- Introducing a shared Splunk tool boundary based on `ToolAdapter`/`ToolResult`.
- Preparing one hostable app surface using the `incidentfox` UI base, with Streamlit hosting compatibility where practical.

Excluded from immediate scope:

- Rewriting `incidentfox` or `aurora` into a brand-new custom framework.
- Building a second parallel application shell outside the `incidentfox` host app.
- Implementing destructive Splunk actions.
- Full compliance RAG, threat intel, or KV-store expansion in the first implementation cycle.

## Architecture Summary

`incidentfox` remains the visible host product: app shell, primary UI, and top-level orchestration entrypoint. `aurora` contributes the investigation engine shape: planning, investigation execution, and synthesis/RCA formatting. A custom translation layer adapts `aurora`'s graph semantics into the host application's agent/task lifecycle instead of replacing `incidentfox` with a separate graph runtime.

All outbound actions to Splunk or any external tool surface must pass through the preserved `ToolAdapter`/`ToolResult` contract. This ensures the guardrails, PII masking, and audit writer remain central to the system and can be preserved without changing their behavior. Splunk access is provided through `mcp-for-splunk`, `splunk-sdk-python`, and selected prompt/search patterns from `SplunkGPT`.

## Workspace Structure Strategy

The workspace should be set up as a fresh integration tree with clear separation between upstream sources and custom glue:

- top-level upstream clone directories for the primary runtime repositories
- a `references/` area for study-only or content repositories
- a custom integration package/module area for translation code, preserved safety modules, and project-level configuration

The exact concrete paths should be decided only after inspecting the cloned repositories. The design intentionally avoids inventing internal file paths before the code is present.

## Major Components

### 1. Incidentfox Host Layer

This layer provides the app shell and remains the dominant runtime. It should be adapted, not replaced. Its responsibilities are:

- own the main entrypoint
- own the user-facing workflow and UI surface
- own the multi-agent or multi-step orchestration shell
- expose the point where adapted `aurora` investigation phases are invoked

The integration should strip or retarget infrastructure assumptions that are specific to its original Kubernetes/Prometheus domain and replace them with Splunk-relevant investigation concerns.

### 2. Aurora Translation Layer

This layer adapts `aurora` into the host application instead of running it as an unrelated adjacent product. Its responsibilities are:

- import or lift `aurora`'s planning/investigation/synthesis logic
- map that logic into `incidentfox`'s agent/task lifecycle
- normalize state transitions into `sentinentialfox` domain terms
- preserve the graph-shaped investigation semantics where possible

The translation layer should define normalized concepts such as:

- `InvestigationGraph`
- `plan_node`
- `investigate_node`
- `synthesize_node`

These names describe the local integration vocabulary, but the implementation should still be visibly derived from `aurora` rather than rewritten freehand.

### 3. Safety And Tool Boundary

The carried-over safety layer is a hard boundary, not an optional add-on. The following modules are preserved unchanged in behavior:

- `ToolAdapter`/`ToolResult`
- `guardrails.py`
- `pii.py`
- JSONL audit writer

All external actions pass through this layer. This layer is responsible for:

- deny-destructive SPL enforcement
- allow-list enforcement
- optional PII masking
- structured audit output for every tool invocation

Its tests must be carried over and kept green before deeper runtime changes proceed.

### 4. Splunk Access Layer

The system should support both direct and mediated Splunk access:

- `mcp-for-splunk` as the main MCP tool surface
- `splunk-sdk-python` for REST/search execution support
- `SplunkGPT` patterns for NL-to-SPL and search prompt construction

The first implementation cycle does not need to maximize feature breadth. It needs a stable, auditable, read-only path that can serve real or stubbed Splunk interactions through the shared tool contract.

### 5. Content And Guardrail References

The following projects shape content and policy but do not define the host runtime:

- `splunk-community-ai` for guardrail rule structure
- `security_content` and `DA-ESS-MitreContent` for detection content and MITRE mappings
- `enterprise-rag-patterns` and `RAG-Based-policy-agent` as stretch references
- `Splunk-createkvstore` as a stretch reference for compliance storage
- `threatintel` and `attack-detections-collector` as stretch references

## Control Flow

The intended control flow is:

1. User enters a prompt through the `incidentfox`-based interface.
2. `incidentfox` routes that request into its dominant orchestration path.
3. The host orchestration invokes the `aurora` translation layer for planning and investigation sequencing.
4. The translation layer emits normalized investigative actions.
5. Each action executes only through the preserved `ToolAdapter`/`ToolResult` boundary.
6. Guardrails, masking, and audit logging wrap each action.
7. Results return to the translation layer for synthesis.
8. The synthesized investigation output is returned to the `incidentfox` host for display and reporting.

This flow keeps `incidentfox` in charge of the user-facing experience while making `aurora` the investigation logic source.

## First Implementation Cycle

The first implementation cycle should produce one running integration slice with preserved safety behavior. The cycle should proceed in this order:

1. Clone the primary upstream projects and reference repositories into the fresh workspace.
2. Inspect the real code layout of `incidentfox` and `aurora`.
3. Identify the actual `incidentfox` entrypoint, orchestration modules, and UI wiring.
4. Identify the actual `aurora` graph/planning/investigation modules worth lifting or adapting.
5. Port the carried-over safety modules and their tests into the integration tree.
6. Re-establish those tests as a baseline.
7. Build the first translation seam from `incidentfox` orchestration into `aurora` plan/investigate/synthesize flow.
8. Connect that seam to a stub or shallow Splunk adapter behind `ToolAdapter`/`ToolResult`.
9. Keep the app runnable while progressively swapping domain assumptions from the original `incidentfox` behavior toward Splunk investigation.

This first cycle is successful if the application can run as a coherent host shell and demonstrate the integrated control flow, even if deeper Splunk breadth is still incomplete.

## Normalized Domain Objects

The integration should normalize around the following project-specific names:

- `InvestigationGraph`
- `ComplianceFinding`
- `SplunkMCPAdapter`
- `CorrelationEngine`

These objects should be introduced only where they clarify the integration. They should not become an excuse to rewrite mature upstream behavior from first principles.

## Hosting Direction

The target product should remain hostable through the `incidentfox` app/UI base and compatible with a Streamlit-hosted presentation if the upstream structure allows it cleanly. The design intent is to preserve an already-existing UI advantage from `incidentfox` rather than replace it with a separate temporary demo shell.

If `incidentfox`'s existing UI stack is not directly Streamlit-based, the adaptation should prefer a thin hosting bridge over a UI rewrite.

## Safety Constraints

The following constraints are mandatory:

- Splunk interactions are read-only by default.
- Any destructive or irreversible action requires explicit user approval first.
- Guardrails must block destructive SPL patterns such as delete-oriented behavior.
- Audit evidence must clearly distinguish real calls from stubbed or simulated behavior.
- Reports and status updates must remain honest about what is implemented versus what is placeholder behavior.

## Attribution And Upstream Integrity

Every reused upstream component should be attributed clearly in documentation. The integration should preserve enough upstream structure that future updates, comparisons, and honest hackathon attribution remain possible.

The guiding rule is:

- reuse and adapt upstream code where possible
- isolate custom glue clearly
- avoid silent code laundering into a brand-new local architecture

## Testing Strategy

The existing 27 passing tests around the carried-over safety modules are the first hard checkpoint. After that, the next tests should cover:

- the translation seam from `incidentfox` orchestration into `aurora` phases
- guardrail enforcement around Splunk tool calls
- audit logging coverage of each tool invocation
- honest handling of stubbed versus real Splunk responses

The initial integration should prioritize a small number of trustworthy tests over broad shallow coverage.

## Risks And Mitigations

### Upstream mismatch

Risk: `incidentfox` and `aurora` may have incompatible lifecycle assumptions.

Mitigation: preserve a dedicated translation layer rather than forcing a direct merge of their internal abstractions.

### Integration drift into rewrite

Risk: custom glue may silently become a from-scratch system.

Mitigation: keep upstream repos intact, keep custom code isolated, and derive logic from inspected upstream modules rather than handwritten equivalents.

### Hostability mismatch

Risk: `incidentfox`'s existing app surface may not map cleanly to Streamlit hosting.

Mitigation: prefer a thin hosting bridge or adapter layer rather than replacing the UI.

### Safety regression

Risk: deeper runtime integration may bypass guardrails or audit behavior.

Mitigation: force all external calls through `ToolAdapter`/`ToolResult` and restore the carried-over tests before deeper integration.

## Success Criteria

This design is successful when:

- `incidentfox` remains the dominant host application
- `aurora` investigation flow is visibly adapted into that host instead of rewritten
- the carried-over safety modules behave unchanged and keep their tests passing
- the system has a coherent Splunk-facing execution seam
- the resulting codebase is honest about what is upstream, what is adapted, and what is still stubbed
