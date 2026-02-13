"""
Tests for session metrics dashboard view.

Per SESSION-METRICS-01-v1: Session analytics UI.
Batch 161: New coverage for views/metrics_view.py (0→12 tests).
"""
import inspect

import pytest


class TestMetricsViewComponents:
    def test_build_metrics_view_callable(self):
        from agent.governance_ui.views.metrics_view import build_metrics_view
        assert callable(build_metrics_view)

    def test_build_metrics_header_callable(self):
        from agent.governance_ui.views.metrics_view import build_metrics_header
        assert callable(build_metrics_header)

    def test_build_metrics_tabs_callable(self):
        from agent.governance_ui.views.metrics_view import build_metrics_tabs
        assert callable(build_metrics_tabs)

    def test_build_stat_cards_callable(self):
        from agent.governance_ui.views.metrics_view import build_stat_cards
        assert callable(build_stat_cards)

    def test_build_per_day_table_callable(self):
        from agent.governance_ui.views.metrics_view import build_per_day_table
        assert callable(build_per_day_table)

    def test_build_tool_breakdown_callable(self):
        from agent.governance_ui.views.metrics_view import build_tool_breakdown
        assert callable(build_tool_breakdown)


class TestMetricsViewContent:
    def test_has_dashboard_testid(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-dashboard" in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-refresh-btn" in source

    def test_has_stat_cards(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-stat-cards" in source

    def test_has_per_day_table(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-per-day-table" in source

    def test_has_tool_breakdown(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-tool-breakdown" in source

    def test_has_days_filter(self):
        from agent.governance_ui.views import metrics_view
        source = inspect.getsource(metrics_view)
        assert "metrics-days-filter" in source
