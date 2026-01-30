"""
Common handlers for Governance Dashboard.

Per RULE-012: Single Responsibility - shared/cross-cutting operations.
Per RULE-019: UI/UX Standards - consistent handler patterns.
"""

import os
import httpx
from typing import Any
from ..data_access import (
    get_proposals,
    build_trust_leaderboard,
)
from ..trace_bar import clear_traces
from ..utils import extract_items_from_response

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
                except Exception:
                    pass

                # Load decisions
                try:
                    decisions_response = client.get(f"{API_BASE_URL}/api/decisions")
                    if decisions_response.status_code == 200:
                        state.decisions = decisions_response.json()
                except Exception:
                    pass

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
                except Exception:
                    pass

                # Load sessions (per GAP-EXPLOR-API-001: now returns paginated response)
                try:
                    sessions_response = client.get(f"{API_BASE_URL}/api/sessions?limit=100")
                    if sessions_response.status_code == 200:
                        data = sessions_response.json()
                        state.sessions = data.get("items", data) if isinstance(data, dict) else data
                except Exception:
                    pass

                # Load agents
                try:
                    agents_response = client.get(f"{API_BASE_URL}/api/agents")
                    if agents_response.status_code == 200:
                        data = agents_response.json()
                        state.agents = data.get("items", data) if isinstance(data, dict) else data
                except Exception:
                    pass

            state.is_loading = False
            state.status_message = "Data refreshed from API"
        except Exception as e:
            state.is_loading = False
            state.status_message = f"Using cached data (API unavailable: {str(e)})"

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
            print(f"Error loading agents: {e}")
            state.agents = []

        state.trust_leaderboard = build_trust_leaderboard(state.agents)

        try:
            state.proposals = get_proposals()
        except Exception:
            state.proposals = []

        try:
            state.escalated_proposals = []
        except Exception:
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
            state.backlog_error = f"Failed to load backlog: {str(e)}"

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
            state.error_message = f"Failed to claim task: {str(e)}"

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
            state.error_message = f"Failed to complete task: {str(e)}"


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
            state.executive_error = f"Failed to load report: {str(e)}"

    @ctrl.trigger("trigger_load_executive_report")
    def trigger_load_executive_report() -> None:
        """Trigger executive report generation."""
        load_executive_report_data()


def register_chat_handlers(ctrl: Any, state: Any) -> None:
    """Register chat/agent interaction handlers."""

    @ctrl.trigger("send_chat_message")
    def send_chat_message() -> None:
        """Send a chat message to the selected agent."""
        if not state.chat_input or not state.chat_input.strip():
            return

        message = state.chat_input.strip()
        state.chat_input = ""

        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        state.chat_messages = state.chat_messages + [user_msg]

        # Process command or send to agent
        if message.startswith("/"):
            _process_chat_command(state, message)
        else:
            _send_to_agent(state, message)

    @ctrl.trigger("clear_chat")
    def clear_chat() -> None:
        """Clear chat history."""
        state.chat_messages = []


def _process_chat_command(state: Any, command: str) -> None:
    """Process a slash command."""
    cmd = command.lower().split()[0]
    responses = {
        "/help": "Available commands: /help, /status, /tasks, /rules, /agents",
        "/status": f"System status: {len(state.rules)} rules, {len(state.tasks)} tasks, {len(state.agents)} agents",
        "/tasks": f"Tasks: {len([t for t in state.tasks if t.get('status') == 'TODO'])} pending",
        "/rules": f"Rules: {len([r for r in state.rules if r.get('status') == 'ACTIVE'])} active",
        "/agents": f"Agents: {len(state.agents)} registered",
    }

    response = responses.get(cmd, f"Unknown command: {cmd}")
    bot_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    state.chat_messages = state.chat_messages + [bot_msg]


