import asyncio
from pathlib import Path

import streamlit as st

from schema import UserInput


APP_TITLE = "ComplianceGuard"
DEFAULT_PROMPT = "Who accessed EU customer PII in the last 30 days, and was it authorized?"
DEFAULT_AUDIT_PATH = Path("data/avg_rms_core.audit.jsonl")


def _secret(name: str, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default


def run_hero_flow(prompt: str) -> str:
    from service import service

    planner_mode = "llm" if _secret("OPENROUTER_API_KEY") else "scripted"
    adapter_mode = "splunk" if _secret("SPLUNK_BASE_URL") and _secret("SPLUNK_TOKEN") else "fake"
    response = asyncio.run(
        service.invoke(
            UserInput(
                message=prompt,
                agent_config={
                    "planner_mode": planner_mode,
                    "adapter_mode": adapter_mode,
                    "splunk_base_url": _secret("SPLUNK_BASE_URL", ""),
                    "splunk_token": _secret("SPLUNK_TOKEN", ""),
                    "splunk_verify_ssl": bool(_secret("SPLUNK_VERIFY_SSL", True)),
                    "openrouter_api_key": _secret("OPENROUTER_API_KEY", ""),
                    "foundation_sec_base_url": _secret("FOUNDATION_SEC_BASE_URL", ""),
                    "foundation_sec_api_key": _secret("FOUNDATION_SEC_API_KEY", ""),
                    "foundation_sec_model": _secret("FOUNDATION_SEC_MODEL", ""),
                    "audit_log_dir": str(DEFAULT_AUDIT_PATH.parent),
                },
            ),
            agent_id="avg-rms-core",
        )
    )
    return response.content


st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Hosted Splunk-only sprint build")

with st.sidebar:
    st.subheader("Required secrets")
    st.code(
        "\n".join(
            [
                "SPLUNK_BASE_URL",
                "SPLUNK_TOKEN",
                "OPENROUTER_API_KEY",
                "FOUNDATION_SEC_BASE_URL",
                "FOUNDATION_SEC_API_KEY",
                "FOUNDATION_SEC_MODEL",
            ]
        )
    )

with st.form("hero"):
    prompt = st.text_area("Question", value=DEFAULT_PROMPT, height=140)
    submitted = st.form_submit_button("Run")

if submitted:
    with st.spinner("Running Splunk investigation..."):
        try:
            st.markdown(run_hero_flow(prompt))
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Investigation failed: {exc}")

if DEFAULT_AUDIT_PATH.exists():
    st.subheader("Audit log")
    st.code(DEFAULT_AUDIT_PATH.read_text(), language="json")
