"""
Data Loader Controllers (GAP-FILE-005)
======================================
Controller functions for loading/refreshing data.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-048: Trace bar event capture
Per DOC-SIZE-01-v1: Infra/workflow/audit extracted to separate modules

Created: 2024-12-28
Updated: 2026-02-01 (split per DOC-SIZE-01-v1)
"""

import time
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)
from agent.governance_ui.utils import format_timestamps_in_list
from agent.governance_ui import (
    get_proposals,
    get_escalated_proposals,
    build_trust_leaderboard,
    get_governance_stats,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
)
from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
from agent.governance_ui.controllers.workflow_loaders import register_workflow_loader_controllers
from agent.governance_ui.controllers.audit_loaders import register_audit_loader_controllers


def register_data_loader_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register data loading controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls

    Returns:
        Dict of loader functions for internal use by view change handler
    """

    # Register extracted domain controllers
    infra_loaders = register_infra_loader_controllers(state, ctrl, api_base_url)
    workflow_loaders = register_workflow_loader_controllers(state, ctrl, api_base_url)
    audit_loaders = register_audit_loader_controllers(state, ctrl, api_base_url)

    def load_trust_data():
        """Load agent trust data from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                start = time.time()
                response = client.get(f"{api_base_url}/api/agents")
                duration_ms = int((time.time() - start) * 1000)

                response_body = None
                try:
                    response_body = response.json()
                except Exception:
                    pass

                add_api_trace(
                    state, "/api/agents", "GET", response.status_code, duration_ms,
                    response_body=response_body
                )
                if response.status_code == 200:
                    data = response_body or []
                    state.agents = data.get("items", data) if isinstance(data, dict) else data
                else:
                    state.agents = []
        except Exception as e:
            add_error_trace(state, f"Load agents failed: {str(e)}", "/api/agents")
            state.agents = []

        state.trust_leaderboard = build_trust_leaderboard(state.agents)

        try:
            state.proposals = get_proposals()
        except Exception:
            state.proposals = []

        try:
            state.escalated_proposals = get_escalated_proposals()
        except Exception:
            state.escalated_proposals = []

        state.governance_stats = get_governance_stats(
            state.agents,
            state.proposals
        )

    def load_monitor_data():
        """Load monitoring data from RuleMonitor."""
        state.monitor_feed = get_monitor_feed(limit=50)
        state.monitor_alerts = get_monitor_alerts(acknowledged=False)
        state.monitor_stats = get_monitor_stats()
        state.top_rules = get_top_monitored_rules(limit=10)
        state.hourly_stats = get_hourly_monitor_stats()

    def load_backlog_data():
        """Load available tasks and agent's claimed tasks from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/available")
                if response.status_code == 200:
                    state.available_tasks = response.json()
                else:
                    state.available_tasks = []

                if state.backlog_agent_id:
                    response = client.get(
                        f"{api_base_url}/api/tasks",
                        params={"agent_id": state.backlog_agent_id}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        all_tasks = data["items"] if isinstance(data, dict) and "items" in data else data
                        state.claimed_tasks = [
                            t for t in all_tasks
                            if t.get("agent_id") == state.backlog_agent_id
                            and t.get("status") == "IN_PROGRESS"
                        ]
                    else:
                        state.claimed_tasks = []
                else:
                    state.claimed_tasks = []
        except Exception:
            state.available_tasks = []
            state.claimed_tasks = []

    def load_executive_report_data():
        """Load executive report from REST API."""
        try:
            state.executive_loading = True
            with httpx.Client(timeout=15.0) as client:
                params = {}
                if hasattr(state, 'executive_session_id') and state.executive_session_id:
                    params["session_id"] = state.executive_session_id
                else:
                    params["period"] = state.executive_period or "week"
                response = client.get(f"{api_base_url}/api/reports/executive", params=params)
                if response.status_code == 200:
                    state.executive_report = response.json()
                else:
                    state.executive_report = {
                        "error": f"Failed to load report: {response.status_code}",
                        "sections": [],
                        "overall_status": "error",
                        "metrics_summary": {},
                    }
        except Exception as e:
            state.executive_report = {
                "error": str(e),
                "sections": [],
                "overall_status": "error",
                "metrics_summary": {},
            }
        finally:
            state.executive_loading = False

    def _traced_get(client: httpx.Client, endpoint: str) -> tuple:
        """Make a traced GET request. Returns (response, duration_ms)."""
        start = time.time()
        try:
            response = client.get(f"{api_base_url}{endpoint}")
            duration_ms = int((time.time() - start) * 1000)

            response_body = None
            try:
                response_body = response.json()
            except Exception:
                text = response.text[:500] if response.text else None
                if text:
                    response_body = {"_raw_text": text}

            add_api_trace(
                state, endpoint, "GET", response.status_code, duration_ms,
                request_body=None,
                response_body=response_body
            )
            return response, duration_ms
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            add_error_trace(state, f"GET {endpoint} failed: {str(e)}", endpoint)
            raise

    @ctrl.trigger("refresh_data")
    def refresh_data():
        """Refresh all data from REST API."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                try:
                    response, _ = _traced_get(client, "/api/rules")
                    if response.status_code == 200:
                        data = response.json()
                        rules = data.get("items", data) if isinstance(data, dict) else data
                        for r in rules:
                            r.setdefault("linked_tasks_count", r.get("linked_tasks_count", 0))
                            r.setdefault("linked_sessions_count", r.get("linked_sessions_count", 0))
                        state.rules = rules
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/decisions")
                    if response.status_code == 200:
                        data = response.json()
                        state.decisions = data.get("items", data) if isinstance(data, dict) else data
                except Exception:
                    pass

                try:
                    page_size = getattr(state, 'tasks_per_page', 20)
                    response, _ = _traced_get(client, f"/api/tasks?limit={page_size}&offset=0")
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "items" in data:
                            state.tasks = format_timestamps_in_list(
                                data["items"], ["created_at", "claimed_at", "completed_at"])
                            state.tasks_pagination = data.get("pagination", {})
                        else:
                            state.tasks = data[:page_size] if len(data) > page_size else data
                            state.tasks_pagination = {
                                "total": len(data),
                                "offset": 0,
                                "limit": page_size,
                                "has_more": len(data) > page_size,
                                "returned": min(len(data), page_size),
                            }
                    state.tasks_page = 1
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/sessions?limit=100")
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", data) if isinstance(data, dict) else data
                        state.sessions = format_timestamps_in_list(
                            items, ["start_time", "end_time"])
                except Exception:
                    pass

                try:
                    response, _ = _traced_get(client, "/api/agents")
                    if response.status_code == 200:
                        data = response.json()
                        state.agents = data.get("items", data) if isinstance(data, dict) else data
                except Exception:
                    pass

            # Also refresh infra health for toolbar indicator
            try:
                infra_loaders['load_infra_status']()
            except Exception:
                pass

            state.is_loading = False
            state.status_message = "Data refreshed from API"
        except Exception as e:
            state.is_loading = False
            state.status_message = f"Using cached data (API unavailable: {str(e)})"

    @ctrl.trigger("load_trust_data")
    def trigger_load_trust_data():
        """Trigger for loading trust data."""
        load_trust_data()

    @ctrl.trigger("load_monitor_data")
    def trigger_load_monitor_data():
        """Trigger for loading monitor data."""
        load_monitor_data()

    @ctrl.trigger("refresh_backlog")
    def refresh_backlog():
        """Refresh backlog data."""
        load_backlog_data()

    @ctrl.trigger("load_executive_report")
    def trigger_load_executive_report():
        """Trigger to load executive report."""
        load_executive_report_data()

    def load_sessions_list():
        """Load sessions list for dropdowns. Per UI-AUDIT-007."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions?limit=100")
                if response.status_code == 200:
                    data = response.json()
                    state.sessions = data.get("items", data) if isinstance(data, dict) else data
        except Exception:
            if not state.sessions:
                state.sessions = []

    @ctrl.trigger("load_sessions_list")
    def trigger_load_sessions_list():
        """Trigger for loading sessions list."""
        load_sessions_list()

    # Return all loaders (including from extracted modules)
    return {
        'load_trust_data': load_trust_data,
        'load_monitor_data': load_monitor_data,
        'load_backlog_data': load_backlog_data,
        'load_executive_report_data': load_executive_report_data,
        'load_infra_status': infra_loaders['load_infra_status'],
        'load_workflow_status': workflow_loaders['load_workflow_status'],
        'load_audit_trail': audit_loaders['load_audit_trail'],
        'load_sessions_list': load_sessions_list,
    }
