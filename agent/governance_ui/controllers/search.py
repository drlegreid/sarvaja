"""
Search Controllers (GAP-UI-009)
===============================
Controller functions for evidence search operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-UI-009: Search functionality implementation

Created: 2026-01-02
"""

from typing import Any

from agent.governance_ui.data_access.core import search_evidence


def register_search_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register search-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused for search)
    """

    @ctrl.trigger("perform_search")
    def perform_search():
        """
        Execute evidence search with current search_query.

        Calls MCP governance_evidence_search tool and populates
        search_results state variable.
        """
        query = state.search_query
        if not query or not query.strip():
            state.search_results = []
            return

        try:
            state.is_loading = True
            results = search_evidence(query.strip())
            state.search_results = results
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Search failed: {str(e)}"
            state.search_results = []

    @ctrl.set("clear_search")
    def clear_search():
        """Clear search query and results."""
        state.search_query = ""
        state.search_results = []
