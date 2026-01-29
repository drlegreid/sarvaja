"""
TDD Test Spec: Session Metrics Temporal Queries
================================================
Per GAP-SESSION-METRICS-TEMPORAL: Temporal queries ("what was I doing at X?").

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_temporal.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temporal_log_dir(tmp_path):
    """Log with entries spanning multiple days and sessions."""
    entries = [
        # Day 1, Session A: morning work
        {"type": "user", "timestamp": "2026-01-27T09:00:00Z",
         "sessionId": "sess-A", "gitBranch": "main",
         "message": {"role": "user", "content": "start work"}},
        {"type": "assistant", "timestamp": "2026-01-27T09:05:00Z",
         "sessionId": "sess-A", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Fixing auth bug in login module."},
                         {"type": "tool_use", "id": "t1", "name": "Read", "input": {}},
                     ]}},
        {"type": "assistant", "timestamp": "2026-01-27T09:30:00Z",
         "sessionId": "sess-A", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Applied fix to authentication."},
                     ]}},

        # Day 1, Session B: afternoon (gap > 30min)
        {"type": "user", "timestamp": "2026-01-27T14:00:00Z",
         "sessionId": "sess-B", "gitBranch": "feature/dashboard",
         "message": {"role": "user", "content": "dashboard work"}},
        {"type": "assistant", "timestamp": "2026-01-27T14:10:00Z",
         "sessionId": "sess-B", "gitBranch": "feature/dashboard",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Building dashboard charts."},
                         {"type": "tool_use", "id": "t2", "name": "Edit", "input": {}},
                     ]}},

        # Day 2, Session C: all day
        {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
         "sessionId": "sess-C", "gitBranch": "main",
         "message": {"role": "user", "content": "testing"}},
        {"type": "assistant", "timestamp": "2026-01-28T10:15:00Z",
         "sessionId": "sess-C", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Running test suite and fixing failures."},
                         {"type": "tool_use", "id": "t3", "name": "Bash", "input": {}},
                     ]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:45:00Z",
         "sessionId": "sess-C", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "DECISION: Refactoring test helpers."},
                     ]}},

        # Day 3
        {"type": "user", "timestamp": "2026-01-29T16:00:00Z",
         "sessionId": "sess-D", "gitBranch": "feature/metrics",
         "message": {"role": "user", "content": "metrics work"}},
        {"type": "assistant", "timestamp": "2026-01-29T16:30:00Z",
         "sessionId": "sess-D", "gitBranch": "feature/metrics",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Implementing session metrics module."},
                         {"type": "tool_use", "id": "t4", "name": "mcp__gov-core__health_check",
                          "input": {}},
                     ]}},
    ]
    log_file = tmp_path / "temporal-test.jsonl"
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return tmp_path


@pytest.fixture
def parsed_entries(temporal_log_dir):
    """Parse entries using extended parser."""
    from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
    files = discover_log_files(temporal_log_dir, include_agents=False)
    return [e for f in files for e in parse_log_file_extended(f)]


# ---------------------------------------------------------------------------
# Tests: Query by time point
# ---------------------------------------------------------------------------

class TestQueryAtTime:
    """Test querying what was happening at a specific time."""

    def test_query_at_time_finds_session(self, parsed_entries):
        """Query at 09:15 on 2026-01-27 finds the auth session."""
        from governance.session_metrics.temporal import query_at_time
        target = datetime(2026, 1, 27, 9, 15, tzinfo=timezone.utc)
        result = query_at_time(parsed_entries, target, window_minutes=30)
        assert result is not None
        assert len(result["entries"]) > 0

    def test_query_at_time_returns_nearby_entries(self, parsed_entries):
        """Query returns entries within the time window."""
        from governance.session_metrics.temporal import query_at_time
        target = datetime(2026, 1, 27, 9, 15, tzinfo=timezone.utc)
        result = query_at_time(parsed_entries, target, window_minutes=30)
        for entry in result["entries"]:
            assert "2026-01-27" in entry["timestamp"]

    def test_query_at_time_includes_text(self, parsed_entries):
        """Query result entries include text_content."""
        from governance.session_metrics.temporal import query_at_time
        target = datetime(2026, 1, 27, 9, 15, tzinfo=timezone.utc)
        result = query_at_time(parsed_entries, target, window_minutes=30)
        texts = [e.get("text_content") for e in result["entries"] if e.get("text_content")]
        assert len(texts) > 0

    def test_query_at_time_no_match(self, parsed_entries):
        """Query at a time with no entries returns empty."""
        from governance.session_metrics.temporal import query_at_time
        target = datetime(2026, 1, 25, 3, 0, tzinfo=timezone.utc)
        result = query_at_time(parsed_entries, target, window_minutes=30)
        assert len(result["entries"]) == 0

    def test_query_at_time_has_summary(self, parsed_entries):
        """Query result includes a summary string."""
        from governance.session_metrics.temporal import query_at_time
        target = datetime(2026, 1, 27, 9, 15, tzinfo=timezone.utc)
        result = query_at_time(parsed_entries, target, window_minutes=30)
        assert "summary" in result
        assert isinstance(result["summary"], str)


# ---------------------------------------------------------------------------
# Tests: Query by date range
# ---------------------------------------------------------------------------

class TestQueryDateRange:
    """Test querying entries within a date range."""

    def test_range_single_day(self, parsed_entries):
        """Query for 2026-01-27 returns entries from that day only."""
        from governance.session_metrics.temporal import query_date_range
        start = datetime(2026, 1, 27, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 27, 23, 59, 59, tzinfo=timezone.utc)
        results = query_date_range(parsed_entries, start, end)
        assert len(results) > 0
        for entry in results:
            assert "2026-01-27" in entry["timestamp"]

    def test_range_multi_day(self, parsed_entries):
        """Query for 2026-01-27 to 2026-01-28 returns both days."""
        from governance.session_metrics.temporal import query_date_range
        start = datetime(2026, 1, 27, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 28, 23, 59, 59, tzinfo=timezone.utc)
        results = query_date_range(parsed_entries, start, end)
        dates = set(e["timestamp"][:10] for e in results)
        assert "2026-01-27" in dates
        assert "2026-01-28" in dates

    def test_range_empty(self, parsed_entries):
        """Query for a date range with no entries returns empty."""
        from governance.session_metrics.temporal import query_date_range
        start = datetime(2026, 1, 20, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 20, 23, 59, 59, tzinfo=timezone.utc)
        results = query_date_range(parsed_entries, start, end)
        assert len(results) == 0

    def test_range_entries_are_dicts(self, parsed_entries):
        """Query results are JSON-serializable dicts."""
        from governance.session_metrics.temporal import query_date_range
        import json
        start = datetime(2026, 1, 27, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 29, 23, 59, 59, tzinfo=timezone.utc)
        results = query_date_range(parsed_entries, start, end)
        json.dumps(results)  # Should not raise


# ---------------------------------------------------------------------------
# Tests: Activity timeline
# ---------------------------------------------------------------------------

class TestActivityTimeline:
    """Test generating an activity timeline summary."""

    def test_timeline_returns_list(self, parsed_entries):
        """activity_timeline returns a list of day summaries."""
        from governance.session_metrics.temporal import activity_timeline
        timeline = activity_timeline(parsed_entries)
        assert isinstance(timeline, list)
        assert len(timeline) > 0

    def test_timeline_sorted_by_date(self, parsed_entries):
        """Timeline entries are sorted by date."""
        from governance.session_metrics.temporal import activity_timeline
        timeline = activity_timeline(parsed_entries)
        dates = [t["date"] for t in timeline]
        assert dates == sorted(dates)

    def test_timeline_has_entry_count(self, parsed_entries):
        """Each timeline entry has entry_count."""
        from governance.session_metrics.temporal import activity_timeline
        timeline = activity_timeline(parsed_entries)
        for t in timeline:
            assert "entry_count" in t
            assert t["entry_count"] > 0

    def test_timeline_has_tools_used(self, parsed_entries):
        """Each timeline entry lists tools used that day."""
        from governance.session_metrics.temporal import activity_timeline
        timeline = activity_timeline(parsed_entries)
        # At least one day should have tools
        tools_found = any(len(t.get("tools_used", [])) > 0 for t in timeline)
        assert tools_found

    def test_timeline_has_branches(self, parsed_entries):
        """Each timeline entry lists git branches active that day."""
        from governance.session_metrics.temporal import activity_timeline
        timeline = activity_timeline(parsed_entries)
        branches_found = any(len(t.get("branches", [])) > 0 for t in timeline)
        assert branches_found

    def test_timeline_serializable(self, parsed_entries):
        """Timeline is JSON-serializable."""
        from governance.session_metrics.temporal import activity_timeline
        import json
        timeline = activity_timeline(parsed_entries)
        json.dumps(timeline)  # Should not raise
