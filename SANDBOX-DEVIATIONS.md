# SANDBOX-DEVIATIONS

Status: code-complete, not done

This branch is intentionally being closed as code-complete only. The implementation is verified enough for the Phase 1 walking skeleton slice, but the following deviations were introduced or left open because of the current sandboxed environment.

## 1. Remote default branch is still divergent

- This submission repo now has normal local git behavior.
- The fresh history and `shared-core-checkpoint` tag were pushed successfully to the public remote.
- The remote already had an unrelated `main`, so the new history is published on a safe branch instead of overwriting that branch.

Required closure:
- decide whether the public submission should stay on a named branch or replace remote `main`
- do not force-update remote `main` without explicitly validating that the old remote history is disposable

## 2. Architecture deviated from the approved StateGraph shape

- The approved design called for an explicit `StateGraph` with named nodes for `plan`, `guardrail_check`, `act`, `observe`, `critic`, and terminal states.
- In this sandbox, the `StateGraph` implementation deadlocked in the LangGraph runtime for this slice.
- The working implementation was moved to a LangGraph `@entrypoint` loop that preserves the same behavioral sequence and audit semantics, but not the same graph surface.

Required closure:
- add an ADR documenting the StateGraph to `@entrypoint` deviation and the reason
- keep the architecture docs aligned with the actual `@entrypoint` implementation as the repo evolves

## 3. HTTP route is not fully verified in a real app environment

- The slice is verified through `service.invoke()` direct-path tests, not through a fully booted HTTP route in a realistic environment.
- `TestClient` plus real app lifespan was not reliable in this sandbox because startup layers outside the shared-core slice blocked clean route verification.

Required closure:
- verify `POST /avg-rms-core/invoke` in a real environment with working app startup and checkpointer wiring
- confirm the route returns the expected recovery, blocked, and attempts-exhausted behaviors

## 4. Async LLMPlanner path is not fully verified

- The default scripted planner path is the verified path.
- The optional LLMPlanner path was smoke-tested only with the toolkit fake model.
- For the fake model case, planner invocation was forced through a synchronous model call to avoid a fake-model async hang in this environment.

Required closure:
- verify the real async LLMPlanner path with an actual supported model/provider before Phase 2 depends on LLM planning behavior
- remove any fake-model-specific assumptions from confidence in the real LLM path

## License confirmation

- The submission repo root contains `LICENSE`
- That file is MIT

## Branch handling

- Keep this work on a branch.
- Do not merge into an assumed-good `main` until git portability and remote pushability are proven.
