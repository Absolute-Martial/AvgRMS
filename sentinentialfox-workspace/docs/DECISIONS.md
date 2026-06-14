# Decisions

Last updated: 2026-06-14

## D-001: Use Aurora's Splunk REST backend as the defined primary runtime path

Status: accepted

Decision:

- The defined backend REST API for Splunk is Aurora's Flask backend:
  - [server/main_compute.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/main_compute.py)
  - [server/routes/splunk/splunk_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/splunk_routes.py)
  - [server/routes/splunk/search_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/search_routes.py)
  - [server/routes/splunk/tasks.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/tasks.py)

Why:

- It is already a concrete HTTP backend, not just a library or MCP adapter.
- It includes both connector lifecycle and investigation-facing endpoints.
- It already bridges to Aurora's UI and incident pipeline.
- It gives `sentinentialfox` a concrete REST shape for connect, search, alerts, and RCA settings.

Consequences:

- Treat Aurora `/splunk/*` as the baseline contract.
- Do not define `mcp-for-splunk` as the main runtime path.
- Do not define `splunk-sdk-python` as the main runtime path.

## D-002: Treat `mcp-for-splunk` as a secondary integration/reference path

Status: accepted

Decision:

- Keep `mcp-for-splunk` as a secondary/reference path only:
  - [src/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/server.py)
  - [src/tools/search/oneshot_search.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/tools/search/oneshot_search.py)
  - [src/tools/search/job_search.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/tools/search/job_search.py)
  - [src/client/splunk_client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/client/splunk_client.py)

Why:

- It is useful for MCP-native clients and tool discovery.
- It is not the simplest primary backend for a product that already wants a direct REST runtime.
- Its value is strongest as a protocol adapter and tool catalogue, not as the single backend definition.

## D-003: Treat `splunk-sdk-python` as a low-level implementation reference

Status: accepted

Decision:

- Keep `splunk-sdk-python` as an SDK/reference dependency only:
  - [splunklib/client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/client.py)
  - [splunklib/binding.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/binding.py)
  - [splunklib/results.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/results.py)

Why:

- It is a developer SDK for talking to Splunk's platform API.
- It does not define the application-level REST contract we need.
- It remains useful if `sentinentialfox` later needs a lower-level Splunk client abstraction behind the REST layer.

## D-004: Prefer Aurora as the architectural reference for orchestration modules

Status: accepted

Decision:

- For graph/planning/investigation/synthesis structure, Aurora is the clearer upstream reference:
  - [server/chat/backend/agent/workflow.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/workflow.py)
  - [server/chat/backend/agent/orchestrator/triage.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/triage.py)
  - [server/chat/backend/agent/orchestrator/dispatcher.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/dispatcher.py)
  - [server/chat/backend/agent/orchestrator/sub_agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/sub_agent.py)
  - [server/chat/backend/agent/orchestrator/synthesis.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/synthesis.py)
  - [server/routes/graph_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/graph_routes.py)

Why:

- Aurora exposes an explicit LangGraph-style workflow and named orchestrator stages.
- IncidentFox has strong service boundaries, but its investigation flow is spread across Slack handlers, the SRE API, and support services rather than a single clearly factored planner/synthesizer package.

## D-005: Treat IncidentFox as a service-layout and Slack-first reference, not the primary orchestration template

Status: accepted

Decision:

- Use IncidentFox for examples of:
  - Slack-first investigation ingress
  - config-service separation
  - webhook orchestration and provisioning
  - RAPTOR/knowledge graph support
- Do not use it as the primary source for a clean planning/synthesis module split.

Key reference paths:

- [slack-bot/investigation_handler.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/investigation_handler.py)
- [sre-agent/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/server.py)
- [sre-agent/agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/agent.py)
- [orchestrator/src/incidentfox_orchestrator/api_server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/api_server.py)
- [ultimate_rag/graph/graph.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/ultimate_rag/graph/graph.py)

Why:

- IncidentFox is useful, but its runtime concerns are more distributed.
- Aurora is the cleaner direct template for a backend inventory that needs explicit graph/planning/investigation/synthesis boundaries.
