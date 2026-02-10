"""
Tests for backfill session data repair (GAP-GOVSESS-TIMESTAMP-001, AGENT-001, DURATION-001).

TDD RED-GREEN for session data quality fixes:
- Timestamps: derive from session_id date, not artificial values
- Agent IDs: assign default "code-agent" for backfilled sessions
- Durations: cap unrealistic durations, detect outliers

Created: 2026-02-11
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestTimestampRepair:
    """GAP-GOVSESS-TIMESTAMP-001: Fix identical artificial timestamps."""

    def test_parse_date_from_session_id(self):
        """Session ID SESSION-YYYY-MM-DD-TOPIC should yield that date."""
        from governance.services.session_repair import parse_session_date
        assert parse_session_date("SESSION-2026-01-15-RULE-AUDIT") == "2026-01-15"

    def test_parse_date_from_legacy_session_id(self):
        """Legacy SESSION-2024-12-26-001 format should also parse."""
        from governance.services.session_repair import parse_session_date
        assert parse_session_date("SESSION-2024-12-26-001") == "2024-12-26"

    def test_parse_date_returns_none_for_invalid(self):
        """Non-standard session IDs return None."""
        from governance.services.session_repair import parse_session_date
        assert parse_session_date("RANDOM-ID-NO-DATE") is None

    def test_generate_reasonable_timestamps(self):
        """Given a date, generate reasonable start/end timestamps."""
        from governance.services.session_repair import generate_timestamps
        start, end = generate_timestamps("2026-01-15")
        assert start.startswith("2026-01-15T")
        assert end.startswith("2026-01-15T")
        # Duration should be 1-8 hours
        st = datetime.fromisoformat(start)
        et = datetime.fromisoformat(end)
        delta = (et - st).total_seconds() / 3600
        assert 1 <= delta <= 8

    def test_detect_identical_timestamps(self):
        """Sessions with identical start/end deltas are flagged."""
        from governance.services.session_repair import detect_identical_timestamps
        sessions = [
            {"session_id": "S1", "start_time": "2026-01-01T00:00:00", "end_time": "2026-01-14T18:30:00"},
            {"session_id": "S2", "start_time": "2026-01-01T00:00:00", "end_time": "2026-01-14T18:30:00"},
            {"session_id": "S3", "start_time": "2026-01-02T09:00:00", "end_time": "2026-01-02T11:00:00"},
        ]
        flagged = detect_identical_timestamps(sessions)
        assert "S1" in flagged
        assert "S2" in flagged
        assert "S3" not in flagged


class TestAgentIdRepair:
    """GAP-GOVSESS-AGENT-001: Assign agent_id to backfilled sessions."""

    def test_detect_missing_agent_id(self):
        """Sessions without agent_id are flagged."""
        from governance.services.session_repair import detect_missing_agent
        sessions = [
            {"session_id": "S1", "agent_id": None},
            {"session_id": "S2", "agent_id": ""},
            {"session_id": "S3", "agent_id": "code-agent"},
        ]
        missing = detect_missing_agent(sessions)
        assert "S1" in missing
        assert "S2" in missing
        assert "S3" not in missing

    def test_assign_default_agent_id(self):
        """Backfilled sessions should get agent_id='code-agent'."""
        from governance.services.session_repair import assign_default_agent
        session = {"session_id": "S1", "agent_id": None, "description": "Backfilled from evidence file"}
        updated = assign_default_agent(session)
        assert updated["agent_id"] == "code-agent"

    def test_preserve_existing_agent_id(self):
        """Sessions with agent_id should not be overwritten."""
        from governance.services.session_repair import assign_default_agent
        session = {"session_id": "S1", "agent_id": "test-agent", "description": ""}
        updated = assign_default_agent(session)
        assert updated["agent_id"] == "test-agent"


class TestDurationRepair:
    """GAP-GOVSESS-DURATION-001: Cap unrealistic session durations."""

    def test_detect_unrealistic_duration(self):
        """Duration > 24h should be flagged as unrealistic."""
        from governance.services.session_repair import detect_unrealistic_durations
        sessions = [
            {"session_id": "S1", "start_time": "2024-12-26T00:00:00",
             "end_time": "2025-01-08T11:30:00"},  # ~9659h
            {"session_id": "S2", "start_time": "2026-01-15T09:00:00",
             "end_time": "2026-01-15T17:00:00"},   # 8h - reasonable
        ]
        flagged = detect_unrealistic_durations(sessions, max_hours=24)
        assert "S1" in flagged
        assert "S2" not in flagged

    def test_cap_duration_to_max(self):
        """Cap session duration to max_hours from start_time."""
        from governance.services.session_repair import cap_duration
        session = {
            "session_id": "S1",
            "start_time": "2024-12-26T09:00:00",
            "end_time": "2025-01-08T11:30:00",  # Unrealistic
        }
        capped = cap_duration(session, max_hours=8)
        et = datetime.fromisoformat(capped["end_time"])
        st = datetime.fromisoformat(capped["start_time"])
        assert (et - st).total_seconds() / 3600 == 8

    def test_cap_preserves_reasonable_durations(self):
        """Reasonable durations should not be modified."""
        from governance.services.session_repair import cap_duration
        session = {
            "session_id": "S1",
            "start_time": "2026-01-15T09:00:00",
            "end_time": "2026-01-15T11:30:00",  # 2.5h - reasonable
        }
        capped = cap_duration(session, max_hours=8)
        assert capped["end_time"] == "2026-01-15T11:30:00"


class TestRepairPlan:
    """Integration: Build and execute a full repair plan."""

    def test_build_repair_plan(self):
        """Build repair plan from session list."""
        from governance.services.session_repair import build_repair_plan
        sessions = [
            {
                "session_id": "SESSION-2026-01-15-TEST",
                "start_time": "2026-01-01T00:00:00",
                "end_time": "2026-01-14T18:30:00",
                "agent_id": None,
                "description": "Backfilled from evidence file",
                "status": "COMPLETED",
            },
            {
                "session_id": "SESSION-2026-01-20-WORK",
                "start_time": "2026-01-20T09:00:00",
                "end_time": "2026-01-20T11:00:00",
                "agent_id": "code-agent",
                "description": "Real session",
                "status": "COMPLETED",
            },
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1  # Only first session needs repair
        repair = plan[0]
        assert repair["session_id"] == "SESSION-2026-01-15-TEST"
        assert "timestamp" in repair["fixes"]
        assert "agent_id" in repair["fixes"]

    def test_apply_repair_returns_summary(self):
        """Apply repair plan returns summary of changes."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-15-TEST",
            "fixes": {
                "timestamp": {"start": "2026-01-15T09:00:00", "end": "2026-01-15T13:00:00"},
                "agent_id": "code-agent",
            },
        }
        # Mock the update_session service
        with patch("governance.services.sessions.update_session") as mock_update:
            mock_update.return_value = {"session_id": "SESSION-2026-01-15-TEST"}
            result = apply_repair(plan_item, dry_run=False)
            assert result["applied"]
            assert mock_update.called

    def test_dry_run_does_not_mutate(self):
        """Dry run should not call update_session."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "S1",
            "fixes": {"agent_id": "code-agent"},
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=True)
            assert not result["applied"]
            assert not mock_update.called

    def test_is_backfilled_session(self):
        """Detect backfilled sessions by description or pattern."""
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"description": "Backfilled from evidence file"})
        assert is_backfilled_session({"agent_id": "agent-1-test"})
        assert not is_backfilled_session({"description": "Normal session", "agent_id": "code-agent"})
