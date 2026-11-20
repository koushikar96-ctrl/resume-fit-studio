from __future__ import annotations

import streamlit as st


def render_kpi_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)
