import os
import sys
from pathlib import Path

from avg_rms_core.splunk_adapter import SplunkAdapter


DEFAULT_QUERY = "search index=botsv3 sourcetype=wineventlog | head 5"


def main(argv: list[str]) -> int:
    token = os.environ.get("SPLUNK_TOKEN")
    host = os.environ.get("SPLUNK_HOST")
    if not token or not host:
        raise SystemExit(
            "SPLUNK_TOKEN and SPLUNK_HOST are required. Optional: SPLUNK_PORT, SPLUNK_SCHEME, SPLUNK_CA_BUNDLE."
        )

    query = argv[1] if len(argv) > 1 else DEFAULT_QUERY
    adapter = SplunkAdapter(
        host=host,
        port=int(os.environ.get("SPLUNK_PORT", "8089")),
        scheme=os.environ.get("SPLUNK_SCHEME", "https"),
        token=token,
        verify=os.environ.get("SPLUNK_CA_BUNDLE", "true").lower() == "true"
        if "SPLUNK_CA_BUNDLE" not in os.environ
        else os.environ["SPLUNK_CA_BUNDLE"],
    )
    result = adapter.search_spl(query)

    payload = "\n".join(
        [
            f"query={query}",
            "rows=",
            result.stdout,
        ]
    ).strip() + "\n"
    print(payload)

    evidence_path = Path("docs/evidence/real_splunk_call.txt")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(payload, encoding="utf-8")
    print(f"saved_evidence={evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
