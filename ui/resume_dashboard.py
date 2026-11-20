from __future__ import annotations

import streamlit as st


def render_dashboard(resume: dict | None) -> None:
    st.subheader("Resume Dashboard")

    if not resume:
        st.info("No resume loaded yet.")
        return

    metrics = [
        ("Skills", str(len(resume.get("skills", [])))),
        ("Experience", str(len(resume.get("experience", [])))),
        ("Projects", str(len(resume.get("projects", [])))),
        ("Certifications", str(len(resume.get("certifications", [])))),
    ]

    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)

    with st.expander("Resume overview"):
        st.json(resume)
