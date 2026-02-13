"""
Tests for evidence grid / search view.

Per PLAN-UI-OVERHAUL-001 Task 1.4: Evidence Grid.
Per GAP-UI-009: Search functionality.

Batch 157c deepening (was 2 tests, now 12).
"""
import inspect

import pytest


class TestEvidenceGrid:
    """Verify evidence search uses data table for results."""

    def test_evidence_uses_data_table(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'VDataTable' in source

    def test_evidence_grid_has_columns(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'headers' in source

    def test_grid_has_source_column(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert '"Source"' in source

    def test_grid_has_score_column(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert '"Score"' in source

    def test_grid_has_content_column(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert '"Content"' in source


class TestSearchView:
    """Tests for the search view UI (redirect + search input)."""

    def test_build_search_view_callable(self):
        from agent.governance_ui.views.search_view import build_search_view
        assert callable(build_search_view)

    def test_redirect_notice(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "integrated into the Sessions tab" in source

    def test_search_input_present(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-input" in source

    def test_loading_indicator(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "is_loading" in source

    def test_no_results_state(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-no-results" in source

    def test_results_count(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-results-count" in source

    def test_goto_sessions_button(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-goto-sessions-btn" in source
