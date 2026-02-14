"""
Tests for BUG-SESSION-DURATION-001: Session duration display fix.

Verifies:
- compute_session_duration returns correct strings
- Session detail view uses 'duration' field (not 'duration_minutes')
- Controller computes duration after API fetch
"""
import inspect


class TestComputeSessionDuration:
    def test_short_duration(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-14T10:00:00", "2026-02-14T10:00:30") == "<1m"

    def test_minutes_only(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-14T10:00:00", "2026-02-14T10:45:00") == "45m"

    def test_hours_and_minutes(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-14T10:00:00", "2026-02-14T12:15:00") == "2h 15m"

    def test_ongoing(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-14T10:00:00", "") == "ongoing"

    def test_no_start(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("", "2026-02-14T10:00:00") == ""

    def test_exact_hour(self):
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration("2026-02-14T10:00:00", "2026-02-14T12:00:00") == "2h 0m"


class TestSessionDetailDurationField:
    def test_content_view_uses_duration_not_duration_minutes(self):
        """BUG-SESSION-DURATION-001: UI must use 'duration' field, not 'duration_minutes'."""
        from agent.governance_ui.views.sessions.content import build_session_info_card
        src = inspect.getsource(build_session_info_card)
        # Must use the string 'duration' field
        assert "selected_session.duration" in src
        # Must NOT use the old broken numeric field
        assert "duration_minutes" not in src

    def test_controller_computes_duration_after_api_fetch(self):
        """Controller must compute duration when selecting a session from API."""
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        src = inspect.getsource(register_sessions_controllers)
        assert "compute_session_duration" in src
        assert 'session_data["duration"]' in src


class TestSessionListDurationColumn:
    def test_list_has_duration_column(self):
        from agent.governance_ui.views.sessions.list import build_sessions_list_view
        src = inspect.getsource(build_sessions_list_view)
        assert "duration" in src

    def test_loader_computes_duration(self):
        from agent.governance_ui.dashboard_data_loader import _load_sessions
        src = inspect.getsource(_load_sessions)
        assert "compute_session_duration" in src
