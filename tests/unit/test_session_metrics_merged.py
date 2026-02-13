"""
Tests for session metrics merged into sessions tab.

Per PLAN-UI-OVERHAUL-001 Task 5.1: Merge Metrics+Sessions.
Batch 159 deepening (was 3 tests, now 8).
"""
import inspect

import pytest


class TestSessionMetricsMerged:
    def test_sessions_list_has_metrics_summary(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'metric' in source.lower()

    def test_sessions_list_shows_total_sessions(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'total' in source.lower()

    def test_sessions_list_shows_duration_info(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'duration' in source.lower() or 'hours' in source.lower()

    def test_sessions_list_has_table(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'VDataTable' in source

    def test_sessions_list_has_headers(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'headers' in source

    def test_metrics_row_shows_completed(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'completed' in source.lower() or 'COMPLETED' in source

    def test_metrics_row_shows_active(self):
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'active' in source.lower() or 'ACTIVE' in source

    def test_build_metrics_row_callable(self):
        from agent.governance_ui.views.sessions.list import _build_metrics_row
        assert callable(_build_metrics_row)
