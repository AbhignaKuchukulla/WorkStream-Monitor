# WorkStream Monitor

Smart Operational Coordination & Execution Visibility System

## Overview
WorkStream Monitor is a lightweight internal engineering tool that provides clear execution visibility, explicit ownership, and early risk detection for small teams working across multiple parallel tasks. It is designed to support daily stand-ups, weekly planning, and execution health reviews without the heavy process overhead of traditional project management platforms.

## Features
- Task management with validation: title, owner, status, description
- Auto-generated `task_id` and reliable timestamps (`created_at`, `last_updated_at`)
- Quick inline task updates for status, owner, title, description
- Execution health metrics: task age, inactivity, blocked, long-running, at-risk
- Real-time visibility: status distribution, ownership workload, risk badges
- Daily summary for stand-ups with core counts
- Optional CSV save/load for tasks (sidebar controls)
- Downloadable daily summary (text + Markdown)
- Clean separation of data logic (Pandas + session_state) and UI (Streamlit)

## Design Philosophy
- Simple, transparent, execution-focused, and engineer-friendly
- Real-time visibility over process complexity
- Modular, reusable functions with minimal UI-to-logic coupling
- Built for clarity and easy extension (persistence, auth, APIs later)

## Tech Stack
- Python 3
- Streamlit
- Pandas
- Altair (charts)

## Project Structure
```
teamflow-dashboard/
├── app.py                # Main Streamlit application
├── task_manager.py       # Task CRUD & validation logic
├── analytics.py          # Execution health & summaries
├── ui_components.py      # Charts and UI helpers
├── requirements.txt
└── README.md
```

## How to Run Locally (Windows PowerShell)
1. Navigate to the project folder:
```powershell
cd "c:\Users\HP\OneDrive\Desktop\Projects\workstream monitor\teamflow-dashboard"
```
2. (Optional) Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Install dependencies:
```powershell
pip install -r requirements.txt
```
4. Run the Streamlit app:
```powershell
streamlit run app.py
```

## Operational Usage
- Use the Task Creation form to add tasks with clear ownership and status.
- Use the Quick Update panel to adjust task status, owner, title, or description.
- Review the Execution Health dashboard for risk indicators (Blocked, At-Risk, Long-Running) and workload distribution.
- Read the Daily Summary section during stand-ups.
## Notes
- Data is stored in Streamlit `session_state` for the initial version.
- Code is organized with modular functions for easy extension.
