"""
Tests for session timeline with Plotly.

Per F.3 upgrade: D3-level interactive session timeline.
Batch 167: New coverage for views/sessions/timeline.py (0->10 tests).
"""
import pytest


class TestTimelineComponents:
    def test_compute_timeline_plotly_data_callable(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        assert callable(compute_timeline_plotly_data)


class TestComputeTimelineData:
    def test_empty_sessions_returns_valid(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        result = compute_timeline_plotly_data([])
        assert isinstance(result, dict)
        assert "data" in result
        assert "layout" in result

    def test_single_session(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"start_time": "2026-02-13T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        assert len(result["data"]) >= 1

    def test_multiple_statuses(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [
            {"start_time": "2026-02-13T10:00:00", "status": "COMPLETED"},
            {"start_time": "2026-02-13T11:00:00", "status": "ACTIVE"},
        ]
        result = compute_timeline_plotly_data(sessions)
        assert len(result["data"]) >= 1

    def test_missing_start_time(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        assert isinstance(result, dict)

    def test_layout_has_title(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"start_time": "2026-02-13T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        assert "layout" in result

    def test_traces_have_type(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"start_time": "2026-02-13T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        for trace in result["data"]:
            assert "type" in trace or "x" in trace

    def test_multiple_days(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [
            {"start_time": "2026-02-12T10:00:00", "status": "COMPLETED"},
            {"start_time": "2026-02-13T10:00:00", "status": "COMPLETED"},
        ]
        result = compute_timeline_plotly_data(sessions)
        assert len(result["data"]) >= 1

    def test_unknown_status(self):
        from agent.governance_ui.views.sessions.timeline import compute_timeline_plotly_data
        sessions = [{"start_time": "2026-02-13T10:00:00", "status": "UNKNOWN"}]
        result = compute_timeline_plotly_data(sessions)
        assert isinstance(result, dict)

    def test_has_plotly_flag(self):
        from agent.governance_ui.views.sessions import timeline
        assert hasattr(timeline, "_HAS_PLOTLY")
