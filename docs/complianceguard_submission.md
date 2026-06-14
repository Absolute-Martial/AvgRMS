# ComplianceGuard Submission

## Tech

- Shared `avg-rms-core` planner, guardrail, act, observe, critic loop
- `SplunkAdapter` over Splunk Cloud REST with normalized `ToolResult` output
- Gemma through OpenRouter for orchestration
- Foundation-Sec or fallback model path for SPL generation and triage
- JSONL audit log with deterministic correction links

## Design

- Hosted Streamlit app runs the agent loop in-process
- Shared-core checkpoint remains domain-agnostic and reusable
- Splunk integration stays behind the `ToolAdapter` boundary
- Read-only guardrails block destructive SPL and keep the audit trail explicit

## Impact

- Turns a security/compliance question into a constrained Splunk investigation flow
- Preserves a self-correction story that judges can inspect in the audit log
- Keeps the submission lightweight enough for a hosted demo while preserving an upgrade path

## Idea

ComplianceGuard applies one reusable orchestration core to compliance-focused incident triage. The same loop that was proven against the fake adapter now drives a Splunk-backed hero flow without coupling the shared baseline to one backend.
