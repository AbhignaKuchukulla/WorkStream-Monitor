from __future__ import annotations

import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
import streamlit as st

# Constants
VALID_STATUSES = ["Planned", "In Progress", "Blocked", "Completed"]
DEFAULT_INACTIVITY_THRESHOLD_DAYS = 3
DEFAULT_DATA_PATH = Path("data/tasks.csv")


# ---- Session State Helpers ----

def _init_session_state() -> None:
    """Ensure core data structures exist in Streamlit session_state."""
    if "tasks_df" not in st.session_state:
        st.session_state["tasks_df"] = pd.DataFrame(
            columns=[
                "task_id",
                "title",
                "description",
                "owner",
                "status",
                "created_at",
                "last_updated_at",
            ]
        )
    if "inactivity_threshold_days" not in st.session_state:
        st.session_state["inactivity_threshold_days"] = DEFAULT_INACTIVITY_THRESHOLD_DAYS


def get_tasks_df() -> pd.DataFrame:
    _init_session_state()
    # Return a copy to avoid accidental mutation without explicit update
    return st.session_state["tasks_df"].copy()


def _set_tasks_df(df: pd.DataFrame) -> None:
    st.session_state["tasks_df"] = df


# ---- Validation ----

def validate_task_fields(title: str, owner: str, status: str, description: str = "") -> List[str]:
    errors: List[str] = []
    if not title or not title.strip():
        errors.append("Title is required.")
    if not owner or not owner.strip():
        errors.append("Owner is required.")
    if status not in VALID_STATUSES:
        errors.append(f"Status must be one of: {', '.join(VALID_STATUSES)}")
    if description is None:
        errors.append("Description cannot be None.")
    return errors


# ---- CRUD ----

def create_task(title: str, description: str, owner: str, status: str) -> Optional[Dict[str, str]]:
    """Create a task after validation and store it in session_state DataFrame."""
    _init_session_state()
    errors = validate_task_fields(title, owner, status, description)
    if errors:
        st.error("\n".join(errors))
        return None

    now = datetime.utcnow().isoformat()
    task = {
        "task_id": str(uuid.uuid4()),
        "title": title.strip(),
        "description": description.strip(),
        "owner": owner.strip(),
        "status": status,
        "created_at": now,
        "last_updated_at": now,
    }

    df = get_tasks_df()
    df = pd.concat([df, pd.DataFrame([task])], ignore_index=True)
    _set_tasks_df(df)
    return task


def update_task(
    task_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
) -> bool:
    """Update an existing task with defensive checks and timestamp updates."""
    _init_session_state()
    df = get_tasks_df()
    if df.empty:
        st.warning("No tasks available to update.")
        return False

    idx = df.index[df["task_id"] == task_id]
    if len(idx) == 0:
        st.error("Task not found.")
        return False
    i = idx[0]

    if title is not None:
        if not title.strip():
            st.error("Title cannot be empty.")
            return False
        df.at[i, "title"] = title.strip()
    if description is not None:
        df.at[i, "description"] = (description or "").strip()
    if owner is not None:
        if not owner.strip():
            st.error("Owner cannot be empty.")
            return False
        df.at[i, "owner"] = owner.strip()
    if status is not None:
        if status not in VALID_STATUSES:
            st.error(f"Status must be one of: {', '.join(VALID_STATUSES)}")
            return False
        df.at[i, "status"] = status

    df.at[i, "last_updated_at"] = datetime.utcnow().isoformat()
    _set_tasks_df(df)
    return True


# ---- Utility Metrics ----

def compute_task_age_days(created_at_iso: str) -> int:
    created = datetime.fromisoformat(created_at_iso)
    return (datetime.utcnow() - created).days


def compute_inactivity_days(last_updated_iso: str) -> int:
    updated = datetime.fromisoformat(last_updated_iso)
    return (datetime.utcnow() - updated).days


def get_inactivity_threshold_days() -> int:
    _init_session_state()
    return int(st.session_state["inactivity_threshold_days"]) or DEFAULT_INACTIVITY_THRESHOLD_DAYS


def set_inactivity_threshold_days(days: int) -> None:
    if days <= 0:
        st.error("Inactivity threshold must be a positive integer.")
        return
    st.session_state["inactivity_threshold_days"] = int(days)


# ---- Derived Views ----

def with_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    df = df.copy()
    df["age_days"] = df["created_at"].apply(compute_task_age_days)
    df["inactivity_days"] = df["last_updated_at"].apply(compute_inactivity_days)
    threshold = get_inactivity_threshold_days()
    df["at_risk"] = df["inactivity_days"] >= threshold
    df["is_blocked"] = df["status"] == "Blocked"
    df["is_long_running"] = (df["status"] != "Completed") & (df["age_days"] >= threshold * 2)
    return df


def reset_all_tasks() -> None:
    """Clear tasks. Useful for demos or resets."""
    _set_tasks_df(
        pd.DataFrame(
            columns=[
                "task_id",
                "title",
                "description",
                "owner",
                "status",
                "created_at",
                "last_updated_at",
            ]
        )
    )


# ---- Persistence (CSV) ----

def save_tasks_to_csv(path: str | Path = DEFAULT_DATA_PATH) -> bool:
    """Persist tasks to CSV. Returns True on success."""
    df = get_tasks_df()
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return True
    except Exception as exc:  # pragma: no cover - Streamlit surface
        st.error(f"Failed to save tasks to CSV: {exc}")
        return False


def load_tasks_from_csv(path: str | Path = DEFAULT_DATA_PATH) -> bool:
    """Load tasks from CSV into session_state. Returns True on success."""
    try:
        path = Path(path)
        if not path.exists():
            st.warning("CSV file not found.")
            return False
        df = pd.read_csv(path)
        # Ensure required columns exist; fill missing ones
        required_cols = [
            "task_id",
            "title",
            "description",
            "owner",
            "status",
            "created_at",
            "last_updated_at",
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[required_cols]
        _set_tasks_df(df)
        return True
    except Exception as exc:  # pragma: no cover - Streamlit surface
        st.error(f"Failed to load tasks from CSV: {exc}")
        return False


# ---- Demo Data ----

def seed_demo_tasks() -> None:
    """Load a small deterministic demo set into session_state."""
    now = datetime.utcnow().isoformat()
    demo = [
        {
            "task_id": str(uuid.uuid4()),
            "title": "Implement auth stub",
            "description": "Placeholder for future auth integration",
            "owner": "Alice",
            "status": "Planned",
            "created_at": now,
            "last_updated_at": now,
        },
        {
            "task_id": str(uuid.uuid4()),
            "title": "Refactor data layer",
            "description": "Separate persistence adapter",
            "owner": "Bob",
            "status": "In Progress",
            "created_at": now,
            "last_updated_at": now,
        },
        {
            "task_id": str(uuid.uuid4()),
            "title": "Fix flaky tests",
            "description": "Stabilize CI failures",
            "owner": "Carol",
            "status": "Blocked",
            "created_at": now,
            "last_updated_at": now,
        },
        {
            "task_id": str(uuid.uuid4()),
            "title": "Improve dashboards",
            "description": "Add filters and summaries",
            "owner": "Dana",
            "status": "In Progress",
            "created_at": now,
            "last_updated_at": now,
        },
        {
            "task_id": str(uuid.uuid4()),
            "title": "Ship v1",
            "description": "Cut scope and release",
            "owner": "Eve",
            "status": "Completed",
            "created_at": now,
            "last_updated_at": now,
        },
    ]
    df = pd.DataFrame(demo)
    _set_tasks_df(df)
