from __future__ import annotations

import streamlit as st
import pandas as pd

from task_manager import (
    VALID_STATUSES,
    DEFAULT_DATA_PATH,
    get_tasks_df,
    with_derived_metrics,
    create_task,
    update_task,
    set_inactivity_threshold_days,
    get_inactivity_threshold_days,
    reset_all_tasks,
    save_tasks_to_csv,
    load_tasks_from_csv,
    seed_demo_tasks,
)
from analytics import compute_health, daily_summary
from ui_components import status_distribution_chart, ownership_workload_chart, risk_badges

st.set_page_config(page_title="WorkStream Monitor", layout="wide")


def render_header():
    st.title("WorkStream Monitor")
    st.caption("Smart Operational Coordination & Execution Visibility")

    with st.sidebar:
        st.subheader("Settings")
        threshold = st.number_input(
            "At-risk inactivity threshold (days)",
            min_value=1,
            value=get_inactivity_threshold_days(),
            step=1,
        )
        set_inactivity_threshold_days(int(threshold))
        st.button("Reset all tasks", on_click=reset_all_tasks, help="Clear all tasks")

        st.markdown("---")
        st.subheader("Persistence (CSV)")
        csv_path = st.text_input("CSV path", value=str(DEFAULT_DATA_PATH))
        col_a, col_b = st.columns(2)
        if col_a.button("Save to CSV"):
            if save_tasks_to_csv(csv_path):
                st.success("Tasks saved to CSV.")
        if col_b.button("Load from CSV"):
            if load_tasks_from_csv(csv_path):
                st.success("Tasks loaded from CSV.")

        st.markdown("---")
        st.subheader("Demo Data")
        if st.button("Seed demo tasks"):
            seed_demo_tasks()
            st.success("Demo tasks loaded.")


def render_task_creation_form():
    st.subheader("Create Task")
    with st.form("task_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description")
        owner = st.text_input("Owner")
        status = st.selectbox("Status", VALID_STATUSES, index=0)
        submitted = st.form_submit_button("Add Task")
        if submitted:
            task = create_task(title=title, description=description, owner=owner, status=status)
            if task:
                st.success("Task created.")


def render_task_table():
    st.subheader("Tasks")
    base_df = with_derived_metrics(get_tasks_df())
    if base_df.empty:
        st.info("No tasks yet. Add some using the form above.")
        return

    with st.expander("Filters", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        status_filter = col_f1.multiselect("Status", VALID_STATUSES)
        owners = sorted(base_df["owner"].unique())
        owner_filter = col_f2.multiselect("Owner", owners)
        text_filter = col_f3.text_input("Search (title/description)")
        col_f4, col_f5 = st.columns(2)
        show_blocked = col_f4.checkbox("Only blocked", value=False)
        show_at_risk = col_f5.checkbox("Only at-risk", value=False)

    df = base_df.copy()
    if status_filter:
        df = df[df["status"].isin(status_filter)]
    if owner_filter:
        df = df[df["owner"].isin(owner_filter)]
    if text_filter:
        mask = df["title"].str.contains(text_filter, case=False, na=False) | df["description"].str.contains(text_filter, case=False, na=False)
        df = df[mask]
    if show_blocked:
        df = df[df["is_blocked"]]
    if show_at_risk:
        df = df[df["at_risk"]]

    if df.empty:
        st.info("No tasks match the filters.")
        return

    # Inline quick edits
    with st.expander("Quick Update", expanded=True):
        selected_task_id = st.selectbox("Select task", options=df["task_id"].tolist(), format_func=lambda tid: f"{df.loc[df['task_id']==tid, 'title'].values[0]} ({tid[:8]})")
        col1, col2, col3, col4 = st.columns(4)
        new_status = col1.selectbox("Status", VALID_STATUSES, index=VALID_STATUSES.index(df.loc[df['task_id']==selected_task_id, 'status'].values[0]))
        new_owner = col2.text_input("Owner", value=df.loc[df['task_id']==selected_task_id, 'owner'].values[0])
        new_title = col3.text_input("Title", value=df.loc[df['task_id']==selected_task_id, 'title'].values[0])
        new_desc = col4.text_area("Description", value=df.loc[df['task_id']==selected_task_id, 'description'].values[0])
        if st.button("Apply Update"):
            ok = update_task(
                selected_task_id,
                title=new_title,
                description=new_desc,
                owner=new_owner,
                status=new_status,
            )
            if ok:
                st.success("Task updated.")

    # Highlighting
    def row_style(row):
        if row.get("is_blocked"):
            return "background-color: #ffe3e3"
        if row.get("at_risk"):
            return "background-color: #fff4e6"
        return ""

    styled = df.style.apply(lambda r: [row_style(r) for _ in r], axis=1)
    st.dataframe(df, use_container_width=True)


def render_health_dashboard():
    st.subheader("Execution Health Dashboard")
    df = with_derived_metrics(get_tasks_df())
    health = compute_health(df)

    risk_badges(df)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Status Distribution**")
        chart = status_distribution_chart(df)
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No data to show.")

    with col_right:
        st.markdown("**Ownership Workload**")
        chart = ownership_workload_chart(df)
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No data to show.")

    st.markdown("**Numbers**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", health.get("total", 0))
    col2.metric("Blocked", health.get("blocked", 0))
    col3.metric("At-Risk", health.get("at_risk", 0))
    col4.metric("Long-Running", health.get("long_running", 0))


def render_daily_summary():
    st.subheader("Daily Summary")
    df = get_tasks_df()
    summary_text = daily_summary(df)
    st.text(summary_text)
    st.download_button(
        label="Download summary (txt)",
        data=summary_text,
        file_name="daily_summary.txt",
        mime="text/plain",
    )
    md_summary = summary_text.replace("\n", "\n\n")
    st.download_button(
        label="Download summary (md)",
        data=md_summary,
        file_name="daily_summary.md",
        mime="text/markdown",
    )


# ---- Main Layout ----
render_header()

colA, colB = st.columns([1, 1])
with colA:
    render_task_creation_form()
with colB:
    render_daily_summary()

st.divider()
render_task_table()

st.divider()
render_health_dashboard()
