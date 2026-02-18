"""
Data Loader Controllers (GAP-FILE-005)
======================================
Controller functions for loading/refreshing data.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-048: Trace bar event capture
Per DOC-SIZE-01-v1: Infra/workflow/audit extracted to separate modules.
    Refresh + sessions-list in data_loaders_refresh.py.

Created: 2024-12-28
Updated: 2026-02-01 (split per DOC-SIZE-01-v1)
"""

import time
from datetime import datetime

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)
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
from agent.governance_ui.controllers.data_loaders_refresh import register_refresh_controllers


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

    # Register refresh + sessions-list controllers
    refresh_loaders = register_refresh_controllers(
        state, ctrl, api_base_url, infra_loaders)

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
                except Exception as e:
                    # BUG-UI-SILENT-JSON-001: Log JSON parse failures
                    # BUG-439-DL-001: Don't leak exception internals via add_error_trace → Trame WebSocket
                    add_error_trace(state, f"Agents JSON parse failed: {type(e).__name__}", "/api/agents")

                add_api_trace(
                    state, "/api/agents", "GET", response.status_code, duration_ms,
                    response_body=response_body
                )
                if response.status_code == 200 and response_body is not None:
                    data = response_body
                    state.agents = data.get("items", data) if isinstance(data, dict) else data
                else:
                    state.agents = []
        except Exception as e:
            # BUG-439-DL-002: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load agents failed: {type(e).__name__}", "/api/agents")
            state.agents = []

        # BUG-283-DL-001: Wrap in try to prevent exception aborting proposals/stats load
        try:
            state.trust_leaderboard = build_trust_leaderboard(state.agents)
        except Exception as e:
            # BUG-439-DL-003: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Build trust leaderboard failed: {type(e).__name__}", "build_trust_leaderboard()")
            state.trust_leaderboard = []

        try:
            state.proposals = get_proposals()
        except Exception as e:
            # BUG-439-DL-004: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load proposals failed: {type(e).__name__}", "get_proposals()")
            state.proposals = []

        try:
            state.escalated_proposals = get_escalated_proposals()
        except Exception as e:
            # BUG-439-DL-005: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load escalated proposals failed: {type(e).__name__}", "get_escalated_proposals()")
            state.escalated_proposals = []

        # BUG-193-010: Guard against get_governance_stats raising
        try:
            state.governance_stats = get_governance_stats(
                state.agents,
                state.proposals
            )
        except Exception as e:
            # BUG-439-DL-006: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load governance stats failed: {type(e).__name__}", "get_governance_stats()")
            state.governance_stats = {}

    def load_monitor_data():
        """Load monitoring data from RuleMonitor."""
        # BUG-283-DL-002: Initialize defaults before try to prevent partial state on exception
        state.monitor_feed = state.monitor_feed if hasattr(state, 'monitor_feed') else []
        state.monitor_alerts = state.monitor_alerts if hasattr(state, 'monitor_alerts') else []
        state.monitor_stats = state.monitor_stats if hasattr(state, 'monitor_stats') else {}
        state.top_rules = state.top_rules if hasattr(state, 'top_rules') else []
        state.hourly_stats = state.hourly_stats if hasattr(state, 'hourly_stats') else []
        try:
            state.monitor_feed = get_monitor_feed(limit=50)
            state.monitor_alerts = get_monitor_alerts(acknowledged=False)
            state.monitor_stats = get_monitor_stats()
            state.top_rules = get_top_monitored_rules(limit=10)
            state.hourly_stats = get_hourly_monitor_stats()
        except Exception as e:
            # BUG-UI-LOAD-002: Add error handling to monitor data loading
            # BUG-439-DL-007: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load monitor data failed: {type(e).__name__}", "monitor_data")
            # BUG-283-DL-002: Mark timestamp as error so UI doesn't show false freshness
            state.monitor_last_updated = f"{datetime.now().isoformat(timespec='seconds')} (ERROR)"
            return
        state.monitor_last_updated = datetime.now().isoformat(timespec="seconds")

    def load_backlog_data():
        """Load available tasks and agent's claimed tasks from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tasks/available")
                if response.status_code == 200:
                    # BUG-239-DL-002: Unwrap paginated dict response
                    data = response.json()
                    state.available_tasks = data["items"] if isinstance(data, dict) and "items" in data else data
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
        except Exception as e:
            # BUG-439-DL-008: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load backlog failed: {type(e).__name__}", "/api/tasks/available")
            # BUG-225-CTRL-007: Don't surface transient refresh errors to user
            # (other loaders use add_error_trace only, not has_error)
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
                    # BUG-UI-EXEC-001: Set error state on non-200 response
                    state.has_error = True
                    state.error_message = f"Executive report API error: {response.status_code}"
                    state.executive_report = {
                        "error": f"Failed to load report: {response.status_code}",
                        "sections": [],
                        "overall_status": "error",
                        "metrics_summary": {},
                    }
        except Exception as e:
            # BUG-439-DL-009: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load executive report failed: {type(e).__name__}", "/api/reports/executive")
            # BUG-389-DL-001: Don't leak exception internals via Trame WebSocket (state.executive_report is pushed to browser)
            state.executive_report = {
                "error": type(e).__name__,
                "sections": [],
                "overall_status": "error",
                "metrics_summary": {},
            }
        finally:
            state.executive_loading = False

    @ctrl.trigger("load_trust_data")
    def trigger_load_trust_data():
        """Trigger for loading trust data."""
        load_trust_data()

    # NOTE: load_monitor_data trigger is registered in monitor.py
    # (with error handling + monitor_filter support).
    # The internal load_monitor_data() function above is used for initial load.

    @ctrl.trigger("refresh_backlog")
    def refresh_backlog():
        """Refresh backlog data."""
        load_backlog_data()

    @ctrl.trigger("load_executive_report")
    def trigger_load_executive_report():
        """Trigger to load executive report."""
        load_executive_report_data()

    # Return all loaders (including from extracted modules)
    return {
        'load_trust_data': load_trust_data,
        'load_monitor_data': load_monitor_data,
        'load_backlog_data': load_backlog_data,
        'load_executive_report_data': load_executive_report_data,
        'load_infra_status': infra_loaders['load_infra_status'],
        'load_workflow_status': workflow_loaders['load_workflow_status'],
        'load_audit_trail': audit_loaders['load_audit_trail'],
        'load_sessions_list': refresh_loaders['load_sessions_list'],
    }
