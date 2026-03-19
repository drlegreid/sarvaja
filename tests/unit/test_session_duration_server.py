"""
Tests for P0-2: Server-side session duration computation.

Verifies:
- compute_session_duration_from_timestamps handles datetime objects and strings
- Both session_to_response() and _session_to_dict() produce identical duration
- _ensure_response() computes duration for in-memory dicts
- Edge cases: ongoing, >24h, repair artifacts, <1m
"""
from datetime import datetime
from unittest.mock import MagicMock


class TestComputeSessionDurationFromTimestamps:
    """Test the shared duration computation function."""

    def test_normal_duration(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T10:00:00", "2026-02-14T12:15:00")
        assert result == "2h 15m"

    def test_datetime_objects(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        start = datetime(2026, 2, 14, 10, 0, 0)
        end = datetime(2026, 2, 14, 12, 15, 0)
        result = compute_session_duration_from_timestamps(start, end)
        assert result == "2h 15m"

    def test_ongoing(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps("2026-02-14T10:00:00", None)
        assert result == "ongoing"

    def test_no_start(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(None, "2026-02-14T10:00:00")
        assert result is None

    def test_both_none(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(None, None)
        assert result is None

    def test_less_than_one_minute(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T10:00:00", "2026-02-14T10:00:30")
        assert result == "<1m"

    def test_over_24h(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-01-15T10:00:00", "2026-02-13T06:18:39")
        assert result == ">24h"

    def test_repair_artifact(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-01-14T09:00:00", "2026-01-14T13:00:00")
        assert result == "~4h (est)"

    def test_exact_hour(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T10:00:00", "2026-02-14T12:00:00")
        assert result == "2h 0m"

    def test_minutes_only(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T10:00:00", "2026-02-14T10:45:00")
        assert result == "45m"

    def test_nanosecond_format(self):
        """TypeDB returns .000000000 nanosecond format."""
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-15T12:10:11.000000000", "2026-02-15T14:27:40.000000000")
        assert result == "2h 17m"

    def test_negative_delta_abs(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T12:00:00", "2026-02-14T10:00:00")
        assert result == "2h 0m"

    def test_z_suffix(self):
        from governance.stores.helpers import compute_session_duration_from_timestamps
        result = compute_session_duration_from_timestamps(
            "2026-02-14T10:00:00Z", "2026-02-14T11:30:00Z")
        assert result == "1h 30m"


class TestDualConversionParity:
    """Both session_to_response and _session_to_dict MUST produce identical duration."""

    def _make_session(self, started_at, completed_at):
        """Create a mock TypeDB Session entity."""
        session = MagicMock()
        session.id = "SESSION-2026-02-14-TEST"
        session.started_at = started_at
        session.completed_at = completed_at
        session.status = "COMPLETED" if completed_at else "ACTIVE"
        session.tasks_completed = 0
        session.agent_id = None
        session.description = "Test"
        session.file_path = None
        session.evidence_files = []
        session.linked_rules_applied = []
        session.linked_decisions = []
        session.cc_session_uuid = None
        session.cc_project_slug = None
        session.cc_git_branch = None
        session.cc_tool_count = None
        session.cc_thinking_chars = None
        session.cc_compaction_count = None
        session.project_id = None
        return session

    def test_both_converters_same_duration_normal(self):
        from governance.stores.helpers import session_to_response
        from governance.stores.typedb_access import _session_to_dict

        start = datetime(2026, 2, 14, 10, 0, 0)
        end = datetime(2026, 2, 14, 12, 15, 0)
        session = self._make_session(start, end)

        response = session_to_response(session)
        dict_result = _session_to_dict(session)

        assert response.duration == "2h 15m"
        assert dict_result["duration"] == "2h 15m"
        assert response.duration == dict_result["duration"]

    def test_both_converters_same_duration_ongoing(self):
        from governance.stores.helpers import session_to_response
        from governance.stores.typedb_access import _session_to_dict

        start = datetime(2026, 2, 14, 10, 0, 0)
        session = self._make_session(start, None)

        response = session_to_response(session)
        dict_result = _session_to_dict(session)

        assert response.duration == "ongoing"
        assert dict_result["duration"] == "ongoing"

    def test_both_converters_same_duration_short(self):
        from governance.stores.helpers import session_to_response
        from governance.stores.typedb_access import _session_to_dict

        start = datetime(2026, 2, 14, 10, 0, 0)
        end = datetime(2026, 2, 14, 10, 0, 30)
        session = self._make_session(start, end)

        response = session_to_response(session)
        dict_result = _session_to_dict(session)

        assert response.duration == "<1m"
        assert dict_result["duration"] == "<1m"


class TestEnsureResponseDuration:
    """_ensure_response must compute duration for in-memory dicts."""

    def test_dict_without_duration_gets_computed(self):
        from governance.routes.sessions.crud import _ensure_response
        result = _ensure_response({
            "session_id": "SESSION-TEST",
            "start_time": "2026-02-14T10:00:00",
            "end_time": "2026-02-14T12:15:00",
            "status": "COMPLETED",
        })
        assert result.duration == "2h 15m"

    def test_dict_with_duration_preserved(self):
        from governance.routes.sessions.crud import _ensure_response
        result = _ensure_response({
            "session_id": "SESSION-TEST",
            "start_time": "2026-02-14T10:00:00",
            "end_time": "2026-02-14T12:15:00",
            "status": "COMPLETED",
            "duration": "2h 15m",
        })
        assert result.duration == "2h 15m"

    def test_dict_ongoing_duration(self):
        from governance.routes.sessions.crud import _ensure_response
        result = _ensure_response({
            "session_id": "SESSION-TEST",
            "start_time": "2026-02-14T10:00:00",
            "status": "ACTIVE",
        })
        assert result.duration == "ongoing"


class TestUIConsistency:
    """Verify UI utils compute_session_duration matches server-side."""

    def test_ui_and_server_agree(self):
        from agent.governance_ui.utils import compute_session_duration
        from governance.stores.helpers import compute_session_duration_from_timestamps

        cases = [
            ("2026-02-14T10:00:00", "2026-02-14T12:15:00"),
            ("2026-02-14T10:00:00", "2026-02-14T10:45:00"),
            ("2026-02-14T10:00:00", "2026-02-14T10:00:30"),
            ("2026-01-14T09:00:00", "2026-01-14T13:00:00"),
            ("2026-01-15T10:00:00", "2026-02-13T06:18:39"),
        ]
        for start, end in cases:
            ui_result = compute_session_duration(start, end)
            server_result = compute_session_duration_from_timestamps(start, end)
            assert ui_result == server_result, (
                f"Mismatch for {start}→{end}: UI='{ui_result}' vs Server='{server_result}'"
            )

    def test_ui_and_server_agree_ongoing(self):
        from agent.governance_ui.utils import compute_session_duration
        from governance.stores.helpers import compute_session_duration_from_timestamps

        ui_result = compute_session_duration("2026-02-14T10:00:00", "")
        server_result = compute_session_duration_from_timestamps("2026-02-14T10:00:00", None)
        assert ui_result == server_result

    def test_ui_and_server_agree_no_start(self):
        from agent.governance_ui.utils import compute_session_duration
        from governance.stores.helpers import compute_session_duration_from_timestamps

        ui_result = compute_session_duration("", "2026-02-14T10:00:00")
        server_result = compute_session_duration_from_timestamps(None, "2026-02-14T10:00:00")
        # UI returns "" for no start, server returns None — both mean "no data"
        assert ui_result in ("", None)
        assert server_result in ("", None)
