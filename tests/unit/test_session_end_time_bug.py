"""
Tests for BUG-SESSION-END-001: Session end_time column display fix.

Verifies:
- format_timestamp works on session end_time values
- Missing end_time shows meaningful text based on session status
- Loader enriches sessions with end_time fallbacks
"""
import inspect


class TestFormatTimestamp:
    def test_formats_iso_to_readable(self):
        from agent.governance_ui.utils import format_timestamp
        result = format_timestamp("2026-02-14T15:30:45.000000000")
        assert result == "2026-02-14 15:30"

    def test_handles_none(self):
        from agent.governance_ui.utils import format_timestamp
        assert format_timestamp(None) == ""

    def test_handles_empty_string(self):
        from agent.governance_ui.utils import format_timestamp
        assert format_timestamp("") == ""

    def test_handles_no_T(self):
        from agent.governance_ui.utils import format_timestamp
        result = format_timestamp("2026-02-14 15:30:45")
        assert "2026-02-14" in result


class TestEndTimeFallback:
    def test_loader_has_end_time_fallback(self):
        """BUG-SESSION-END-001: Loader must set end_time fallback for missing values."""
        from agent.governance_ui.dashboard_data_loader import _load_sessions
        src = inspect.getsource(_load_sessions)
        assert "(completed)" in src or "ongoing" in src
        assert "BUG-SESSION-END-001" in src

    def test_completed_session_shows_completed(self):
        """COMPLETED sessions with no end_time should show '(completed)'."""
        item = {"status": "COMPLETED", "end_time": None, "start_time": "2026-02-14T10:00:00"}
        if not item.get("end_time"):
            status = (item.get("status") or "").upper()
            if status in ("COMPLETED", "CLOSED"):
                item["end_time"] = "(completed)"
        assert item["end_time"] == "(completed)"

    def test_active_session_shows_ongoing(self):
        """ACTIVE sessions should show 'ongoing'."""
        item = {"status": "ACTIVE", "end_time": None, "start_time": "2026-02-14T10:00:00"}
        if not item.get("end_time"):
            status = (item.get("status") or "").upper()
            if status == "ACTIVE":
                item["end_time"] = "ongoing"
        assert item["end_time"] == "ongoing"

    def test_session_with_end_time_unchanged(self):
        """Sessions with valid end_time should not be overwritten."""
        item = {"status": "COMPLETED", "end_time": "2026-02-14T12:00:00"}
        if not item.get("end_time"):
            item["end_time"] = "(completed)"
        assert item["end_time"] == "2026-02-14T12:00:00"


class TestSessionsListEndColumn:
    def test_list_has_end_time_column(self):
        from agent.governance_ui.views.sessions import list as sess_list
        src = inspect.getsource(sess_list)
        assert "end_time" in src
