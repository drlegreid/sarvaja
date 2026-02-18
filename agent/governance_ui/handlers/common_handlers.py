"""
Common handlers for Governance Dashboard.

Per RULE-012: Single Responsibility - shared/cross-cutting operations.
Per RULE-019: UI/UX Standards - consistent handler patterns.
Per DOC-SIZE-01-v1: Chat handlers in common_handlers_chat.py,
    rule detail/audit handlers in common_handlers_audit.py.
"""

import os
import httpx
from typing import Any
from ..data_access import (
    get_proposals,
    build_trust_leaderboard,
)
from ..trace_bar import clear_traces
from ..trace_bar.transforms import add_error_trace
from ..utils import (
    extract_items_from_response, format_timestamps_in_list,
    compute_session_duration,
)

# Re-export extracted handlers for backward compatibility
from .common_handlers_chat import register_chat_handlers  # noqa: F401
from .common_handlers_audit import register_rule_detail_handlers  # noqa: F401

# Per GAP-UI-EXP-012: Use env var for container compatibility
API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def register_common_handlers(ctrl: Any, state: Any) -> None:
    """Register common/shared handlers with the controller."""

    @ctrl.trigger("refresh_data")
    def refresh_data() -> None:
        """Refresh all data from REST API."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                # Load rules
                try:
                    rules_response = client.get(f"{API_BASE_URL}/api/rules")
                    if rules_response.status_code == 200:
                        data = rules_response.json()
                        state.rules = data.get("items", data) if isinstance(data, dict) else data
                except Exception as e:
                    add_error_trace(state, f"Refresh rules failed: {e}", "/api/rules")

                # Load decisions
                try:
                    decisions_response = client.get(f"{API_BASE_URL}/api/decisions")
                    if decisions_response.status_code == 200:
                        data = decisions_response.json()
                        state.decisions = data.get("items", data) if isinstance(data, dict) else data
                except Exception as e:
                    add_error_trace(state, f"Refresh decisions failed: {e}", "/api/decisions")

                # Load tasks with pagination
                try:
                    page_size = getattr(state, 'tasks_per_page', 20)
                    tasks_response = client.get(f"{API_BASE_URL}/api/tasks", params={"limit": page_size, "offset": 0})
                    if tasks_response.status_code == 200:
                        data = tasks_response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = data["items"]
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            all_items = extract_items_from_response(data)
                            state.tasks = all_items[:page_size]
                            state.tasks_pagination = {
                                "total": len(all_items), "offset": 0,
                                "limit": page_size,
                                "has_more": len(all_items) > page_size,
                                "returned": min(len(all_items), page_size),
                            }
                    state.tasks_page = 1
                except Exception as e:
                    add_error_trace(state, f"Refresh tasks failed: {e}", "/api/tasks")

                # Load sessions (per GAP-EXPLOR-API-001: now returns paginated response)
                try:
                    sessions_response = client.get(f"{API_BASE_URL}/api/sessions?limit=100")
                    if sessions_response.status_code == 200:
                        data = sessions_response.json()
                        items = data.get("items", data) if isinstance(data, dict) else data
                        # F.2: Add duration column
                        for item in items:
                            item["duration"] = compute_session_duration(
                                item.get("start_time", ""), item.get("end_time", ""))
                            # BUG-UI-SESSIONS-003: Derive source_type
                            if not item.get("source_type"):
                                sid = item.get("session_id", "")
                                if item.get("cc_session_uuid") or "-CC-" in sid:
                                    item["source_type"] = "CC"
                                elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                                    item["source_type"] = "Chat"
                                else:
                                    item["source_type"] = "API"
                        state.sessions = format_timestamps_in_list(
                            items, ["start_time", "end_time"])
                except Exception as e:
                    add_error_trace(state, f"Refresh sessions failed: {e}", "/api/sessions")

                # Load agents
                try:
                    agents_response = client.get(f"{API_BASE_URL}/api/agents")
                    if agents_response.status_code == 200:
                        data = agents_response.json()
                        state.agents = data.get("items", data) if isinstance(data, dict) else data
                except Exception as e:
                    add_error_trace(state, f"Refresh agents failed: {e}", "/api/agents")

            state.is_loading = False
            state.status_message = "Data refreshed from API"
        except Exception as e:
            state.is_loading = False
            # BUG-UI-SILENT-FAIL-001: Use error_message not status_message for failures
            state.has_error = True
            state.error_message = f"API unavailable: {type(e).__name__}"  # BUG-476-CHN-1

    @ctrl.set("toggle_graph_view")
    def toggle_graph_view() -> None:
        """Toggle between graph and list view."""
        state.show_graph_view = not state.show_graph_view

    @ctrl.trigger("load_trust_data")
    def load_trust_data() -> None:
        """Load agent trust data from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{API_BASE_URL}/api/agents")
                if response.status_code == 200:
                    data = response.json()
                    state.agents = data.get("items", data) if isinstance(data, dict) else data
                else:
                    state.agents = []
        except Exception as e:
            add_error_trace(state, f"Load trust agents failed: {e}", "/api/agents")
            state.agents = []

        state.trust_leaderboard = build_trust_leaderboard(state.agents)

        try:
            state.proposals = get_proposals()
        except Exception as e:
            add_error_trace(state, f"Load proposals failed: {e}", "get_proposals()")
            state.proposals = []

        state.escalated_proposals = []


