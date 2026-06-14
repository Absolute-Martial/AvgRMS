# Upstream Inventory

Last updated: 2026-06-14

## Scope

This inventory was built from direct inspection of:

- `sentinentialfox-workspace/incidentfox`
- `sentinentialfox-workspace/aurora`
- `sentinentialfox-workspace/mcp-for-splunk`
- `sentinentialfox-workspace/splunk-sdk-python`

The goal is to pin real upstream entrypoints, UI surfaces, orchestration modules, and graph/planning/investigation/synthesis modules that are relevant to `sentinentialfox`.

## Primary Splunk Backend Decision

Defined backend REST API path:

- Aurora Flask backend registered in [server/main_compute.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/main_compute.py)
- Splunk REST blueprints in:
  - [server/routes/splunk/splunk_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/splunk_routes.py)
  - [server/routes/splunk/search_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/search_routes.py)
  - [server/routes/splunk/tasks.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/splunk/tasks.py)

Observed registration:

- `app.register_blueprint(splunk_bp, url_prefix="/splunk")`
- `app.register_blueprint(splunk_search_bp, url_prefix="/splunk")`

Concrete backend REST/API surface exposed by Aurora:

- `/splunk/connect`
- `/splunk/status`
- `/splunk/disconnect`
- `/splunk/alerts`
- `/splunk/alerts/webhook/<user_id>`
- `/splunk/alerts/webhook-url`
- `/splunk/rca-settings`
- `/splunk/search`
- `/splunk/search/jobs`
- `/splunk/search/jobs/<sid>`
- `/splunk/search/jobs/<sid>/results`

Secondary/reference Splunk paths only:

- `mcp-for-splunk`
  - [src/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/server.py)
  - [src/tools/search/oneshot_search.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/tools/search/oneshot_search.py)
  - [src/tools/search/job_search.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/tools/search/job_search.py)
  - [src/client/splunk_client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/mcp-for-splunk/src/client/splunk_client.py)
- `splunk-sdk-python`
  - [splunklib/client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/client.py)
  - [splunklib/binding.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/binding.py)
  - [splunklib/results.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/splunk-sdk-python/splunklib/results.py)

## IncidentFox Inventory

### Runtime entrypoints

- Local stack composition: [docker-compose.yml](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/docker-compose.yml)
- Investigation API server:
  - [sre-agent/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/server.py)
  - Handles investigation sessions, SSE streaming, `/investigate`, `/interrupt`, and health behavior
- Investigation engine:
  - [sre-agent/agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/agent.py)
- Slack runtime:
  - [slack-bot/app.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/app.py)
  - Bolt app with Socket Mode and HTTP/Flask production mode
- Config API:
  - [config_service/src/api/main.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/config_service/src/api/main.py)
  - Docker/README point to `uvicorn src.api.main:app --port 8080`
- Orchestrator API:
  - [orchestrator/src/incidentfox_orchestrator/api_server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/api_server.py)
  - Docker points to `uvicorn incidentfox_orchestrator.api_server:app --port 8070`
- Knowledge/RAG API:
  - [ultimate_rag/api/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/ultimate_rag/api/server.py)
  - Runs a FastAPI app for query, ingest, graph, and teaching

### UI surfaces

- Primary web console:
  - [web_ui/src/app/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app/page.tsx)
  - App routes under [web_ui/src/app](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app)
- Concrete admin/team pages include:
  - [web_ui/src/app/admin/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app/admin/page.tsx)
  - [web_ui/src/app/team/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app/team/page.tsx)
  - [web_ui/src/app/team/knowledge/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app/team/knowledge/page.tsx)
  - [web_ui/src/app/team/agent-runs/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/web_ui/src/app/team/agent-runs/page.tsx)
- Slack UI surface:
  - [slack-bot/app.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/app.py)
  - [slack-bot/home_tab.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/home_tab.py)
  - [slack-bot/modal_handler.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/modal_handler.py)
  - [slack-bot/modal_builder.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/modal_builder.py)
