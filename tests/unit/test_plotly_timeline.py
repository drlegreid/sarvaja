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

    def test_14_day_range(self):
        """Timeline should cover exactly 14 days."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        result = compute_timeline_plotly_data([])
        assert len(result["data"][0]["x"]) == 14

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

    def test_sessions_outside_14_days_excluded(self):
        """Sessions older than 14 days should not appear."""
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        sessions = [{"start_time": f"{old_date}T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        # All counts should be 0 since the session is outside the window
        assert all(v == 0 for v in result["data"][0]["y"])


class TestPlotlyAvailability:
    """Check trame-plotly detection."""

    def test_has_plotly_returns_bool(self):
        """has_plotly() should return a boolean."""
        from agent.governance_ui.views.sessions.timeline import has_plotly
        result = has_plotly()
        assert isinstance(result, bool)
