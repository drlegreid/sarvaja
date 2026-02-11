"""
Tests for Plotly timeline data computation (F.3 upgrade).

Verifies that the stacked bar chart data is correctly computed
from session data, with proper date bucketing and status breakdown.

Created: 2026-02-11
"""

import pytest
from datetime import datetime, timedelta


class TestPlotlyTimelineData:
    """Timeline data computation for Plotly chart."""

    def test_compute_returns_traces_and_layout(self):
        """Output must have data (traces list) and layout dict."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"start_time": datetime.now().isoformat(), "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        assert "data" in result
        assert "layout" in result
        assert len(result["data"]) == 2  # COMPLETED + ACTIVE traces

    def test_completed_sessions_in_green_trace(self):
        """COMPLETED sessions should appear in the green trace."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        today = datetime.now().strftime("%Y-%m-%d")
        sessions = [
            {"start_time": f"{today}T10:00:00", "status": "COMPLETED"},
            {"start_time": f"{today}T11:00:00", "status": "COMPLETED"},
        ]
        result = compute_timeline_plotly_data(sessions)
        completed_trace = result["data"][0]
        assert completed_trace["name"] == "Completed"
        # Today should be the last date in x-axis
        today_mm_dd = today[5:]  # MM-DD
        assert today_mm_dd in completed_trace["x"]
        idx = completed_trace["x"].index(today_mm_dd)
        assert completed_trace["y"][idx] == 2

    def test_active_sessions_in_blue_trace(self):
        """ACTIVE sessions should appear in the blue trace."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        today = datetime.now().strftime("%Y-%m-%d")
        sessions = [
            {"start_time": f"{today}T10:00:00", "status": "ACTIVE"},
        ]
        result = compute_timeline_plotly_data(sessions)
        active_trace = result["data"][1]
        assert active_trace["name"] == "Active"
        today_mm_dd = today[5:]
        idx = active_trace["x"].index(today_mm_dd)
        assert active_trace["y"][idx] == 1

    def test_default_range_minimum_7_days(self):
        """Empty sessions should produce at least 7+1 day range."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        result = compute_timeline_plotly_data([])
        # Default with no sessions: 14 days (clamped to min 7)
        assert len(result["data"][0]["x"]) >= 8  # 7+1 (inclusive)

    def test_stacked_bar_layout(self):
        """Layout should specify stacked bar mode."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        result = compute_timeline_plotly_data([])
        assert result["layout"]["barmode"] == "stack"

    def test_empty_sessions_returns_zero_counts(self):
        """Empty session list should have all-zero counts."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        result = compute_timeline_plotly_data([])
        assert all(v == 0 for v in result["data"][0]["y"])
        assert all(v == 0 for v in result["data"][1]["y"])

    def test_adaptive_range_includes_old_sessions(self):
        """Old sessions should extend the timeline range to include them."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        sessions = [{"start_time": f"{old_date}T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        # Adaptive range should expand to include the old session
        assert len(result["data"][0]["x"]) >= 31  # at least 30+1 days
        # The old date should be in the range with count > 0
        assert sum(result["data"][0]["y"]) == 1

    def test_sessions_beyond_60_days_capped(self):
        """Sessions older than 60 days should cap the range at 60."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        old_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        sessions = [{"start_time": f"{old_date}T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        # Capped at 60+1 days
        assert len(result["data"][0]["x"]) == 61


class TestPlotlyAvailability:
    """Check trame-plotly detection."""

    def test_has_plotly_returns_bool(self):
        """has_plotly() should return a boolean."""
        from agent.governance_ui.views.sessions.timeline import has_plotly
        result = has_plotly()
        assert isinstance(result, bool)
