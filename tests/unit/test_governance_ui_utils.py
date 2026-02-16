"""
Unit tests for Governance UI Utilities.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/utils.py module.
Tests: extract_items_from_response, extract_pagination_from_response,
       compute_session_metrics, compute_session_duration,
       compute_timeline_data, compute_pivot_data,
       format_timestamp, format_timestamps_in_list.
"""

from datetime import datetime, timedelta

import pytest

from agent.governance_ui.utils import (
    extract_items_from_response,
    extract_pagination_from_response,
    compute_session_metrics,
    compute_session_duration,
    compute_timeline_data,
    compute_pivot_data,
    format_timestamp,
    format_timestamps_in_list,
)


# ── extract_items_from_response ───────────────────────────────


class TestExtractItems:
    def test_dict_with_items(self):
        data = {"items": [1, 2, 3], "pagination": {}}
        assert extract_items_from_response(data) == [1, 2, 3]

    def test_plain_list(self):
        assert extract_items_from_response([1, 2]) == [1, 2]

    def test_dict_without_items(self):
        assert extract_items_from_response({"other": "data"}) == []

    def test_string_input(self):
        assert extract_items_from_response("string") == []


# ── extract_pagination_from_response ──────────────────────────


class TestExtractPagination:
    def test_with_pagination(self):
        data = {"items": [], "pagination": {"total": 5, "offset": 0}}
        result = extract_pagination_from_response(data)
        assert result["total"] == 5

    def test_without_pagination(self):
        assert extract_pagination_from_response({"items": []}) == {}

    def test_list_input(self):
        assert extract_pagination_from_response([1, 2]) == {}


# ── compute_session_metrics ───────────────────────────────────


class TestComputeSessionMetrics:
    def test_hours_format(self):
        sessions = [{"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T12:00:00"}]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "2h"

    def test_minutes_format(self):
        sessions = [{"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T10:30:00"}]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "30m"

    def test_zero_duration(self):
        sessions = []
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"

    def test_avg_tasks(self):
        sessions = [
            {"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T11:00:00", "tasks_completed": 4},
            {"start_time": "2026-02-11T12:00:00", "end_time": "2026-02-11T13:00:00", "tasks_completed": 6},
        ]
        result = compute_session_metrics(sessions)
        assert result["avg_tasks"] == 5.0

    def test_invalid_timestamps_ignored(self):
        sessions = [{"start_time": "bad", "end_time": "data"}]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "0h"

    def test_non_numeric_tasks(self):
        sessions = [{"tasks_completed": "not a number"}]
        result = compute_session_metrics(sessions)
        assert result["avg_tasks"] == 0


# ── compute_session_duration ──────────────────────────────────


class TestComputeSessionDuration:
    def test_hours_and_minutes(self):
        result = compute_session_duration("2026-02-11T10:00:00", "2026-02-11T12:30:00")
        assert result == "2h 30m"

    def test_minutes_only(self):
        result = compute_session_duration("2026-02-11T10:00:00", "2026-02-11T10:45:00")
        assert result == "45m"

    def test_less_than_one_minute(self):
        result = compute_session_duration("2026-02-11T10:00:00", "2026-02-11T10:00:30")
        assert result == "<1m"

    def test_no_start(self):
        assert compute_session_duration("", "2026-02-11T10:00:00") == ""

    def test_no_end_ongoing(self):
        assert compute_session_duration("2026-02-11T10:00:00", "") == "ongoing"

    def test_z_suffix_handled(self):
        result = compute_session_duration("2026-02-11T10:00:00Z", "2026-02-11T11:00:00Z")
        assert result == "1h 0m"

    def test_invalid_timestamps(self):
        assert compute_session_duration("bad", "data") == ""

    def test_negative_duration_uses_absolute(self):
        """End time before start time uses abs() to compute valid duration."""
        result = compute_session_duration(
            "2026-02-14T00:07:18", "2026-02-13T22:09:29")
        assert result != "invalid"
        assert "m" in result  # Should be "1h 57m"

    def test_absurd_duration_capped(self):
        """>24h duration returns '>24h'."""
        result = compute_session_duration(
            "2026-01-19T02:07:03", "2026-02-01T20:37:30")
        assert result == ">24h"

    def test_exactly_24h(self):
        """24h exactly is still valid (not capped)."""
        result = compute_session_duration(
            "2026-02-11T00:00:00", "2026-02-12T00:00:00")
        assert result == "24h 0m"

    def test_estimated_duration_detected(self):
        """Repair-generated 09:00→13:00 shows '~4h (est)'."""
        result = compute_session_duration(
            "2026-02-11T09:00:00", "2026-02-11T13:00:00")
        assert result == "~4h (est)"

    def test_real_09_start_not_flagged(self):
        """Real session starting at 09:00 but NOT ending at 13:00 is normal."""
        result = compute_session_duration(
            "2026-02-11T09:00:00", "2026-02-11T11:30:00")
        assert result == "2h 30m"

    def test_real_13_end_not_flagged(self):
        """Real session ending at 13:00 but NOT starting at 09:00 is normal."""
        result = compute_session_duration(
            "2026-02-11T10:00:00", "2026-02-11T13:00:00")
        assert result == "3h 0m"


