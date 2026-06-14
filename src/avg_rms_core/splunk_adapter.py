import hashlib
import json
from typing import Any

import httpx

from avg_rms_core.contracts import Artifact, ToolResult
from avg_rms_core.pii import mask_pii


DENY_PATTERNS = ("| delete", "| collect ")


def deny_destructive_spl(spl: str) -> str:
    normalized = spl.lower()
    if any(pattern in normalized for pattern in DENY_PATTERNS):
        return "blocked"
    return "allowed"


class SplunkAdapter:
    name = "splunk"

    def __init__(
        self,
        base_url: str,
        token: str,
        app: str = "search",
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.app = app
        self.verify_ssl = verify_ssl

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": "search_spl"}, {"name": "get_index_info"}]

    def run_tool(self, tool: str, args: dict[str, Any]) -> ToolResult:
        if tool == "search_spl":
            return self.search_spl(args["spl"])
        raise ValueError(f"unsupported Splunk tool: {tool}")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _normalize_search_result(self, spl: str, rows: list[dict[str, Any]]) -> ToolResult:
        payload = json.dumps(rows, sort_keys=True)
        masked_payload = mask_pii(payload)
        return ToolResult(
            tool="search_spl",
            args={"spl": spl},
            stdout=masked_payload,
            artifacts=[
                Artifact(kind="spl_query", ref=spl),
                Artifact(kind="spl_event", ref=f"rows:{len(rows)}", detail=masked_payload[:200]),
            ],
            output_hash=hashlib.sha256(masked_payload.encode("utf-8")).hexdigest(),
            status="ok",
        )

    def search_spl(self, spl: str) -> ToolResult:
        response = httpx.post(
            f"{self.base_url}/services/search/jobs/export",
            headers=self._headers(),
            data={"search": spl, "output_mode": "json"},
            verify=self.verify_ssl,
            timeout=60,
        )
        response.raise_for_status()
        rows = [line for line in response.text.splitlines() if line.strip()]
        parsed = [json.loads(line).get("result", {}) for line in rows if '"result"' in line]
        return self._normalize_search_result(spl=spl, rows=parsed)
