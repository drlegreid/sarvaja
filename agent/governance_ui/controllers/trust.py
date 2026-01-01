"""
Trust Dashboard Controllers (GAP-FILE-005)
==========================================
Controller functions for agent trust dashboard (P9.5 - RULE-011).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

from typing import Any


def register_trust_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register trust dashboard controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused but kept for consistency)
    """

    @ctrl.set("select_agent")
    def select_agent(agent_id):
        """Select agent for detail view."""
        for agent in state.agents:
            if agent.get('agent_id') == agent_id:
                state.selected_agent = agent
                state.show_agent_detail = True
                break

    @ctrl.set("close_agent_detail")
    def close_agent_detail():
        """Close agent detail view."""
        state.selected_agent = None
        state.show_agent_detail = False
