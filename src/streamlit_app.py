import asyncio
from pathlib import Path

import streamlit as st

from schema import UserInput


APP_TITLE = "ComplianceGuard"
DEFAULT_PROMPT = "Who accessed EU customer PII in the last 30 days, and was it authorized?"
DEFAULT_AUDIT_PATH = Path("data/avg_rms_core.audit.jsonl")
OVERRIDE_KEYS = {
    "OPENROUTER_API_KEY": "override_openrouter_api_key",
    "SPLUNK_TOKEN": "override_splunk_token",
    "SPLUNK_HOST": "override_splunk_host",
}


def _secret(name: str, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _effective_value(secret_key: str) -> str | None:
    override_key = OVERRIDE_KEYS[secret_key]
    override = st.session_state.get(override_key, "").strip()
    if override:
        return override
    secret_value = _secret(secret_key)
    if secret_value in (None, ""):
        return None
    return str(secret_value)


def _effective_runtime_config() -> dict[str, str | None]:
    return {
        "openrouter_api_key": _effective_value("OPENROUTER_API_KEY"),
        "splunk_token": _effective_value("SPLUNK_TOKEN"),
        "splunk_host": _effective_value("SPLUNK_HOST"),
    }


def run_hero_flow(prompt: str, runtime_config: dict[str, str | None]) -> str:
    from service import service

    planner_mode = "llm" if runtime_config["openrouter_api_key"] else "scripted"
    adapter_mode = "splunk" if runtime_config["splunk_host"] and runtime_config["splunk_token"] else "fake"
    response = asyncio.run(
        service.invoke(
            UserInput(
                message=prompt,
                agent_config={
                    "planner_mode": planner_mode,
                    "adapter_mode": adapter_mode,
                    "splunk_host": runtime_config["splunk_host"] or "",
                    "splunk_token": runtime_config["splunk_token"] or "",
                    "splunk_port": int(_secret("SPLUNK_PORT", 8089)),
                    "splunk_scheme": _secret("SPLUNK_SCHEME", "https"),
                    "splunk_ca_bundle": _secret("SPLUNK_CA_BUNDLE", None),
                    "splunk_verify_ssl": bool(_secret("SPLUNK_VERIFY_SSL", True)),
                    "openrouter_api_key": runtime_config["openrouter_api_key"] or "",
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

runtime_config = _effective_runtime_config()
missing_required = [
    label
    for label, value in {
        "OpenRouter API key": runtime_config["openrouter_api_key"],
        "Splunk token": runtime_config["splunk_token"],
        "Splunk host": runtime_config["splunk_host"],
    }.items()
    if value is None
]

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
    with st.expander("⚙️ Settings"):
        st.text_input(
            "OpenRouter API key",
            value="",
            type="password",
            key=OVERRIDE_KEYS["OPENROUTER_API_KEY"],
        )
        st.text_input(
            "Splunk token",
            value="",
            type="password",
            key=OVERRIDE_KEYS["SPLUNK_TOKEN"],
        )
        st.text_input(
            "Splunk host",
            value="",
            type="password",
            key=OVERRIDE_KEYS["SPLUNK_HOST"],
        )

if missing_required:
    st.warning(
        "Missing required configuration: " + ", ".join(missing_required) + ". "
        "Provide a sidebar override or configure Streamlit secrets."
    )

with st.form("hero"):
    prompt = st.text_area("Question", value=DEFAULT_PROMPT, height=140)
    submitted = st.form_submit_button("Run", disabled=bool(missing_required))

if submitted:
    with st.spinner("Running Splunk investigation..."):
        try:
            st.markdown(run_hero_flow(prompt, runtime_config))
        except Exception as exc:  # pragma: no cover - UI fallback
            st.error(f"Investigation failed: {exc}")

if DEFAULT_AUDIT_PATH.exists():
    st.subheader("Audit log")
    st.code(DEFAULT_AUDIT_PATH.read_text(), language="json")
