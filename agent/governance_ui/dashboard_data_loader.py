"""
Dashboard Initial Data Loader.

Per DOC-SIZE-01-v1: Extracted from governance_dashboard.py (679 lines).
Handles REST API loading at dashboard startup with MCP fallback.
"""

import logging
from typing import Any

from agent.governance_ui.utils import (
    format_timestamps_in_list,
    compute_session_metrics,
    compute_session_duration,
    compute_timeline_data,
)

logger = logging.getLogger(__name__)


def load_initial_data(
    state: Any,
    api_base_url: str,
    get_rules,
    get_decisions,
    get_sessions,
    get_tasks,
) -> None:
    """Load initial data from REST API with MCP fallback.

    Populates state with rules, decisions, sessions, agents, and tasks.
    Uses REST API first (includes document_path), falls back to MCP functions.
    """
    import httpx
    page_size = 20

    try:
        with httpx.Client(timeout=10.0) as client:
            _load_rules(state, client, api_base_url, get_rules)
            _load_decisions(state, client, api_base_url, get_decisions)
            _load_sessions(state, client, api_base_url, get_sessions, page_size)
            _load_agents(state, client, api_base_url)
            _load_tasks(state, client, api_base_url, get_tasks, page_size)
            _load_projects(state, client, api_base_url)
    except Exception:
        state.rules = get_rules()
        state.decisions = get_decisions()
        state.sessions = get_sessions(limit=100)
        state.tasks = get_tasks()


def _load_rules(state, client, api_base_url, get_rules) -> None:
    """Load rules from REST API."""
    resp = client.get(f"{api_base_url}/api/rules")
    if resp.status_code == 200:
        data = resp.json()
        state.rules = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.rules = get_rules()


def _load_decisions(state, client, api_base_url, get_decisions) -> None:
    """Load decisions from REST API."""
    resp = client.get(f"{api_base_url}/api/decisions")
    if resp.status_code == 200:
        data = resp.json()
        state.decisions = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.decisions = get_decisions()


def _load_sessions(state, client, api_base_url, get_sessions, page_size) -> None:
    """Load sessions with pagination and compute metrics."""
    resp = client.get(
        f"{api_base_url}/api/sessions",
        params={"limit": page_size, "offset": 0},
    )
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
            state.sessions_pagination = data.get("pagination", {})
        else:
            items = data[:page_size] if len(data) > page_size else data

        metrics = compute_session_metrics(items)
        state.sessions_metrics_duration = metrics["duration"]
        state.sessions_metrics_avg_tasks = metrics["avg_tasks"]

        for item in items:
            item["duration"] = compute_session_duration(
                item.get("start_time", ""), item.get("end_time", ""),
            )
            # BUG-SESSION-END-001: Show meaningful text for missing end_time
            if not item.get("end_time"):
                status = (item.get("status") or "").upper()
                if status in ("COMPLETED", "CLOSED"):
                    item["end_time"] = "(completed)"
                elif status == "ACTIVE":
                    item["end_time"] = "ongoing"
            # Derive source_type for Source column (SESSION-CC-01-v1)
            if not item.get("source_type"):
                sid = item.get("session_id", "")
                if item.get("cc_session_uuid") or "-CC-" in sid:
                    item["source_type"] = "CC"
                elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                    item["source_type"] = "Chat"
                else:
                    item["source_type"] = "API"

        tl_vals, tl_labels = compute_timeline_data(items)
        state.sessions_timeline_data = tl_vals
        state.sessions_timeline_labels = tl_labels

        agents = sorted(set(
            s.get("agent_id") for s in items if s.get("agent_id")
        ))
        state.sessions_agent_options = agents
        state.sessions = format_timestamps_in_list(
            items, ["start_time", "end_time"],
        )
    else:
        state.sessions = get_sessions(limit=100)


def _load_agents(state, client, api_base_url) -> None:
    """Load agents from REST API."""
    resp = client.get(f"{api_base_url}/api/agents")
    if resp.status_code == 200:
        data = resp.json()
        state.agents = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.agents = []


def _load_projects(state, client, api_base_url) -> None:
    """Load projects from REST API (GOV-PROJECT-01-v1)."""
    try:
        resp = client.get(f"{api_base_url}/api/projects", params={"limit": 50})
        if resp.status_code == 200:
            data = resp.json()
            state.projects = data.get("items", data) if isinstance(data, dict) else data
        else:
            state.projects = []
    except Exception:
        state.projects = []


def _load_tasks(state, client, api_base_url, get_tasks, page_size) -> None:
    """Load tasks with pagination."""
    resp = client.get(
        f"{api_base_url}/api/tasks",
        params={"limit": page_size, "offset": 0},
    )
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "items" in data:
            state.tasks = data["items"]
            state.tasks_pagination = data.get("pagination", {})
        else:
            state.tasks = data[:page_size] if len(data) > page_size else data
            state.tasks_pagination = {
                "total": len(data), "offset": 0, "limit": page_size,
                "has_more": len(data) > page_size,
                "returned": min(len(data), page_size),
            }
        # BUG-UI-TASKS-003: Format timestamps on initial load
        state.tasks = format_timestamps_in_list(
            state.tasks, ["created_at", "completed_at", "claimed_at"]
        )
    else:
        state.tasks = get_tasks()
