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
import re

import httpx
from typing import Any

# BUG-303-TRUST-001: Validate agent_id before URL path interpolation
_AGENT_ID_RE = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')

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

    @ctrl.trigger("select_agent")
    def select_agent(agent_id):
        """Select agent for detail view. Per EPIC-A.4: Fetch linked sessions."""
        # BUG-303-TRUST-001: Validate agent_id format before URL interpolation
        if not agent_id or not isinstance(agent_id, str) or not _AGENT_ID_RE.match(agent_id):
            return
        # BUG-239-RULES-001: Guard against None state.agents
        for agent in (state.agents or []):
            if agent.get('agent_id') == agent_id:
                state.selected_agent = agent
                state.show_agent_detail = True
                break

        # Fetch full session data for this agent (A.4: session-agent linking)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{api_base_url}/api/agents/{agent_id}/sessions")
                add_api_trace(state, f"/api/agents/{agent_id}/sessions", "GET", resp.status_code, 0)
                if resp.status_code == 200:
                    data = resp.json()
                    sessions = data.get("sessions", [])
                    state.agent_sessions = sessions
                    if state.selected_agent:
                        updated = dict(state.selected_agent)
                        updated["sessions_count"] = data.get("pagination", {}).get("total", len(sessions))
                        state.selected_agent = updated
                else:
                    # BUG-225-CTRL-009: Clear stale sessions from prior agent
                    state.agent_sessions = []
        except Exception as e:
            add_error_trace(state, f"Load agent sessions failed: {e}", f"/api/agents/{agent_id}/sessions")
            state.agent_sessions = []

    @ctrl.trigger("close_agent_detail")
    def close_agent_detail():
        """Close agent detail view and reset associated state."""
        state.selected_agent = None
        state.show_agent_detail = False
        state.agent_sessions = []

    @ctrl.trigger("toggle_agent_pause")
    def toggle_agent_pause(agent_id):
        """Toggle agent between PAUSED and ACTIVE. Per GAP-AGENT-PAUSE-001."""
        # BUG-303-TRUST-001: Validate agent_id format before URL interpolation
        if not agent_id or not isinstance(agent_id, str) or not _AGENT_ID_RE.match(agent_id):
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
                    # BUG-260-TRUST-001: Guard against None state.agents
                    agents = list(state.agents or [])
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
            # BUG-385-TRS-001: Don't leak httpx internals via Trame WebSocket
            state.status_message = f"Error toggling agent: {type(e).__name__}"

    @ctrl.trigger("stop_agent_task")
    def stop_agent_task(agent_id):
        """Stop an agent's current task."""
        if not agent_id:
            return
        state.status_message = f"Stop task for {agent_id} (not yet implemented — agents are PAUSED)"

    @ctrl.trigger("end_agent_session")
    def end_agent_session(agent_id):
        """End an agent's active session."""
        if not agent_id:
            return
        state.status_message = f"End session for {agent_id} (not yet implemented — agents are PAUSED)"

    @ctrl.trigger("register_agent")
    def register_agent(agent_id, name, agent_type, model, rules, instructions):
        """Register a new agent."""
        if not agent_id or not name:
            state.status_message = "Agent ID and name are required"
            return
        state.has_error = False
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{api_base_url}/api/agents", json={
                    "agent_id": agent_id,
                    "name": name,
                    "agent_type": agent_type or "custom",
                    "model": model or "",
                    "rules": rules or "",
                    "instructions": instructions or "",
                })
                if response.status_code in (200, 201):
                    state.status_message = f"Agent {agent_id} registered"
                    state.show_agent_registration = False
                else:
                    state.status_message = f"Registration failed: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Register agent failed: {e}", "/api/agents")
            # BUG-385-TRS-002: Don't leak httpx internals via Trame WebSocket
            state.status_message = f"Registration failed: {type(e).__name__}"

    @ctrl.trigger("load_trust_history")
    def load_trust_history(agent_id):
        """Load trust score history for an agent."""
        # BUG-303-TRUST-001: Validate agent_id format before URL interpolation
        if not agent_id or not isinstance(agent_id, str) or not _AGENT_ID_RE.match(agent_id):
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/agents/{agent_id}")
                if response.status_code == 200:
                    data = response.json()
                    state.trust_history = [{
                        "timestamp": data.get("last_active", "now"),
                        "score": data.get("trust_score", 0),
                        "tasks": data.get("tasks_executed", 0),
                    }]
                    state.status_message = f"Trust data loaded for {agent_id}"
        except Exception as e:
            add_error_trace(state, f"Load trust history failed: {e}",
                            f"/api/agents/{agent_id}")
            state.trust_history = []