def _send_to_agent(state: Any, message: str) -> None:
    """Send message to selected agent via API."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE_URL}/api/agents/{state.selected_chat_agent or 'claude-code'}/chat",
                json={"message": message}
            )
            if response.status_code == 200:
                result = response.json()
                bot_msg = {
                    "role": "assistant",
                    "content": result.get("response", "No response"),
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                }
            else:
                bot_msg = {
                    "role": "assistant",
                    "content": f"Error: {response.status_code}",
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                }
    except Exception as e:
        bot_msg = {
            "role": "assistant",
            "content": f"Connection error: {str(e)}",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }

    state.chat_messages = state.chat_messages + [bot_msg]


def register_trace_bar_handlers(ctrl: Any, state: Any) -> None:
    """Register trace bar handlers (GAP-UI-048)."""

    @ctrl.trigger("clear_traces")
    def handle_clear_traces() -> None:
        """Clear all trace events."""
        clear_traces(state)


def register_rule_detail_handlers(ctrl: Any, state: Any) -> None:
    """Register rule detail handlers (UI-AUDIT-003)."""

    @ctrl.trigger("load_rule_implementing_tasks")
    def load_rule_implementing_tasks() -> None:
        """
        Load tasks that implement the selected rule.

        Per UI-AUDIT-003: Rule↔task traceability for dashboard.
        Per GAP-UI-AUDIT-001: Rules view should show implementing tasks.
        """
        if not state.selected_rule:
            state.rule_implementing_tasks = []
            return

        rule_id = state.selected_rule.get("id") or state.selected_rule.get("rule_id")
        if not rule_id:
            state.rule_implementing_tasks = []
            return

        try:
            state.rule_implementing_tasks_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{API_BASE_URL}/api/rules/{rule_id}/tasks")
                if response.status_code == 200:
                    data = response.json()
                    state.rule_implementing_tasks = data.get("implementing_tasks", [])
                else:
                    state.rule_implementing_tasks = []
            state.rule_implementing_tasks_loading = False
        except Exception as e:
            print(f"Error loading implementing tasks for rule {rule_id}: {e}")
            state.rule_implementing_tasks = []
            state.rule_implementing_tasks_loading = False

    # Auto-load implementing tasks when rule detail is shown
    @state.change("show_rule_detail")
    def on_show_rule_detail_change(show_rule_detail: bool, **kwargs) -> None:
        """Load implementing tasks when rule detail view is opened."""
        if show_rule_detail and state.selected_rule:
            load_rule_implementing_tasks()

    # Also trigger when selected_rule changes (handles state sync timing)
    @state.change("selected_rule")
    def on_selected_rule_change(selected_rule, **kwargs) -> None:
        """Load implementing tasks when a rule is selected."""
        if state.show_rule_detail and selected_rule:
            load_rule_implementing_tasks()

    # =========================================================================
    # AUDIT FILTER REACTIVE HANDLERS (UI-AUDIT-004)
    # Per GAP-UI-AUDIT-2026-01-18: Make audit trail filterable by entity
    # =========================================================================

    @state.change("audit_filter_entity_type")
    def on_audit_filter_entity_type_change(audit_filter_entity_type, **kwargs):
        """Reload audit trail when entity type filter changes."""
        if state.active_view == "audit":
            ctrl.trigger("load_audit_trail")

    @state.change("audit_filter_action_type")
    def on_audit_filter_action_type_change(audit_filter_action_type, **kwargs):
        """Reload audit trail when action type filter changes."""
        if state.active_view == "audit":
            ctrl.trigger("load_audit_trail")

    @state.change("audit_filter_entity_id")
    def on_audit_filter_entity_id_change(audit_filter_entity_id, **kwargs):
        """Reload audit trail when entity ID filter changes."""
        if state.active_view == "audit":
            ctrl.trigger("load_audit_trail")

    @state.change("audit_filter_correlation_id")
    def on_audit_filter_correlation_id_change(audit_filter_correlation_id, **kwargs):
        """Reload audit trail when correlation ID filter changes."""
        if state.active_view == "audit":
            ctrl.trigger("load_audit_trail")