- Static config-service UI exists but is secondary:
  - [config_service/src/ui/index.html](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/config_service/src/ui/index.html)
  - [config_service/src/ui/admin.html](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/config_service/src/ui/admin.html)

### Orchestration modules

- Main orchestration API:
  - [orchestrator/src/incidentfox_orchestrator/api_server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/api_server.py)
- Webhook routing and channeling:
  - [orchestrator/src/incidentfox_orchestrator/webhooks/router.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/webhooks/router.py)
  - [orchestrator/src/incidentfox_orchestrator/webhooks/slack_bolt_app.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/webhooks/slack_bolt_app.py)
  - [orchestrator/src/incidentfox_orchestrator/webhooks/slack_handlers.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/webhooks/slack_handlers.py)
- Provisioning/scheduling/runtime helpers:
  - [orchestrator/src/incidentfox_orchestrator/scheduler.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/scheduler.py)
  - [orchestrator/src/incidentfox_orchestrator/clients.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/clients.py)
  - [orchestrator/src/incidentfox_orchestrator/k8s/client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/k8s/client.py)
  - [orchestrator/src/incidentfox_orchestrator/k8s/cronjobs.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/k8s/cronjobs.py)
  - [orchestrator/src/incidentfox_orchestrator/k8s/deployments.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/orchestrator/src/incidentfox_orchestrator/k8s/deployments.py)

### Graph / planning / investigation / synthesis modules

- Graph / retrieval:
  - [ultimate_rag/graph/graph.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/ultimate_rag/graph/graph.py)
  - [ultimate_rag/graph/entities.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/ultimate_rag/graph/entities.py)
  - [ultimate_rag/api/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/ultimate_rag/api/server.py)
- Investigation ingress and streaming:
  - [slack-bot/investigation_handler.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/investigation_handler.py)
  - [slack-bot/stream_handler.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/stream_handler.py)
  - [sre-agent/server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/server.py)
  - [sre-agent/agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/sre-agent/agent.py)
- Planning:
  - No separate LangGraph-style planner module found in `incidentfox`.
  - The closest control-plane planning/runtime logic is the provisioning and webhook routing layer in `orchestrator`.
- Synthesis:
  - No dedicated synthesis module was found as a standalone package.
  - User-facing result assembly is split across:
    - [slack-bot/message_builder.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/message_builder.py)
    - [slack-bot/markdown_utils.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/markdown_utils.py)
    - [slack-bot/table_converter.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/incidentfox/slack-bot/table_converter.py)

## Aurora Inventory

### Runtime entrypoints

- Stack composition:
  - [docker-compose.yaml](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/docker-compose.yaml)
- Main backend REST API:
  - [server/main_compute.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/main_compute.py)
  - Docker runs `gunicorn main_compute:app`
- Chat/WebSocket runtime:
  - [server/main_chatbot.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/main_chatbot.py)
  - README exposes `ws://localhost:5006`
- MCP runtime:
  - [server/mcp_server.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/mcp_server.py)
- Celery/background runtime:
  - [server/celery_config.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/celery_config.py)

### UI surfaces

- Primary frontend:
  - [client/src/app/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/page.tsx)
  - [client/src/app/layout.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/layout.tsx)
- Concrete application surfaces:
  - Chat: [client/src/app/chat/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/chat/page.tsx)
  - Incidents list: [client/src/app/incidents/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/incidents/page.tsx)
  - Incident detail: [client/src/app/incidents/[id]/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/incidents/[id]/page.tsx)
  - Connectors: [client/src/app/connectors/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/connectors/page.tsx)
  - Monitor: [client/src/app/monitor/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/monitor/page.tsx)
  - Splunk auth: [client/src/app/splunk/auth/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/splunk/auth/page.tsx)
  - Splunk search: [client/src/app/splunk/search/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/splunk/search/page.tsx)
  - Splunk alerts: [client/src/app/splunk/alerts/page.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/splunk/alerts/page.tsx)
