"""
Unit tests for Session Data Repair Service.

Per GAP-GOVSESS-TIMESTAMP/AGENT/DURATION: Tests for session_repair.py
data quality functions.
"""

import pytest
from datetime import datetime

from governance.services.session_repair import (
    parse_session_date,
    generate_timestamps,
    detect_identical_timestamps,
    detect_missing_agent,
    assign_default_agent,
    detect_negative_durations,
    detect_unrealistic_durations,
    cap_duration,
    is_backfilled_session,
    build_repair_plan,
    apply_repair,
    _DEFAULT_DURATION_HOURS,
    _MAX_DURATION_HOURS,
    _SESSION_DATE_PATTERN,
)


# ---------------------------------------------------------------------------
# parse_session_date
# ---------------------------------------------------------------------------
class TestParseSessionDate:
    """Tests for parse_session_date()."""

    def test_standard_format(self):
        assert parse_session_date("SESSION-2026-01-15-TOPIC") == "2026-01-15"

    def test_numbered_format(self):
        assert parse_session_date("SESSION-2024-12-26-001") == "2024-12-26"

    def test_no_match(self):
        assert parse_session_date("UNKNOWN-ID") is None

    def test_partial_date(self):
        assert parse_session_date("SESSION-2026-13") is None  # incomplete

    def test_embedded_date(self):
        assert parse_session_date("PREFIX-SESSION-2026-03-05-SUFFIX") == "2026-03-05"


# ---------------------------------------------------------------------------
# generate_timestamps
# ---------------------------------------------------------------------------
class TestGenerateTimestamps:
    """Tests for generate_timestamps()."""

    def test_returns_tuple(self):
        start, end = generate_timestamps("2026-01-15")
        assert isinstance(start, str)
        assert isinstance(end, str)

    def test_start_at_nine(self):
        start, _ = generate_timestamps("2026-01-15")
        assert "T09:00:00" in start

    def test_duration_default(self):
        start, end = generate_timestamps("2026-01-15")
        st = datetime.fromisoformat(start)
        et = datetime.fromisoformat(end)
        hours = (et - st).total_seconds() / 3600
        assert hours == _DEFAULT_DURATION_HOURS

    def test_preserves_date(self):
        start, _ = generate_timestamps("2026-07-20")
        assert start.startswith("2026-07-20")


# ---------------------------------------------------------------------------
# detect_identical_timestamps
# ---------------------------------------------------------------------------
class TestDetectIdenticalTimestamps:
    """Tests for detect_identical_timestamps()."""

    def test_no_duplicates(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00", "end_time": "2026-01-01T13:00"},
            {"session_id": "S-2", "start_time": "2026-01-02T09:00", "end_time": "2026-01-02T13:00"},
        ]
        assert detect_identical_timestamps(sessions) == []

    def test_detects_duplicates(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00", "end_time": "2026-01-01T13:00"},
            {"session_id": "S-2", "start_time": "2026-01-01T09:00", "end_time": "2026-01-01T13:00"},
            {"session_id": "S-3", "start_time": "2026-01-02T09:00", "end_time": "2026-01-02T13:00"},
        ]
        flagged = detect_identical_timestamps(sessions)
        assert "S-1" in flagged
        assert "S-2" in flagged
        assert "S-3" not in flagged

    def test_empty_list(self):
        assert detect_identical_timestamps([]) == []

    def test_missing_timestamps(self):
        sessions = [
            {"session_id": "S-1"},
            {"session_id": "S-2", "start_time": "", "end_time": ""},
        ]
        assert detect_identical_timestamps(sessions) == []


# ---------------------------------------------------------------------------
# detect_missing_agent
# ---------------------------------------------------------------------------
class TestDetectMissingAgent:
    """Tests for detect_missing_agent()."""

    def test_no_missing(self):
        sessions = [
            {"session_id": "S-1", "agent_id": "code-agent"},
            {"session_id": "S-2", "agent_id": "rules-curator"},
        ]
        assert detect_missing_agent(sessions) == []

    def test_detects_missing(self):
        sessions = [
            {"session_id": "S-1", "agent_id": "code-agent"},
            {"session_id": "S-2"},
            {"session_id": "S-3", "agent_id": ""},
            {"session_id": "S-4", "agent_id": None},
        ]
        flagged = detect_missing_agent(sessions)
        assert "S-2" in flagged
        assert "S-3" in flagged
        assert "S-4" in flagged
        assert "S-1" not in flagged

    def test_empty_list(self):
        assert detect_missing_agent([]) == []


