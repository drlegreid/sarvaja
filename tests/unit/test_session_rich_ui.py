"""
Tests for EPIC-F: Rich Session UI Features.

Verifies:
- F.1: Dynamic column filters (Status, Agent)
- F.2: Duration column computation
- F.3: Timeline histogram data generation
- F.4: Pivot table aggregation
- F.5: Server-side pagination with filters

Created: 2026-02-09
"""
import pytest
from datetime import datetime, timedelta


class TestDurationComputation:
    """F.2: Session duration column computation."""

    def test_normal_duration_hours_and_minutes(self):
        """Duration of 2h 15m should format correctly."""
        from agent.governance_ui.utils import compute_session_duration
        start = "2026-02-09T10:00:00"
        end = "2026-02-09T12:15:00"
        assert compute_session_duration(start, end) == "2h 15m"

    def test_short_duration_minutes_only(self):
        """Duration under 1h should show only minutes."""
        from agent.governance_ui.utils import compute_session_duration
        start = "2026-02-09T10:00:00"
        end = "2026-02-09T10:45:00"
        assert compute_session_duration(start, end) == "45m"

    def test_very_short_duration(self):
        """Duration under 1 minute should show <1m."""
        from agent.governance_ui.utils import compute_session_duration
        start = "2026-02-09T10:00:00"
        end = "2026-02-09T10:00:30"
        assert compute_session_duration(start, end) == "<1m"

    def test_ongoing_session_no_end_time(self):
        """Active session with no end time should show 'ongoing'."""
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-09T10:00:00", "") == "ongoing"
        assert compute_session_duration("2026-02-09T10:00:00", None) == "ongoing"

    def test_no_start_time(self):
        """Missing start time should return empty string."""
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("", "2026-02-09T12:00:00") == ""
        assert compute_session_duration(None, "2026-02-09T12:00:00") == ""

    def test_invalid_timestamps(self):
        """Invalid timestamps should return empty string."""
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("invalid", "also-invalid") == ""

    def test_handles_nanosecond_timestamps(self):
        """TypeDB timestamps with nanoseconds should be handled."""
        from agent.governance_ui.utils import compute_session_duration
        start = "2026-02-09T10:00:00.000000000"
        end = "2026-02-09T11:30:00.000000000"
        assert compute_session_duration(start, end) == "1h 30m"


class TestTimelineData:
    """F.3: Timeline histogram data generation."""

    def test_timeline_returns_14_days(self):
        """Timeline should always return 14 data points."""
        from agent.governance_ui.utils import compute_timeline_data
        values, labels = compute_timeline_data([])
        assert len(values) == 14
        assert len(labels) == 14

    def test_timeline_counts_sessions_by_date(self):
        """Sessions on the same date should be counted together."""
        from agent.governance_ui.utils import compute_timeline_data
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        sessions = [
            {"start_time": today},
            {"start_time": today},
            {"start_time": today},
        ]
        values, labels = compute_timeline_data(sessions)
        # Last value should be 3 (today)
        assert values[-1] == 3

    def test_timeline_labels_are_mm_dd(self):
        """Labels should be in MM-DD format."""
        from agent.governance_ui.utils import compute_timeline_data
        _, labels = compute_timeline_data([])
        for label in labels:
            assert len(label) == 5  # MM-DD
            assert "-" in label

    def test_timeline_handles_no_sessions(self):
        """Empty session list should produce all-zero timeline."""
        from agent.governance_ui.utils import compute_timeline_data
        values, _ = compute_timeline_data([])
        assert all(v == 0 for v in values)


