# ComplianceGuard Architecture

This submission runs the ComplianceGuard hero flow directly inside the hosted Streamlit app.

## Runtime path

Browser -> Streamlit -> `avg-rms-core` `@entrypoint` -> planner/guardrail/act/critic loop -> `SplunkAdapter` -> Splunk Cloud REST

## Model split

- Orchestrator: Gemma via OpenRouter
- SPL generation and triage: Foundation-Sec
- Deterministic fallback: scripted planner for tests and reproducible runs

## Safety boundaries

- Deny-by-default tool gate
- Destructive SPL block rules
- PII masking before model and UI output
- JSONL audit log with `action_id`, `event_type`, and `correction_of`
