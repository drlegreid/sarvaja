"""
Tests for merging Evidence Search into Sessions tab.

Per PLAN-UI-OVERHAUL-001 Task 5.3: Merge Evidence+Sessions.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestEvidenceSessionsMerge:
    """Verify evidence search is integrated into sessions list view."""

    def test_sessions_list_has_evidence_search(self):
        """Sessions list should include evidence search capability."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'evidence' in source.lower(), (
            "Sessions list should include evidence search"
        )

    def test_sessions_list_has_semantic_search_button(self):
        """Sessions list should have a semantic search trigger."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'perform_search' in source or 'evidence_search' in source, (
            "Sessions list should have semantic search trigger"
        )

    def test_search_view_redirects_to_sessions(self):
        """Search view should redirect users to sessions tab."""
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'sessions' in source.lower(), (
            "Search view should reference sessions tab"
        )
