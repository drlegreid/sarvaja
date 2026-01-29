"""
TDD Test Spec: Session Metrics Calculator
==========================================
Per SESSION-METRICS-01-v1: Duration calculation, session splitting, aggregation.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_calculator.py -v
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures: parsed entry objects (mock parser output)
# ---------------------------------------------------------------------------

@pytest.fixture
def parsed_entries_two_sessions():
    """Parsed entries spanning 2 sessions on 1 day, separated by >30 min gap."""
    from governance.session_metrics.models import ParsedEntry, ToolUseInfo

    entries = [
        # Session 1: 10:00 - 10:10 (10 min)
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 0, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 1, tzinfo=timezone.utc),
            entry_type="assistant",
            tool_uses=[ToolUseInfo(name="Read", input_summary="{}", is_mcp=False)],
            thinking_chars=150, is_compaction=False,
            model="claude-opus-4-5-20251101",
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 5, tzinfo=timezone.utc),
            entry_type="assistant", tool_uses=[], thinking_chars=0,
            is_compaction=False, model="claude-opus-4-5-20251101",
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 10, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        ),

        # Gap of 50 min (> 30 min threshold) → Session 2
        # Session 2: 11:00 - 11:05 (5 min)
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 11, 0, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 11, 2, tzinfo=timezone.utc),
            entry_type="assistant",
            tool_uses=[
                ToolUseInfo(name="Bash", input_summary="{}", is_mcp=False),
                ToolUseInfo(name="mcp__gov-core__rules_query", input_summary="{}", is_mcp=True),
            ],
            thinking_chars=200, is_compaction=False,
            model="claude-opus-4-5-20251101",
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 11, 5, tzinfo=timezone.utc),
            entry_type="assistant", tool_uses=[], thinking_chars=0,
            is_compaction=False, model="claude-opus-4-5-20251101",
        ),
    ]
    return entries


@pytest.fixture
def parsed_entries_two_days():
    """Parsed entries spanning 2 different days."""
    from governance.session_metrics.models import ParsedEntry, ToolUseInfo

    entries = [
        # Day 1: 2026-01-28
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 0, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 5, tzinfo=timezone.utc),
            entry_type="assistant",
            tool_uses=[ToolUseInfo(name="Edit", input_summary="{}", is_mcp=False)],
            thinking_chars=100, is_compaction=False,
            model="claude-opus-4-5-20251101",
        ),

        # Day 2: 2026-01-29
        ParsedEntry(
            timestamp=datetime(2026, 1, 29, 14, 0, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 29, 14, 3, tzinfo=timezone.utc),
            entry_type="assistant", tool_uses=[], thinking_chars=0,
            is_compaction=True, model=None,
        ),
        ParsedEntry(
            timestamp=datetime(2026, 1, 29, 14, 10, tzinfo=timezone.utc),
            entry_type="assistant",
            tool_uses=[ToolUseInfo(name="Read", input_summary="{}", is_mcp=False)],
            thinking_chars=0, is_compaction=False,
            model="claude-opus-4-5-20251101",
        ),
    ]
    return entries


# ---------------------------------------------------------------------------
# Tests: Session Splitting
# ---------------------------------------------------------------------------

class TestSessionSplitting:
    """Test idle-threshold-based session splitting."""

    def test_splits_on_30min_gap(self, parsed_entries_two_sessions):
        """Entries with >30 min gap are split into separate sessions."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        assert len(sessions) == 2

    def test_single_session_no_gap(self, parsed_entries_two_sessions):
        """With high threshold, all entries stay in one session."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=120)
        assert len(sessions) == 1

    def test_session_has_start_and_end(self, parsed_entries_two_sessions):
        """Each session has first and last timestamp."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        for session in sessions:
            assert session.start_time <= session.end_time

    def test_session_entry_count(self, parsed_entries_two_sessions):
        """Sessions have correct entry counts."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        assert sessions[0].entry_count == 4
        assert sessions[1].entry_count == 3

    def test_empty_entries(self):
        """Empty entry list returns empty session list."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions([], idle_threshold_min=30)
        assert sessions == []

    def test_single_entry(self):
        """Single entry creates one session with 0 duration."""
        from governance.session_metrics.models import ParsedEntry
        from governance.session_metrics.calculator import split_sessions
        entries = [ParsedEntry(
            timestamp=datetime(2026, 1, 28, 10, 0, tzinfo=timezone.utc),
            entry_type="user", tool_uses=[], thinking_chars=0,
            is_compaction=False, model=None,
        )]
        sessions = split_sessions(entries, idle_threshold_min=30)
        assert len(sessions) == 1
        assert sessions[0].active_minutes == 0


# ---------------------------------------------------------------------------
# Tests: Duration Calculation
# ---------------------------------------------------------------------------

class TestDurationCalculation:
    """Test active and wall-clock duration computation."""

    def test_active_duration_session1(self, parsed_entries_two_sessions):
        """Session 1: 10:00→10:10 = 10 min active."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        assert sessions[0].active_minutes == 10

    def test_active_duration_session2(self, parsed_entries_two_sessions):
        """Session 2: 11:00→11:05 = 5 min active."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        assert sessions[1].active_minutes == 5

    def test_wall_clock_single_session(self, parsed_entries_two_sessions):
        """Wall clock = last - first timestamp."""
        from governance.session_metrics.calculator import split_sessions
        sessions = split_sessions(parsed_entries_two_sessions, idle_threshold_min=30)
        assert sessions[0].wall_clock_minutes == 10
        assert sessions[1].wall_clock_minutes == 5


