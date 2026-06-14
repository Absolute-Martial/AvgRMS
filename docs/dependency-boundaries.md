# Dependency Boundaries

## External dependency boundaries

- Base code builds on `agent-service-toolkit` under the inherited MIT license.
- Splunk access uses `splunk-sdk-python` as a dependency rather than vendored source.
- MCP integration uses `langchain-mcp-adapters` plus one externally run Splunk MCP server.
- Detection content will be adapted from `security_content` and MITRE mapping sources with attribution where used.
- `SplunkGPT` is reference-only and no source code is copied into this repository.