# ---------------------------------------------------------------------------
# assign_default_agent
# ---------------------------------------------------------------------------
class TestAssignDefaultAgent:
    """Tests for assign_default_agent()."""

    def test_assigns_when_missing(self):
        session = {"session_id": "S-1"}
        result = assign_default_agent(session)
        assert result["agent_id"] == "code-agent"

    def test_assigns_when_empty_string(self):
        session = {"session_id": "S-1", "agent_id": ""}
        result = assign_default_agent(session)
        assert result["agent_id"] == "code-agent"

    def test_preserves_existing(self):
        session = {"session_id": "S-1", "agent_id": "rules-curator"}
        result = assign_default_agent(session)
        assert result["agent_id"] == "rules-curator"

    def test_does_not_mutate_original(self):
        session = {"session_id": "S-1"}
        result = assign_default_agent(session)
        assert "agent_id" not in session
        assert result["agent_id"] == "code-agent"


# ---------------------------------------------------------------------------
# detect_negative_durations
# ---------------------------------------------------------------------------
class TestDetectNegativeDurations:
    """Tests for detect_negative_durations()."""

    def test_normal_sessions_not_flagged(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
        ]
        assert detect_negative_durations(sessions) == []

    def test_detects_negative_duration(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-02-14T00:07:18", "end_time": "2026-02-13T22:09:29"},
        ]
        flagged = detect_negative_durations(sessions)
        assert "S-1" in flagged

    def test_missing_timestamps_skipped(self):
        sessions = [{"session_id": "S-1", "start_time": "2026-01-01T09:00:00"}]
        assert detect_negative_durations(sessions) == []

    def test_equal_timestamps_not_flagged(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T09:00:00"},
        ]
        assert detect_negative_durations(sessions) == []


# ---------------------------------------------------------------------------
# detect_unrealistic_durations
# ---------------------------------------------------------------------------
class TestDetectUnrealisticDurations:
    """Tests for detect_unrealistic_durations()."""

    def test_normal_durations(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
        ]
        assert detect_unrealistic_durations(sessions) == []

    def test_detects_long_duration(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-03T09:00:00"},
        ]
        flagged = detect_unrealistic_durations(sessions)
        assert "S-1" in flagged

    def test_custom_max_hours(self):
        sessions = [
            {"session_id": "S-1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T15:00:00"},
        ]
        # 6 hours, default max is 24 — should pass
        assert detect_unrealistic_durations(sessions) == []
        # Custom max of 4 — should flag
        flagged = detect_unrealistic_durations(sessions, max_hours=4)
        assert "S-1" in flagged

    def test_missing_timestamps_skipped(self):
        sessions = [{"session_id": "S-1"}]
        assert detect_unrealistic_durations(sessions) == []

    def test_invalid_timestamps_skipped(self):
        sessions = [
            {"session_id": "S-1", "start_time": "not-a-date", "end_time": "also-not"},
        ]
        assert detect_unrealistic_durations(sessions) == []


# ---------------------------------------------------------------------------
# cap_duration
# ---------------------------------------------------------------------------
class TestCapDuration:
    """Tests for cap_duration()."""

    def test_caps_long_duration(self):
        session = {
            "session_id": "S-1",
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-03T09:00:00",  # 48 hours
        }
        result = cap_duration(session, max_hours=8)
        et = datetime.fromisoformat(result["end_time"])
        st = datetime.fromisoformat(result["start_time"])
        assert (et - st).total_seconds() / 3600 == 8

    def test_short_duration_unchanged(self):
        session = {
            "session_id": "S-1",
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-01T13:00:00",  # 4 hours
        }
        result = cap_duration(session, max_hours=8)
        assert result["end_time"] == "2026-01-01T13:00:00"

    def test_missing_start_unchanged(self):
        session = {"session_id": "S-1", "end_time": "2026-01-01T13:00:00"}
        result = cap_duration(session)
        assert result is session

    def test_missing_end_unchanged(self):
        session = {"session_id": "S-1", "start_time": "2026-01-01T09:00:00"}
        result = cap_duration(session)
        assert result is session

    def test_does_not_mutate_original(self):
        session = {
            "session_id": "S-1",
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-03T09:00:00",
        }
        original_end = session["end_time"]
        cap_duration(session, max_hours=8)
        assert session["end_time"] == original_end


# ---------------------------------------------------------------------------
# is_backfilled_session
# ---------------------------------------------------------------------------
class TestIsBackfilledSession:
    """Tests for is_backfilled_session()."""

    def test_backfilled_from_evidence(self):
        session = {"description": "Backfilled from evidence file"}
        assert is_backfilled_session(session) is True

    def test_backfilled_case_insensitive(self):
        session = {"description": "BACKFILLED FROM EVIDENCE file"}
        assert is_backfilled_session(session) is True

    def test_agent_test_suffix(self):
        session = {"agent_id": "curator-test"}
        assert is_backfilled_session(session) is True

    def test_normal_session(self):
        session = {"description": "Regular session", "agent_id": "code-agent"}
        assert is_backfilled_session(session) is False

    def test_empty_session(self):
        session = {}
        assert is_backfilled_session(session) is False


