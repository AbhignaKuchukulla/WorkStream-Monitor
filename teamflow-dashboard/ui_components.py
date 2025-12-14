from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st


def status_distribution_chart(df: pd.DataFrame) -> Optional[alt.Chart]:
    if df.empty:
        return None
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("status", title="Status"),
            y=alt.Y("count", title="Count"),
            color=alt.Color("status", legend=None),
            tooltip=["status", "count"],
        )
        .properties(height=250)
    )
    return chart


def ownership_workload_chart(df: pd.DataFrame) -> Optional[alt.Chart]:
    if df.empty:
        return None
    counts = df["owner"].value_counts().reset_index()
    counts.columns = ["owner", "count"]
    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("owner", title="Owner"),
            y=alt.Y("count", title="Tasks"),
            color=alt.Color("owner", legend=None),
            tooltip=["owner", "count"],
        )
        .properties(height=250)
    )
    return chart


def risk_badges(df: pd.DataFrame) -> None:
    total = len(df)
    blocked = int((df["status"] == "Blocked").sum()) if total else 0
    at_risk = int((df.get("at_risk", pd.Series(False))).sum()) if total else 0
    long_running = int((df.get("is_long_running", pd.Series(False))).sum()) if total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Blocked", blocked)
    col2.metric("At-Risk", at_risk)
    col3.metric("Long-Running", long_running)