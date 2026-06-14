from streamlit.testing.v1 import AppTest


def test_complianceguard_streamlit_renders_hero_flow():
    at = AppTest.from_file("../../src/streamlit_app.py").run()

    assert at.title[0].value == "ComplianceGuard"
    assert at.text_area[0].value.startswith("Who accessed EU customer PII")
    assert not at.exception
