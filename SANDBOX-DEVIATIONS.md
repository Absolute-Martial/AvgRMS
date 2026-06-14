# SANDBOX-DEVIATIONS

Status: code-complete, not done

This branch is intentionally being closed as code-complete only. The implementation is verified enough for the Phase 1 walking skeleton slice, but the following deviations were introduced or left open because of the current sandboxed environment.

## 1. Git portability is not yet proven

- Local git history is currently operating through `.git.broken-2026-06-14` with explicit `--git-dir` and `--work-tree` flags.
- Treat this repository state as locally usable but not yet trusted for remote portability.
- Before relying on this history for submission, verify:
  - normal `git status` works without explicit flags
  - remote push to `origin` works
  - commit graph and branch history remain intact after that verification

Required closure:
- prove real-remote pushability with intact history before trusting this repo layout

## 2. Architecture deviated from the approved StateGraph shape

- The approved design called for an explicit `StateGraph` with named nodes for `plan`, `guardrail_check`, `act`, `observe`, `critic`, and terminal states.
- In this sandbox, the `StateGraph` implementation deadlocked in the LangGraph runtime for this slice.
- The working implementation was moved to a LangGraph `@entrypoint` loop that preserves the same behavioral sequence and audit semantics, but not the same graph surface.

Required closure:
- add an ADR documenting the StateGraph to `@entrypoint` deviation and the reason
- update the architecture diagram and any related docs to match the actual `@entrypoint` implementation

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
