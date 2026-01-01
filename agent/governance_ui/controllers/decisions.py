"""
Decisions Controllers (GAP-FILE-005)
====================================
Controller functions for decision operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

from typing import Any


def register_decisions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register decision-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused but kept for consistency)
    """

    @ctrl.set("select_decision")
    def select_decision(decision_id):
        """Handle decision selection for detail view."""
        for decision in state.decisions:
            if decision.get('decision_id') == decision_id or decision.get('id') == decision_id:
                state.selected_decision = decision
                state.show_decision_detail = True
                break

    @ctrl.set("close_decision_detail")
    def close_decision_detail():
        """Close decision detail view."""
        state.show_decision_detail = False
        state.selected_decision = None
