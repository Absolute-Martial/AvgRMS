import hashlib
import json
import ssl
from typing import Any, Callable
from urllib.parse import urlparse

import splunklib.client as splunk_client
import splunklib.results as splunk_results

from avg_rms_core.contracts import Artifact, ToolResult
from avg_rms_core.pii import mask_pii


DENY_PATTERNS = ("| delete", "| collect ")


def deny_destructive_spl(spl: str) -> str:
    normalized = spl.lower()
    if any(pattern in normalized for pattern in DENY_PATTERNS):
        return "blocked"
    return "allowed"


def validate_botsv3_read_only_spl(spl: str) -> None:
    normalized = spl.lower()
    if "index=botsv3" not in normalized:
        raise ValueError("Splunk searches must target index=botsv3")
    if deny_destructive_spl(spl) == "blocked":
        raise ValueError("Splunk searches must be read-only")


class SplunkAdapter:
    name = "splunk"

    def __init__(
        self,
        base_url: str | None = None,
        token: str = "",
        app: str = "search",
        verify_ssl: bool | str = True,
        *,
        host: str | None = None,
        port: int = 8089,
        scheme: str = "https",
        verify: bool | str | None = None,
        connect_fn: Callable[..., Any] | None = None,
        results_reader_cls: Callable[[Any], Any] | None = None,
    ) -> None:
        parsed_host, parsed_port, parsed_scheme = self._parse_base_url(base_url)
        self.host = host or parsed_host or "localhost"
        self.port = port if host else parsed_port
        self.scheme = scheme if host else parsed_scheme
        self.token = token
        self.app = app
        self.verify = verify if verify is not None else verify_ssl
        self._connect_fn = connect_fn or splunk_client.connect
        self._results_reader_cls = results_reader_cls or splunk_results.JSONResultsReader

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": "search_spl"}, {"name": "get_index_info"}]

    def run_tool(self, tool: str, args: dict[str, Any]) -> ToolResult:
        if tool == "search_spl":
            return self.search_spl(args["spl"])
        raise ValueError(f"unsupported Splunk tool: {tool}")

    @staticmethod
    def _parse_base_url(base_url: str | None) -> tuple[str | None, int, str]:
        if not base_url:
            return None, 8089, "https"
        parsed = urlparse(base_url)
        scheme = parsed.scheme or "https"
        port = parsed.port or (443 if scheme == "https" else 80)
        return parsed.hostname, port, scheme

    def _connection_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "scheme": self.scheme,
            "app": self.app,
            "bearerToken": self.token,
        }
        if isinstance(self.verify, str):
            kwargs["verify"] = True
            kwargs["context"] = ssl.create_default_context(cafile=self.verify)
        else:
            kwargs["verify"] = self.verify
        return kwargs

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
        validate_botsv3_read_only_spl(spl)
        service = self._connect_fn(**self._connection_kwargs())
        stream = service.jobs.export(spl, output_mode="json", segmentation="none")
        rows = [result for result in self._results_reader_cls(stream) if isinstance(result, dict)]
        return self._normalize_search_result(spl=spl, rows=rows)
