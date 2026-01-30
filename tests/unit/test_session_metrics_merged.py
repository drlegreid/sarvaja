"""
Tests for session metrics merged into sessions tab.

Per PLAN-UI-OVERHAUL-001 Task 5.1: Merge Metrics+Sessions.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestSessionMetricsMerged:
    """Verify session metrics are integrated into sessions list view."""

    def test_sessions_list_has_metrics_summary(self):
        """Sessions list should include metrics summary cards."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'metric' in source.lower(), (
            "Sessions list should include metrics summary"
        )

    def test_sessions_list_shows_total_sessions(self):
        """Sessions list should show total sessions count."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'total' in source.lower(), (
            "Sessions list should show total sessions metric"
        )

    def test_sessions_list_shows_duration_info(self):
        """Sessions list should show session duration information."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'duration' in source.lower() or 'hours' in source.lower(), (
            "Sessions list should show duration/hours metric"
        )
