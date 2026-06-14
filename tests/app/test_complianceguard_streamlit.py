import streamlit as st
from streamlit.testing.v1 import AppTest


def test_complianceguard_streamlit_renders_hero_flow():
    original_secrets = st.secrets._secrets
    st.secrets._secrets = {
        "OPENROUTER_API_KEY": "secret-openrouter",
        "SPLUNK_TOKEN": "secret-splunk-token",
        "SPLUNK_HOST": "secret-splunk-host",
    }
    try:
        at = AppTest.from_file("../../src/streamlit_app.py").run()
    finally:
        st.secrets._secrets = original_secrets

    assert at.title[0].value == "ComplianceGuard"
    assert at.text_area[0].value.startswith("Who accessed EU customer PII")
    assert at.expander[0].label == "⚙️ Settings"
    assert [widget.label for widget in at.text_input] == [
        "OpenRouter API key",
        "Splunk token",
        "Splunk host",
    ]
    assert at.button[0].disabled is False
    assert len(at.warning) == 0
    assert not at.exception