# ---------------------------------------------------------------------------
# build_repair_plan
# ---------------------------------------------------------------------------
class TestBuildRepairPlan:
    """Tests for build_repair_plan()."""

    def test_empty_sessions(self):
        assert build_repair_plan([]) == []

    def test_healthy_sessions_no_plan(self):
        sessions = [
            {"session_id": "SESSION-2026-01-15-TOPIC", "agent_id": "code-agent",
             "start_time": "2026-01-15T09:00:00", "end_time": "2026-01-15T13:00:00",
             "description": "Normal work"},
        ]
        plan = build_repair_plan(sessions)
        assert plan == []

    def test_missing_agent_creates_fix(self):
        sessions = [
            {"session_id": "SESSION-2026-01-15-TOPIC",
             "start_time": "2026-01-15T09:00:00", "end_time": "2026-01-15T13:00:00",
             "description": "Normal work"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert plan[0]["fixes"]["agent_id"] == "code-agent"

    def test_backfilled_gets_timestamp_fix(self):
        sessions = [
            {"session_id": "SESSION-2026-01-15-TOPIC", "agent_id": "code-agent",
             "start_time": "2026-01-15T09:00:00", "end_time": "2026-01-15T13:00:00",
             "description": "Backfilled from evidence file"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "timestamp" in plan[0]["fixes"]

    def test_unrealistic_duration_fix(self):
        sessions = [
            {"session_id": "SESSION-2026-01-15-TOPIC", "agent_id": "code-agent",
             "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-10T09:00:00",
             "description": "Normal"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "duration" in plan[0]["fixes"]

    def test_multiple_fixes_combined(self):
        """Backfilled + missing agent: timestamp fix subsumes duration fix."""
        sessions = [
            {"session_id": "SESSION-2026-01-15-TOPIC",
             "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-10T09:00:00",
             "description": "Backfilled from evidence file"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        fixes = plan[0]["fixes"]
        assert "agent_id" in fixes
        assert "timestamp" in fixes
        # duration fix skipped because timestamp fix already regenerates end_time

    def test_negative_duration_swaps_timestamps(self):
        """Negative duration sessions get start/end swapped if reasonable."""
        sessions = [
            {"session_id": "SESSION-2026-02-14-CHAT-TEST", "agent_id": "code-agent",
             "start_time": "2026-02-14T00:07:18", "end_time": "2026-02-13T22:09:29",
             "description": "Test"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "timestamp" in plan[0]["fixes"]
        ts = plan[0]["fixes"]["timestamp"]
        # Swapped: end becomes start, start becomes end
        assert ts["start"] == "2026-02-13T22:09:29"
        assert ts["end"] == "2026-02-14T00:07:18"

    def test_negative_duration_regenerates_if_swap_absurd(self):
        """If swapping produces >24h, regenerate from session ID date."""
        sessions = [
            {"session_id": "SESSION-2026-02-14-TOPIC", "agent_id": "code-agent",
             "start_time": "2026-02-14T00:00:00", "end_time": "2026-01-01T00:00:00",
             "description": "Very negative"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        ts = plan[0]["fixes"]["timestamp"]
        # Should regenerate from date, not swap
        assert ts["start"] == "2026-02-14T09:00:00"


# ---------------------------------------------------------------------------
# apply_repair
# ---------------------------------------------------------------------------
class TestApplyRepair:
    """Tests for apply_repair()."""

    def test_dry_run_no_update(self):
        item = {"session_id": "S-1", "fixes": {"agent_id": "code-agent"}}
        result = apply_repair(item, dry_run=True)
        assert result["applied"] is False
        assert result["dry_run"] is True
        assert result["fixes"] == {"agent_id": "code-agent"}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Tests for module constants."""

    def test_default_duration(self):
        assert _DEFAULT_DURATION_HOURS == 4

    def test_max_duration(self):
        assert _MAX_DURATION_HOURS == 24

    def test_session_date_pattern(self):
        match = _SESSION_DATE_PATTERN.search("SESSION-2026-05-20-TOPIC")
        assert match is not None
        assert match.group(1) == "2026-05-20"

    def test_pattern_no_match(self):
        match = _SESSION_DATE_PATTERN.search("RANDOM-TEXT")
        assert match is None
