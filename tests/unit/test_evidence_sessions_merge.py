"""
Tests for merging Evidence Search into Sessions tab.

Per PLAN-UI-OVERHAUL-001 Task 5.3: Merge Evidence+Sessions.
Batch 159 deepening (was 3 tests, now 8).
"""
import inspect

import pytest


class TestEvidenceSessionsMerge:
    def test_sessions_list_has_evidence_search(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'evidence' in source.lower()

    def test_sessions_list_has_semantic_search_button(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'perform_search' in source or 'evidence_search' in source

    def test_search_view_redirects_to_sessions(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'sessions' in source.lower()

    def test_sessions_has_filter_status(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'sessions-filter-status' in source

    def test_sessions_has_filter_agent(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'sessions-filter-agent' in source

    def test_sessions_has_search_icon(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'mdi-magnify' in source

    def test_build_metrics_row_callable(self):
        from agent.governance_ui.views.sessions.list import _build_metrics_row
        assert callable(_build_metrics_row)

    def test_build_filters_row_callable(self):
        from agent.governance_ui.views.sessions.list import _build_filters_row
        assert callable(_build_filters_row)
