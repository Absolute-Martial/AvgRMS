from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from sentinentialfox.safety.guardrails import enforce_safe_spl
from sentinentialfox.safety.tool_contract import ToolResult


@dataclass(slots=True)
class SplunkRestBackend:
    base_url: str | None
    token: str | None
    user_id: str = "sentinentialfox"
    timeout: int = 30

    @property
    def status(self) -> str:
        return "configured" if self.base_url and self.token else "unconfigured"

    @property
    def reason(self) -> str:
        missing: list[str] = []
        if not self.base_url:
            missing.append("SPLUNK_BACKEND_URL")
        if not self.token:
            missing.append("SPLUNK_TOKEN")
        return "" if not missing else f"Missing SPLUNK config: {', '.join(missing)}"

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "SplunkRestBackend":
        return cls(
            base_url=env.get("SPLUNK_BACKEND_URL"),
            token=env.get("SPLUNK_TOKEN"),
            user_id=env.get("SPLUNK_USER_ID", "sentinentialfox"),
            timeout=int(env.get("SPLUNK_TIMEOUT", "30")),
        )

    def is_configured(self) -> bool:
        return self.status == "configured"

    def search(
        self,
        query: str,
        *,
        earliest_time: str = "-24h",
        latest_time: str = "now",
        max_count: int = 100,
    ) -> ToolResult:
        safe_query = enforce_safe_spl(query)
        if not self.is_configured():
            return ToolResult(
                content="unconfigured",
                structured_content={
                    "tool_name": "splunk.search",
                    "status": "unconfigured",
                    "mode": "rest-backend",
                    "query": safe_query,
                    "error": self.reason,
                },
            )

        request_data = json.dumps(
            {
                "query": safe_query,
                "earliestTime": earliest_time,
                "latestTime": latest_time,
                "maxCount": max_count,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint("/splunk/search"),
            data=request_data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-User-ID": self.user_id,
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw_content = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_content = exc.read().decode("utf-8", errors="replace")
            return ToolResult(
                content=raw_content,
                structured_content={
                    "tool_name": "splunk.search",
                    "status": "error",
                    "mode": "rest-backend",
                    "query": safe_query,
                    "http_status": exc.code,
                },
            )
        except urllib.error.URLError as exc:
            return ToolResult(
                content=str(exc),
                structured_content={
                    "tool_name": "splunk.search",
                    "status": "error",
                    "mode": "rest-backend",
                    "query": safe_query,
                    "error": str(exc.reason),
                },
            )

        parsed: dict[str, Any]
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            parsed = {"raw": raw_content}

        parsed.setdefault("tool_name", "splunk.search")
        parsed.setdefault("status", "ok")
        parsed.setdefault("mode", "rest-backend")
        parsed.setdefault("query", safe_query)
        return ToolResult(content=raw_content, structured_content=parsed)

    def run_tool(self, name: str, args: dict[str, Any]) -> ToolResult:
        if name != "splunk.search":
            return ToolResult(
                content="unsupported",
                structured_content={
                    "tool_name": name,
                    "status": "unsupported",
                    "mode": "rest-backend",
                    "error": f"Unsupported tool: {name}",
                },
            )
        return self.search(
            args.get("query", ""),
            earliest_time=args.get("earliestTime", "-24h"),
            latest_time=args.get("latestTime", "now"),
            max_count=int(args.get("maxCount", 100)),
        )

    def _endpoint(self, path: str) -> str:
        assert self.base_url is not None
        return urllib.parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
