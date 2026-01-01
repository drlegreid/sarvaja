"""
Data Loader Controllers (GAP-FILE-005)
======================================
Controller functions for loading/refreshing data.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

import httpx
from typing import Any, Callable

from agent.governance_ui import (
    get_rules,
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

    def load_trust_data():
        """Load agent trust data from REST API."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/agents")
                if response.status_code == 200:
                    state.agents = response.json()
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
                        all_tasks = response.json()
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
            print(f"Error loading backlog data: {e}")
            state.available_tasks = []
            state.claimed_tasks = []

    def load_executive_report_data():
        """Load executive report from REST API."""
        try:
            state.executive_loading = True
            with httpx.Client(timeout=15.0) as client:
                params = {"period": state.executive_period or "week"}
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

    @ctrl.trigger("refresh_data")
    def refresh_data():
        """Refresh all data from REST API."""
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                try:
                    rules_response = client.get(f"{api_base_url}/api/rules")
                    if rules_response.status_code == 200:
                        state.rules = rules_response.json()
                except Exception:
                    pass

                try:
                    decisions_response = client.get(f"{api_base_url}/api/decisions")
                    if decisions_response.status_code == 200:
                        state.decisions = decisions_response.json()
                except Exception:
                    pass

                try:
                    tasks_response = client.get(f"{api_base_url}/api/tasks")
                    if tasks_response.status_code == 200:
                        state.tasks = tasks_response.json()
                except Exception:
                    pass

                try:
                    sessions_response = client.get(f"{api_base_url}/api/sessions")
                    if sessions_response.status_code == 200:
                        state.sessions = sessions_response.json()
                except Exception:
                    pass

                try:
                    agents_response = client.get(f"{api_base_url}/api/agents")
                    if agents_response.status_code == 200:
                        state.agents = agents_response.json()
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

    # Return loaders for internal use
    return {
        'load_trust_data': load_trust_data,
        'load_monitor_data': load_monitor_data,
        'load_backlog_data': load_backlog_data,
        'load_executive_report_data': load_executive_report_data,
    }
