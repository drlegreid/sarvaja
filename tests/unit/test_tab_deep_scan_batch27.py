"""
Unit tests for Tab Deep Scan Batch 27 — Utils type safety + edge cases.

Covers: BUG-UI-FORMAT-001 (format_timestamp type coercion),
compute_session_duration edge cases, compute_session_metrics safety.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

from agent.governance_ui.utils import (
    format_timestamp,
    format_timestamps_in_list,
    compute_session_duration,
    compute_session_metrics,
    compute_timeline_data,
    compute_pivot_data,
    extract_items_from_response,
)


# ── BUG-UI-FORMAT-001: format_timestamp type safety ───────────────────


class TestFormatTimestampTypeSafety:
    """format_timestamp must always return a string."""

    def test_returns_string_for_none(self):
        assert format_timestamp(None) == ""

    def test_returns_string_for_empty(self):
        assert format_timestamp("") == ""

    def test_returns_string_for_integer(self):
        """Integer timestamps must return empty string, not the integer."""
        result = format_timestamp(1705676400)
        assert isinstance(result, str)
        assert result == ""

    def test_returns_string_for_float(self):
        result = format_timestamp(1705676400.123)
        assert isinstance(result, str)
        assert result == ""

    def test_returns_string_for_bool(self):
        result = format_timestamp(True)
        assert isinstance(result, str)

    def test_returns_string_for_list(self):
        result = format_timestamp([])
        assert isinstance(result, str)
        assert result == ""

    def test_formats_valid_iso(self):
        result = format_timestamp("2026-01-15T10:30:45")
        assert isinstance(result, str)
        assert result == "2026-01-15 10:30"

    def test_formats_iso_with_nanoseconds(self):
        result = format_timestamp("2026-01-15T10:30:45.123456789")
        assert isinstance(result, str)
        assert "2026-01-15" in result
        assert "10:30" in result

    def test_formats_iso_with_z(self):
        result = format_timestamp("2026-01-15T10:30:45Z")
        assert isinstance(result, str)
        assert "2026-01-15" in result


# ── format_timestamps_in_list safety ──────────────────────────────────


class TestFormatTimestampsInList:
    """format_timestamps_in_list must handle edge cases."""

    def test_skips_missing_fields(self):
        items = [{"name": "test"}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert result == [{"name": "test"}]

    def test_skips_falsy_values(self):
        items = [{"start_time": None}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert result[0]["start_time"] is None

    def test_formats_valid_items(self):
        items = [{"start_time": "2026-01-15T10:30:45"}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert result[0]["start_time"] == "2026-01-15 10:30"


# ── compute_session_duration edge cases ───────────────────────────────


class TestComputeSessionDurationEdgeCases:
    """compute_session_duration must handle all edge cases."""

    def test_empty_start_returns_empty(self):
        assert compute_session_duration("", "2026-01-15T10:30:00") == ""

    def test_none_start_returns_empty(self):
        assert compute_session_duration(None, "2026-01-15T10:30:00") == ""

    def test_empty_end_returns_ongoing(self):
        assert compute_session_duration("2026-01-15T10:30:00", "") == "ongoing"

    def test_none_end_returns_ongoing(self):
        assert compute_session_duration("2026-01-15T10:30:00", None) == "ongoing"

    def test_negative_delta_uses_abs(self):
        """Reversed timestamps should still produce a duration."""
        result = compute_session_duration(
            "2026-01-15T14:00:00", "2026-01-15T10:00:00"
        )
        assert result != ""
        assert "4h" in result

    def test_short_duration_shows_minutes(self):
        result = compute_session_duration(
            "2026-01-15T10:00:00", "2026-01-15T10:45:00"
        )
        assert "45m" in result

    def test_sub_minute_shows_less_than_1m(self):
        result = compute_session_duration(
            "2026-01-15T10:00:00", "2026-01-15T10:00:30"
        )
        assert result == "<1m"

    def test_over_24h_shows_marker(self):
        result = compute_session_duration(
            "2026-01-13T10:00:00", "2026-01-15T10:00:00"
        )
        assert result == ">24h"

    def test_estimated_duration_shows_est(self):
        result = compute_session_duration(
            "2026-01-15T09:00:00", "2026-01-15T13:00:00"
        )
        assert "est" in result

    def test_invalid_format_returns_empty(self):
        result = compute_session_duration("not-a-date", "also-not")
        assert result == ""

    def test_with_z_suffix(self):
        result = compute_session_duration(
            "2026-01-15T10:00:00Z", "2026-01-15T12:30:00Z"
        )
        assert "2h" in result


# ── compute_session_metrics edge cases ────────────────────────────────


class TestComputeSessionMetricsEdgeCases:
    """compute_session_metrics must handle edge cases."""

    def test_empty_list(self):
        result = compute_session_metrics([])
        assert result["duration"] == "0h"
        assert result["avg_tasks"] == 0

    def test_sessions_without_timestamps(self):
        sessions = [{"session_id": "S-1"}, {"session_id": "S-2"}]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"

    def test_non_numeric_tasks(self):
        """Non-numeric tasks_completed should be skipped."""
        sessions = [{"tasks_completed": "invalid"}]
        result = compute_session_metrics(sessions)
        assert result["avg_tasks"] == 0

    def test_skips_estimated_durations(self):
        """Repair-generated timestamps should be excluded."""
        sessions = [{
            "start_time": "2026-01-15T09:00:00",
            "end_time": "2026-01-15T13:00:00",
        }]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"

    def test_skips_negative_durations(self):
        """Sessions with end < start should be skipped (0 < hours check)."""
        sessions = [{
            "start_time": "2026-01-15T14:00:00",
            "end_time": "2026-01-15T10:00:00",
        }]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"


# ── compute_timeline_data edge cases ──────────────────────────────────


class TestComputeTimelineDataEdgeCases:

    def test_empty_list_returns_14_days(self):
        values, labels = compute_timeline_data([])
        assert len(values) == 14
        assert len(labels) == 14
        assert all(v == 0 for v in values)

    def test_invalid_timestamps_skipped(self):
        sessions = [{"start_time": "not-a-date"}]
        values, labels = compute_timeline_data(sessions)
        assert len(values) == 14


# ── compute_pivot_data edge cases ─────────────────────────────────────


class TestComputePivotDataEdgeCases:

    def test_empty_list(self):
        result = compute_pivot_data([])
        assert result == []

    def test_missing_group_key(self):
        """Sessions without the group_by field should go to '(none)'."""
        sessions = [{"session_id": "S-1"}]
        result = compute_pivot_data(sessions, "agent_id")
        assert len(result) == 1
        assert result[0]["group"] == "(none)"

    def test_skips_estimated_durations_in_pivot(self):
        sessions = [{
            "agent_id": "a1",
            "start_time": "2026-01-15T09:00:00",
            "end_time": "2026-01-15T13:00:00",
        }]
        result = compute_pivot_data(sessions, "agent_id")
        assert result[0]["avg_duration"] == "0m"


# ── extract_items_from_response edge cases ────────────────────────────


class TestExtractItemsEdgeCases:

    def test_dict_with_items(self):
        assert extract_items_from_response({"items": [1, 2]}) == [1, 2]

    def test_plain_list(self):
        assert extract_items_from_response([1, 2]) == [1, 2]

    def test_dict_without_items(self):
        assert extract_items_from_response({"other": "data"}) == []

    def test_none_returns_empty(self):
        assert extract_items_from_response(None) == []

    def test_string_returns_empty(self):
        assert extract_items_from_response("not a list") == []
