import hashlib

from avg_rms_core.contracts import ToolResult


class FakeAdapter:
    name = "fake"

    def __init__(self, mode: str = "fail_once") -> None:
        self.mode = mode
        self.calls = 0

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": "fake.lookup"}]

    def run_tool(self, tool: str, args: dict) -> ToolResult:
        self.calls += 1
        target = args["target"]
        if self.mode == "always_fail" or (self.mode == "fail_once" and self.calls == 1):
            stdout = f"FAKE_LOOKUP_ERROR target={target}\n"
            return ToolResult(
                tool=tool,
                args=args,
                stdout=stdout,
                output_hash=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
                status="error",
                error="simulated runtime error",
            )
        stdout = f"FAKE_LOOKUP_OK target={target}\n"
        return ToolResult(
            tool=tool,
            args=args,
            stdout=stdout,
            output_hash=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            status="ok",
        )
