"""
Tests for metrics view search and timeline tabs.

Per DOC-SIZE-01-v1: Extracted from metrics_view.py.
Batch 164: New coverage for views/metrics_view_tabs.py (0->10 tests).
"""
import inspect

import pytest


class TestMetricsViewTabsComponents:
    def test_build_search_tab_callable(self):
        from agent.governance_ui.views.metrics_view_tabs import build_search_tab
        assert callable(build_search_tab)

    def test_build_timeline_tab_callable(self):
        from agent.governance_ui.views.metrics_view_tabs import build_timeline_tab
        assert callable(build_timeline_tab)


class TestSearchTabContent:
    def test_has_search_input_testid(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "metrics-search-input" in source

    def test_has_search_button(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "metrics-search-btn" in source

    def test_has_search_results(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "metrics-search-results" in source

    def test_has_magnify_icon(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "mdi-magnify" in source


class TestTimelineTabContent:
    def test_has_timeline_btn_testid(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "metrics-timeline-btn" in source

    def test_has_timeline_testid(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "metrics-timeline" in source

    def test_has_calendar_icon(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "mdi-calendar" in source

    def test_has_branches_section(self):
        from agent.governance_ui.views import metrics_view_tabs
        source = inspect.getsource(metrics_view_tabs)
        assert "Branches" in source
