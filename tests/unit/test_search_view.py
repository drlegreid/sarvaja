"""
Tests for search view component.

Batch 168: New coverage for agent/governance_ui/views/search_view.py (0->10 tests).
"""
import inspect

import pytest


class TestSearchViewComponents:
    def test_build_search_view_callable(self):
        from agent.governance_ui.views.search_view import build_search_view
        assert callable(build_search_view)


class TestSearchViewContent:
    def test_has_search_view_testid(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-view" in source

    def test_has_search_input(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-input" in source

    def test_has_search_btn(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-btn" in source

    def test_has_redirect_notice(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-redirect-notice" in source

    def test_has_magnify_icon(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "mdi-magnify" in source

    def test_has_no_results_state(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-no-results" in source

    def test_has_results_table(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-results-table" in source

    def test_has_loading_indicator(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-loading" in source

    def test_has_goto_sessions_btn(self):
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert "search-goto-sessions-btn" in source