# ---------------------------------------------------------------------------
# Tests: Tool Counting
# ---------------------------------------------------------------------------

class TestToolCounting:
    """Test tool call aggregation."""

    def test_total_tool_calls(self, parsed_entries_two_sessions):
        """Count total tool_use blocks across all entries."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.tool_calls == 3  # Read + Bash + mcp__gov-core

    def test_mcp_call_count(self, parsed_entries_two_sessions):
        """Count MCP tool calls (name starts with mcp__)."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.mcp_calls == 1

    def test_tool_breakdown(self, parsed_entries_two_sessions):
        """Tool breakdown shows per-tool counts."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.tool_breakdown["Read"] == 1
        assert metrics.tool_breakdown["Bash"] == 1
        assert metrics.tool_breakdown["mcp__gov-core__rules_query"] == 1

    def test_message_count(self, parsed_entries_two_sessions):
        """Count user + assistant messages."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.message_count == 7


# ---------------------------------------------------------------------------
# Tests: Per-Day Aggregation
# ---------------------------------------------------------------------------

class TestPerDayAggregation:
    """Test grouping metrics by date."""

    def test_groups_by_date(self, parsed_entries_two_days):
        """Entries are grouped by UTC date."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_days, idle_threshold_min=30)
        assert len(metrics.days) == 2
        dates = [d.date for d in metrics.days]
        assert "2026-01-28" in dates
        assert "2026-01-29" in dates

    def test_day_session_count(self, parsed_entries_two_days):
        """Each day shows correct session count."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_days, idle_threshold_min=30)
        day_map = {d.date: d for d in metrics.days}
        assert day_map["2026-01-28"].session_count == 1
        assert day_map["2026-01-29"].session_count == 1

    def test_day_compaction_count(self, parsed_entries_two_days):
        """Compaction count per day."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_days, idle_threshold_min=30)
        day_map = {d.date: d for d in metrics.days}
        assert day_map["2026-01-28"].compactions == 0
        assert day_map["2026-01-29"].compactions == 1

    def test_day_tool_calls(self, parsed_entries_two_days):
        """Tool call count per day."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_days, idle_threshold_min=30)
        day_map = {d.date: d for d in metrics.days}
        assert day_map["2026-01-28"].tool_calls == 1  # Edit
        assert day_map["2026-01-29"].tool_calls == 1  # Read


# ---------------------------------------------------------------------------
# Tests: Totals
# ---------------------------------------------------------------------------

class TestTotals:
    """Test aggregated totals."""

    def test_total_active_minutes(self, parsed_entries_two_sessions):
        """Total active = sum of all session active durations."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.active_minutes == 15  # 10 + 5

    def test_total_session_count(self, parsed_entries_two_sessions):
        """Total sessions = count of split sessions."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.session_count == 2

    def test_total_thinking_chars(self, parsed_entries_two_sessions):
        """Total thinking chars across all entries."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        assert metrics.totals.thinking_chars == 350  # 150 + 200

    def test_days_covered(self, parsed_entries_two_days):
        """Days covered = distinct dates."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_days, idle_threshold_min=30)
        assert metrics.totals.days_covered == 2


# ---------------------------------------------------------------------------
# Tests: Date Filtering
# ---------------------------------------------------------------------------

class TestDateFiltering:
    """Test filtering entries by date range."""

    def test_filter_last_n_days(self, parsed_entries_two_days):
        """Filter to last N days from most recent entry."""
        from governance.session_metrics.calculator import filter_entries_by_days
        # Only last 1 day (2026-01-29)
        filtered = filter_entries_by_days(parsed_entries_two_days, days=1)
        timestamps = [e.timestamp for e in filtered]
        assert all(t.day == 29 for t in timestamps)

    def test_filter_all_days(self, parsed_entries_two_days):
        """Large day count returns all entries."""
        from governance.session_metrics.calculator import filter_entries_by_days
        filtered = filter_entries_by_days(parsed_entries_two_days, days=365)
        assert len(filtered) == len(parsed_entries_two_days)


# ---------------------------------------------------------------------------
# Tests: Output Serialization
# ---------------------------------------------------------------------------

class TestOutputSerialization:
    """Test JSON-serializable output."""

    def test_metrics_to_dict(self, parsed_entries_two_sessions):
        """Metrics can be serialized to JSON-compatible dict."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert "days" in result
        assert "totals" in result
        assert "tool_breakdown" in result
        # Should be JSON-serializable
        json.dumps(result)

    def test_output_matches_schema(self, parsed_entries_two_sessions):
        """Output matches SESSION-METRICS-01-v1 schema."""
        from governance.session_metrics.calculator import calculate_metrics
        metrics = calculate_metrics(parsed_entries_two_sessions, idle_threshold_min=30)
        result = metrics.to_dict()

        # Totals schema
        totals = result["totals"]
        assert "active_minutes" in totals
        assert "session_count" in totals
        assert "message_count" in totals
        assert "tool_calls" in totals

        # Day schema
        for day in result["days"]:
            assert "date" in day
            assert "active_minutes" in day
            assert "session_count" in day
            assert "tool_calls" in day
            assert "mcp_calls" in day
            assert "compactions" in day
