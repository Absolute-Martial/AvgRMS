from __future__ import annotations

from click.testing import CliRunner

from incidentfox.local.incidentfox_cli import cli


def test_cli_local_investigation_bypasses_remote_requirements(monkeypatch) -> None:
    calls: list[str] = []

    def fake_run_local_investigation(prompt: str) -> dict:
        calls.append(prompt)
        return {
            "adapter_mode": "stub",
            "plan": {"goal": prompt},
            "investigation": {
                "status": "ok",
                "tool_name": "splunk.search",
                "query": "search index=main | head 5",
            },
            "synthesis": {"summary": "Local investigation summary"},
        }

    def fail_check_health(self) -> bool:  # pragma: no cover - should not run
        raise AssertionError("remote health check should be skipped")

    monkeypatch.delenv("TEAM_TOKEN", raising=False)
    monkeypatch.setattr(cli, "run_local_investigation", fake_run_local_investigation)
    monkeypatch.setattr(cli.AgentClient, "check_health", fail_check_health)

    result = CliRunner().invoke(
        cli.main,
        ["--local-investigate", "Check unusual access"],
    )

    assert result.exit_code == 0
    assert calls == ["Check unusual access"]
    assert "Local investigation summary" in result.output
    assert "Adapter mode: stub" in result.output
    assert "SentinentialFox" in result.output
