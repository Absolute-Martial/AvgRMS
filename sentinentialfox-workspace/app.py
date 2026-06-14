from __future__ import annotations

from pathlib import Path

import streamlit as st

from sentinentialfox.presentation.streamlit_view import build_investigation_snapshot
from sentinentialfox.runtime.service import run_investigation
from sentinentialfox.safety.audit import AuditWriter


APP_TITLE = "SentinentialFox"
AUDIT_PATH = Path("artifacts/streamlit-audit.jsonl")


def _append_audit(prompt: str, result: dict) -> None:
    writer = AuditWriter(AUDIT_PATH)
    writer.append(
        event_type="streamlit_investigation",
        tool_name=result["investigation"]["tool_name"],
        payload={
            "prompt": prompt,
            "adapter_mode": result["adapter_mode"],
            "status": result["investigation"]["status"],
            "query": result["investigation"]["query"],
        },
        decision="streamlit",
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🦊", layout="wide")

    if "history" not in st.session_state:
        st.session_state.history = []

    st.title("🦊 SentinentialFox")
    st.caption("Agentic Splunk investigator with a Streamlit Cloud entrypoint.")

    with st.sidebar:
        st.subheader("Runtime")
        st.write("Primary path: Splunk REST backend")
        st.write("Fallback path: local stub backend")
        st.write(f"Audit log: `{AUDIT_PATH}`")

    prompt = st.text_area(
        "Investigation prompt",
        value="Investigate suspicious login activity",
        height=120,
        help="Describe the incident or compliance question you want investigated.",
    )

    run_clicked = st.button("Run Investigation", type="primary", use_container_width=True)

    if run_clicked:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            st.warning("Enter an investigation prompt first.")
        else:
            with st.spinner("Running investigation..."):
                result = run_investigation(clean_prompt)
                _append_audit(clean_prompt, result)
                snapshot = build_investigation_snapshot(result)
                st.session_state.history.insert(0, snapshot)

    if st.session_state.history:
        latest = st.session_state.history[0]

        top = st.columns(4)
        top[0].metric("Adapter", latest["adapter_mode"])
        top[1].metric("Status", latest["status"])
        top[2].metric("Tool", latest["tool_name"])
        top[3].metric("Results", str(latest["result_count"]))

        st.subheader("Summary")
        st.write(latest["summary"] or "No synthesis summary returned.")

        st.subheader("Executed Query")
        st.code(latest["query"] or "No query recorded.", language="spl")

        st.subheader("Search Results")
        if latest["results"]:
            st.json(latest["results"])
        else:
            st.info("No result rows returned.")

        with st.expander("Run History", expanded=False):
            for index, item in enumerate(st.session_state.history, start=1):
                st.markdown(f"**Run {index}:** {item['goal']}")
                st.write(item["summary"])
                st.caption(
                    f"Adapter={item['adapter_mode']} | Status={item['status']} | Results={item['result_count']}"
                )
                st.divider()
    else:
        st.info("Run an investigation to populate the dashboard.")


if __name__ == "__main__":
    main()