- Important chat/investigation widgets:
  - [client/src/components/chat/message-list.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/components/chat/message-list.tsx)
  - [client/src/components/chat/subagent-detail-panel.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/components/chat/subagent-detail-panel.tsx)
  - [client/src/app/incidents/components/SubAgentInvestigationsSection.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/incidents/components/SubAgentInvestigationsSection.tsx)
  - [client/src/app/incidents/components/ExecutionWaterfall.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/app/incidents/components/ExecutionWaterfall.tsx)
  - [client/src/components/incidents/InfrastructureVisualization.tsx](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/client/src/components/incidents/InfrastructureVisualization.tsx)

### Orchestration modules

- LangGraph workflow shell:
  - [server/chat/backend/agent/workflow.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/workflow.py)
- Agent runtime:
  - [server/chat/backend/agent/agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/agent.py)
- Orchestrator package:
  - [server/chat/backend/agent/orchestrator/triage.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/triage.py)
  - [server/chat/backend/agent/orchestrator/dispatcher.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/dispatcher.py)
  - [server/chat/backend/agent/orchestrator/sub_agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/sub_agent.py)
  - [server/chat/backend/agent/orchestrator/synthesis.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/synthesis.py)
  - [server/chat/backend/agent/orchestrator/select_skills.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/select_skills.py)
  - [server/chat/backend/agent/orchestrator/role_registry.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/role_registry.py)
  - [server/chat/backend/agent/orchestrator/findings_writer.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/findings_writer.py)

### Graph / planning / investigation / synthesis modules

- Graph runtime and APIs:
  - [server/routes/graph_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/graph_routes.py)
  - [server/services/graph/memgraph_client.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/services/graph/memgraph_client.py)
  - [server/services/discovery/discovery_service.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/services/discovery/discovery_service.py)
  - [server/services/discovery/graph_writer.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/services/discovery/graph_writer.py)
  - [server/services/discovery/tasks.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/services/discovery/tasks.py)
- Planning/triage:
  - [server/chat/backend/agent/orchestrator/triage.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/triage.py)
  - [server/chat/backend/agent/orchestrator/inputs.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/inputs.py)
  - [server/chat/backend/agent/orchestrator/select_skills.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/select_skills.py)
- Investigation execution:
  - [server/chat/backend/agent/workflow.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/workflow.py)
  - [server/chat/backend/agent/agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/agent.py)
  - [server/chat/backend/agent/orchestrator/dispatcher.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/dispatcher.py)
  - [server/chat/backend/agent/orchestrator/sub_agent.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/sub_agent.py)
  - [server/routes/incidents_routes.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/incidents_routes.py)
  - [server/routes/incidents_sse.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/routes/incidents_sse.py)
- Synthesis and output shaping:
  - [server/chat/backend/agent/orchestrator/synthesis.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/backend/agent/orchestrator/synthesis.py)
  - [server/chat/background/summarization.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/background/summarization.py)
  - [server/chat/background/rca_prompt_builder.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/background/rca_prompt_builder.py)
  - [server/chat/background/citation_extractor.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/background/citation_extractor.py)
  - [server/chat/background/suggestion_extractor.py](/home/lets-smile/PycharmProjects/AvgRMS/sentinentialfox-workspace/aurora/server/chat/background/suggestion_extractor.py)

## Practical Upstream Takeaways

- IncidentFox is split across multiple services. Its operational investigation flow is Slack-first and service-oriented, but it does not expose a clean single planning/synthesis module comparable to Aurora's LangGraph orchestrator package.
- Aurora has the clearest reusable backend contract for `sentinentialfox`:
  - one REST backend in `server/main_compute.py`
  - one chat/websocket runtime in `server/main_chatbot.py`
  - explicit graph routes in `server/routes/graph_routes.py`
  - explicit orchestration nodes in `server/chat/backend/agent/orchestrator/*`
  - explicit Splunk REST endpoints already wired into the backend and frontend
- For Splunk specifically, Aurora's `/splunk/*` backend should be treated as the implementation model; `mcp-for-splunk` and `splunk-sdk-python` are better treated as supporting references, not the primary runtime path.
