"""
Sessions Controllers (GAP-FILE-005)
===================================
Controller functions for session operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

from typing import Any


def register_sessions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register session-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused but kept for consistency)
    """

    @ctrl.set("select_session")
    def select_session(session_id):
        """Handle session selection for detail view."""
        for session in state.sessions:
            if session.get('session_id') == session_id or session.get('id') == session_id:
                state.selected_session = session
                state.show_session_detail = True
                break

    @ctrl.set("close_session_detail")
    def close_session_detail():
        """Close session detail view."""
        state.show_session_detail = False
        state.selected_session = None
