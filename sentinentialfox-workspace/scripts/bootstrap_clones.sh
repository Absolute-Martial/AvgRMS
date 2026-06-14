#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p references

clone() {
  local dir="$1"
  local url="$2"
  if [ -d "$dir/.git" ]; then
    echo "skip $dir"
  else
    git clone --depth 1 "$url" "$dir"
    echo "ok $dir"
  fi
}

echo "== Primary bases =="
clone incidentfox https://github.com/incidentfox/incidentfox.git
clone aurora https://github.com/Arvo-AI/aurora.git
clone agent-service-toolkit https://github.com/JoshuaC215/agent-service-toolkit.git
clone mcp-for-splunk https://github.com/deslicer/mcp-for-splunk.git
clone splunk-sdk-python https://github.com/splunk/splunk-sdk-python.git

echo "== References =="
clone references/SplunkGPT https://github.com/KingOfTheNOPs/SplunkGPT.git
clone references/langchain-mcp-adapters https://github.com/langchain-ai/langchain-mcp-adapters.git
clone references/splunk-mcp-server2 https://github.com/splunk/splunk-mcp-server2.git
clone references/splunk-mcp https://github.com/livehybrid/splunk-mcp.git
clone references/fastapi-langgraph-template https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template.git
clone references/OpenRCA https://github.com/microsoft/OpenRCA.git
clone references/agentic-soc-platform https://github.com/FunnyWolf/agentic-soc-platform.git
clone references/security_content https://github.com/splunk/security_content.git
clone references/DA-ESS-MitreContent https://github.com/seynur/DA-ESS-MitreContent.git
clone references/attack-detections-collector https://github.com/splunk/attack-detections-collector.git
clone references/threatintel https://github.com/splunkchamp/threatintel.git
clone references/splunk-community-ai https://github.com/billebel/splunk-community-ai.git
clone references/enterprise-rag-patterns https://github.com/ashutoshrana/enterprise-rag-patterns.git
clone references/RAG-Based-policy-agent https://github.com/Srujanrana07/RAG-Based-policy-agent.git
clone references/Splunk-createkvstore https://github.com/georgestarcher/Splunk-createkvstore.git
