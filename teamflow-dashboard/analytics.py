from __future__ import annotations

from typing import Dict

import pandas as pd

from task_manager import with_derived_metrics


def compute_health(df: pd.DataFrame) -> Dict[str, int]:
    df = with_derived_metrics(df)
    total = len(df)
    blocked = int(df["is_blocked"].sum()) if total else 0
    at_risk = int(df["at_risk"].sum()) if total else 0
    long_running = int(df["is_long_running"].sum()) if total else 0

    by_status = df["status"].value_counts().to_dict() if total else {}
    by_owner = df["owner"].value_counts().to_dict() if total else {}

    return {
        "total": total,
        "blocked": blocked,
        "at_risk": at_risk,
        "long_running": long_running,
        "by_status": by_status,
        "by_owner": by_owner,
    }


def daily_summary(df: pd.DataFrame) -> str:
    df = with_derived_metrics(df)
    total = len(df)
    blocked = int(df["is_blocked"].sum()) if total else 0
    at_risk = int(df["at_risk"].sum()) if total else 0

    completed_today = 0
    if total:
        completed_today = int(
            ((df["status"] == "Completed") & (df["inactivity_days"] == 0)).sum()
        )

    return (
        f"Total tasks: {total}\n"
        f"Blocked: {blocked}, At-Risk: {at_risk}\n"
        f"Completed today: {completed_today}\n"
        f"Owners active: {len(df['owner'].unique()) if total else 0}"
    )