def register_view_handlers(ctrl: Any, state: Any, load_view_data_fn: Any) -> None:
    """Register view change handlers with the controller."""

    @state.change("active_view")
    def on_view_change(active_view: str, **kwargs) -> None:
        """Handle view navigation changes - load data when view becomes active."""
        load_view_data_fn(active_view)


def register_backlog_handlers(ctrl: Any, state: Any) -> None:
    """Register backlog-related handlers."""

    @ctrl.trigger("load_backlog_data")
    def load_backlog_data() -> None:
        """Load backlog tasks from REST API."""
        try:
            state.backlog_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{API_BASE_URL}/api/tasks/backlog",
                    params={"status": "TODO,pending"}
                )
                if response.status_code == 200:
                    state.backlog_tasks = response.json()
                else:
                    state.backlog_tasks = []
            state.backlog_loading = False
        except Exception as e:
            state.backlog_loading = False
            state.backlog_error = f"Failed to load backlog: {type(e).__name__}"  # BUG-476-CHN-2

    @ctrl.trigger("refresh_backlog")
    def refresh_backlog() -> None:
        """Refresh backlog data."""
        load_backlog_data()

    @ctrl.trigger("claim_backlog_task")
    def claim_backlog_task(task_id: str) -> None:
        """Claim a backlog task for the current agent."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/api/tasks/{task_id}/claim",
                    json={"agent_id": state.current_agent_id or "claude-code"}
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} claimed"
                    load_backlog_data()  # Refresh
                else:
                    state.error_message = f"Failed to claim task: {response.status_code}"
        except Exception as e:
            state.error_message = f"Failed to claim task: {type(e).__name__}"  # BUG-476-CHN-3

    @ctrl.trigger("complete_backlog_task")
    def complete_backlog_task(task_id: str) -> None:
        """Mark a backlog task as complete."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{API_BASE_URL}/api/tasks/{task_id}",
                    json={"status": "DONE"}
                )
                if response.status_code == 200:
                    state.status_message = f"Task {task_id} completed"
                    load_backlog_data()  # Refresh
                else:
                    state.error_message = f"Failed to complete task: {response.status_code}"
        except Exception as e:
            state.error_message = f"Failed to complete task: {type(e).__name__}"  # BUG-476-CHN-4


def register_executive_handlers(ctrl: Any, state: Any) -> None:
    """Register executive report handlers."""

    @ctrl.trigger("load_executive_report_data")
    def load_executive_report_data() -> None:
        """Load executive report from REST API."""
        try:
            state.executive_loading = True
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{API_BASE_URL}/api/executive/report",
                    params={"period": state.executive_period or "week"}
                )
                if response.status_code == 200:
                    state.executive_report = response.json()
                else:
                    state.executive_report = {}
            state.executive_loading = False
        except Exception as e:
            state.executive_loading = False
            state.executive_error = f"Failed to load report: {type(e).__name__}"  # BUG-476-CHN-5

    @ctrl.trigger("trigger_load_executive_report")
    def trigger_load_executive_report() -> None:
        """Trigger executive report generation."""
        load_executive_report_data()


def register_trace_bar_handlers(ctrl: Any, state: Any) -> None:
    """Register trace bar handlers (GAP-UI-048)."""

    @ctrl.trigger("clear_traces")
    def handle_clear_traces() -> None:
        """Clear all trace events."""
        clear_traces(state)