class TestComputeSessionMetricsOutliers:
    """Tests for outlier exclusion in compute_session_metrics()."""

    def test_negative_duration_excluded(self):
        """Negative duration sessions don't inflate total."""
        sessions = [
            {"start_time": "2026-02-14T00:07:18", "end_time": "2026-02-13T22:09:29"},
            {"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T12:00:00"},
        ]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "2h"

    def test_absurd_duration_excluded(self):
        """>24h sessions don't inflate total."""
        sessions = [
            {"start_time": "2026-01-19T02:07:03", "end_time": "2026-02-01T20:37:30"},
            {"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T11:00:00"},
        ]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "1h"

    def test_estimated_duration_excluded(self):
        """Repair-generated 09:00→13:00 sessions excluded from total."""
        sessions = [
            {"start_time": "2026-02-11T09:00:00", "end_time": "2026-02-11T13:00:00"},
            {"start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T12:00:00"},
        ]
        result = compute_session_metrics(sessions)
        assert result["duration"] == "2h"  # only the real session counted


class TestComputePivotDataOutliers:
    """Tests for outlier exclusion in compute_pivot_data()."""

    def test_negative_duration_excluded_from_avg(self):
        sessions = [
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-14T00:07:18", "end_time": "2026-02-13T22:09:29"},
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T10:30:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert "30m" in result[0]["avg_duration"]

    def test_absurd_duration_excluded_from_avg(self):
        sessions = [
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-01-01T00:00:00", "end_time": "2026-01-15T00:00:00"},
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T11:00:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert result[0]["avg_duration"] == "1h 0m"

    def test_estimated_duration_excluded_from_avg(self):
        """Repair-generated 09:00→13:00 excluded from pivot avg."""
        sessions = [
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-11T09:00:00", "end_time": "2026-02-11T13:00:00"},
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T10:30:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert "30m" in result[0]["avg_duration"]


# ── compute_timeline_data ─────────────────────────────────────


class TestComputeTimelineData:
    def test_returns_14_days(self):
        values, labels = compute_timeline_data([])
        assert len(values) == 14
        assert len(labels) == 14

    def test_counts_sessions(self):
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        sessions = [
            {"start_time": today},
            {"start_time": today},
        ]
        values, labels = compute_timeline_data(sessions)
        assert values[-1] == 2  # today is the last element

    def test_labels_mm_dd_format(self):
        _, labels = compute_timeline_data([])
        for label in labels:
            assert len(label) == 5  # MM-DD

    def test_plotly_layout_has_axis_titles(self):
        """Plotly timeline layout includes chart title and Y-axis label."""
        from agent.governance_ui.views.sessions.timeline import (
            compute_timeline_plotly_data,
        )
        sessions = [{"start_time": "2026-02-11T10:00:00", "status": "COMPLETED"}]
        result = compute_timeline_plotly_data(sessions)
        layout = result["layout"]
        assert "title" in layout
        assert layout["title"]["text"] == "Sessions per Day"
        assert "title" in layout["yaxis"]
        assert layout["yaxis"]["title"]["text"] == "Count"


# ── compute_pivot_data ────────────────────────────────────────


class TestComputePivotData:
    def test_groups_by_agent(self):
        sessions = [
            {"agent_id": "code-agent", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T11:00:00"},
            {"agent_id": "code-agent", "status": "ACTIVE",
             "start_time": "2026-02-11T12:00:00", "end_time": ""},
            {"agent_id": "research-agent", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T10:30:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert len(result) == 2
        code = next(r for r in result if r["group"] == "code-agent")
        assert code["count"] == 2
        assert code["completed"] == 1
        assert code["active"] == 1

    def test_missing_group_key(self):
        sessions = [{"status": "COMPLETED"}]
        result = compute_pivot_data(sessions, "agent_id")
        assert result[0]["group"] == "(none)"

    def test_avg_duration(self):
        sessions = [
            {"agent_id": "a", "status": "COMPLETED",
             "start_time": "2026-02-11T10:00:00", "end_time": "2026-02-11T10:30:00"},
        ]
        result = compute_pivot_data(sessions, "agent_id")
        assert "30m" in result[0]["avg_duration"]


# ── format_timestamp ──────────────────────────────────────────


class TestFormatTimestamp:
    def test_iso_with_nanoseconds(self):
        result = format_timestamp("2026-01-19T04:06:50.000000000")
        assert result == "2026-01-19 04:06"

    def test_iso_with_z(self):
        result = format_timestamp("2026-02-11T10:30:00Z")
        assert result == "2026-02-11 10:30"

    def test_plain_iso(self):
        result = format_timestamp("2026-02-11T10:30:00")
        assert result == "2026-02-11 10:30"

    def test_empty_string(self):
        assert format_timestamp("") == ""

    def test_none_input(self):
        assert format_timestamp(None) == ""

    def test_non_string(self):
        # BUG-UI-FORMAT-001: Non-string inputs now return "" to prevent AttributeError
        assert format_timestamp(42) == ""


# ── format_timestamps_in_list ─────────────────────────────────


class TestFormatTimestampsInList:
    def test_formats_specified_fields(self):
        items = [{"start_time": "2026-02-11T10:00:00", "name": "test"}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert result[0]["start_time"] == "2026-02-11 10:00"
        assert result[0]["name"] == "test"

    def test_skips_missing_fields(self):
        items = [{"name": "test"}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert "start_time" not in result[0]

    def test_skips_none_values(self):
        items = [{"start_time": None}]
        result = format_timestamps_in_list(items, ["start_time"])
        assert result[0]["start_time"] is None