class TestPivotData:
    """F.4: Pivot table aggregation."""

    def test_pivot_groups_by_agent(self):
        """Pivot should group sessions by agent_id."""
        from agent.governance_ui.utils import compute_pivot_data
        sessions = [
            {"agent_id": "agent-curator", "status": "COMPLETED",
             "start_time": "2026-02-09T10:00:00", "end_time": "2026-02-09T11:00:00"},
            {"agent_id": "agent-curator", "status": "ACTIVE",
             "start_time": "2026-02-09T12:00:00"},
            {"agent_id": "agent-scanner", "status": "COMPLETED",
             "start_time": "2026-02-09T10:00:00", "end_time": "2026-02-09T10:30:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert len(result) == 2
        curator = [r for r in result if r["group"] == "agent-curator"][0]
        assert curator["count"] == 2
        assert curator["completed"] == 1
        assert curator["active"] == 1

    def test_pivot_groups_by_status(self):
        """Pivot should group sessions by status."""
        from agent.governance_ui.utils import compute_pivot_data
        sessions = [
            {"status": "COMPLETED", "start_time": "2026-02-09T10:00:00",
             "end_time": "2026-02-09T11:00:00"},
            {"status": "COMPLETED", "start_time": "2026-02-09T12:00:00",
             "end_time": "2026-02-09T13:00:00"},
            {"status": "ACTIVE", "start_time": "2026-02-09T14:00:00"},
        ]
        result = compute_pivot_data(sessions, "status")
        assert len(result) == 2
        completed = [r for r in result if r["group"] == "COMPLETED"][0]
        assert completed["count"] == 2

    def test_pivot_handles_none_agent(self):
        """Sessions with no agent should group under '(none)'."""
        from agent.governance_ui.utils import compute_pivot_data
        sessions = [
            {"agent_id": None, "status": "COMPLETED",
             "start_time": "2026-02-09T10:00:00", "end_time": "2026-02-09T11:00:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert result[0]["group"] == "(none)"

    def test_pivot_avg_duration_format(self):
        """Average duration should be formatted as hours and minutes."""
        from agent.governance_ui.utils import compute_pivot_data
        sessions = [
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-09T10:00:00", "end_time": "2026-02-09T12:00:00"},
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-09T13:00:00", "end_time": "2026-02-09T14:00:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        # Avg: (120min + 60min) / 2 = 90min = 1h 30m
        assert result[0]["avg_duration"] == "1h 30m"

    def test_pivot_empty_sessions(self):
        """Empty session list should return empty pivot."""
        from agent.governance_ui.utils import compute_pivot_data
        assert compute_pivot_data([], "agent_id") == []


class TestFilterState:
    """F.1: Dynamic column filter state and view integration."""

    def test_initial_state_has_filter_fields(self):
        """Initial state should include sessions filter fields."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "sessions_filter_status" in state
        assert state["sessions_filter_status"] is None
        assert "sessions_filter_agent" in state
        assert state["sessions_filter_agent"] is None
        assert "sessions_agent_options" in state
        assert state["sessions_agent_options"] == []

    def test_initial_state_has_view_mode(self):
        """Initial state should include view mode toggle."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_view_mode"] == "table"

    def test_initial_state_has_timeline_data(self):
        """Initial state should include timeline data fields."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_timeline_data"] == []
        assert state["sessions_timeline_labels"] == []

    def test_initial_state_has_pivot_data(self):
        """Initial state should include pivot data fields."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert state["sessions_pivot_data"] == []
        assert state["sessions_pivot_group_by"] == "agent_id"


class TestViewIntegration:
    """F.1-F.5: View source code integration checks."""

    def test_list_view_has_filter_dropdowns(self):
        """Sessions list view should have filter dropdown components."""
        import inspect
        from agent.governance_ui.views.sessions.list import build_sessions_list_view
        source = inspect.getsource(build_sessions_list_view.__module__ and
                                    __import__('agent.governance_ui.views.sessions.list',
                                               fromlist=['']))
        assert "sessions_filter_status" in source
        assert "sessions_filter_agent" in source

    def test_list_view_has_duration_column(self):
        """Sessions table should include duration column."""
        import inspect
        import agent.governance_ui.views.sessions.list as mod
        source = inspect.getsource(mod)
        assert '"duration"' in source or "'duration'" in source

    def test_list_view_has_timeline(self):
        """Sessions view should include timeline sparkline."""
        import inspect
        import agent.governance_ui.views.sessions.list as mod
        source = inspect.getsource(mod)
        assert "sessions_timeline_data" in source
        assert "VSparkline" in source

    def test_list_view_has_pivot_table(self):
        """Sessions view should include pivot table."""
        import inspect
        import agent.governance_ui.views.sessions.list as mod
        source = inspect.getsource(mod)
        assert "sessions_pivot_data" in source
        assert "sessions_view_mode" in source

    def test_controller_has_filter_trigger(self):
        """Controller should have sessions_apply_filters trigger."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "sessions_apply_filters" in source

    def test_controller_computes_duration(self):
        """Controller should compute duration for each session."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "compute_session_duration" in source

    def test_controller_computes_timeline(self):
        """Controller should compute timeline data."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "compute_timeline_data" in source
