# Architecture Diagram

Browser -> Streamlit -> `avg-rms-core` `@entrypoint` -> Gemma via OpenRouter + Foundation-Sec -> `SplunkAdapter` -> Splunk Cloud REST

Guardrails sit between planning and tool execution:

- deny-by-default tool allow-list
- destructive SPL blocking
- PII masking before model and UI output

Audit output is written as JSONL with `action_id`, `event_type`, and `correction_of` so retries and self-corrections are explicit.
