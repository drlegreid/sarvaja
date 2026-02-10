"""
Trust Dashboard Controllers (GAP-FILE-005)
==========================================
Controller functions for agent trust dashboard (P9.5 - RULE-011).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-AGENT-PAUSE-001: Agent pause/resume toggle

Created: 2024-12-28
"""

import logging
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_api_trace, add_error_trace

logger = logging.getLogger(__name__)


def register_trust_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register trust dashboard controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.set("select_agent")
    def select_agent(agent_id):
        """Select agent for detail view. Per EPIC-A.4: Fetch linked sessions."""
        for agent in state.agents:
            if agent.get('agent_id') == agent_id:
                state.selected_agent = agent
                state.show_agent_detail = True
                break

        # Fetch full session data for this agent (A.4: session-agent linking)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{api_base_url}/api/agents/{agent_id}/sessions")
                if resp.status_code == 200:
                    data = resp.json()
                    sessions = data.get("sessions", [])
                    state.agent_sessions = sessions
                    if state.selected_agent:
                        updated = dict(state.selected_agent)
                        updated["sessions_count"] = data.get("pagination", {}).get("total", len(sessions))
                        state.selected_agent = updated
        except Exception:
            state.agent_sessions = []

    @ctrl.set("close_agent_detail")
    def close_agent_detail():
        """Close agent detail view."""
        state.selected_agent = None
        state.show_agent_detail = False

    @ctrl.trigger("toggle_agent_pause")
    def toggle_agent_pause(agent_id):
        """Toggle agent between PAUSED and ACTIVE. Per GAP-AGENT-PAUSE-001."""
        if not agent_id:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(f"{api_base_url}/api/agents/{agent_id}/status/toggle")
                add_api_trace(
                    state, f"/api/agents/{agent_id}/status/toggle", "PUT",
                    response.status_code, 0,
                )
                if response.status_code == 200:
                    updated = response.json()
                    # Update selected_agent in place
                    state.selected_agent = updated
                    # Update in agents list
                    agents = list(state.agents)
                    for i, a in enumerate(agents):
                        if a.get("agent_id") == agent_id:
                            agents[i] = updated
                            break
                    state.agents = agents
                    new_status = updated.get("status", "unknown")
                    state.status_message = f"Agent {agent_id} is now {new_status}"
                else:
                    state.status_message = f"Failed to toggle agent: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Toggle agent pause failed: {e}", f"/api/agents/{agent_id}/status/toggle")
            state.status_message = f"Error toggling agent: {e}"
