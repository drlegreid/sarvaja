"""Session splitting, metrics calculation, and aggregation (SESSION-METRICS-01-v1)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from governance.session_metrics.models import (
    DayMetrics,
    MetricsResult,
    ParsedEntry,
    SessionInfo,
    TotalMetrics,
)


def filter_entries_by_days(
    entries: list[ParsedEntry], days: int
) -> list[ParsedEntry]:
    """Filter entries to only those within the last N days.

    Uses the most recent entry's date as reference.
    """
    if not entries:
        return []

    latest = max(e.timestamp for e in entries)
    cutoff = latest.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    return [e for e in entries if e.timestamp >= cutoff]


def split_sessions(
    entries: list[ParsedEntry], idle_threshold_min: int = 30
) -> list[SessionInfo]:
    """Split entries into sessions based on idle gaps.

    A new session starts when the gap between consecutive entries
    exceeds idle_threshold_min minutes.
    """
    if not entries:
        return []

    sorted_entries = sorted(entries, key=lambda e: e.timestamp)
    threshold = timedelta(minutes=idle_threshold_min)

    sessions = []
    current_start = 0

    for i in range(1, len(sorted_entries)):
        gap = sorted_entries[i].timestamp - sorted_entries[i - 1].timestamp
        if gap > threshold:
            sessions.append(_build_session(sorted_entries[current_start:i]))
            current_start = i

    # Final session
    sessions.append(_build_session(sorted_entries[current_start:]))
    return sessions


def _build_session(entries: list[ParsedEntry]) -> SessionInfo:
    """Build a SessionInfo from a contiguous block of entries."""
    start = entries[0].timestamp
    end = entries[-1].timestamp
    delta = end - start
    minutes = int(delta.total_seconds() / 60)
    return SessionInfo(
        start_time=start,
        end_time=end,
        entry_count=len(entries),
        active_minutes=minutes,
        wall_clock_minutes=minutes,
    )


def calculate_metrics(
    entries: list[ParsedEntry], idle_threshold_min: int = 30
) -> MetricsResult:
    """Calculate full metrics from parsed entries."""
    if not entries:
        return MetricsResult()

    sessions = split_sessions(entries, idle_threshold_min)

    # Tool breakdown
    tool_counts: dict[str, int] = defaultdict(int)
    total_tool_calls = 0
    total_mcp_calls = 0
    total_thinking_chars = 0
    total_compactions = 0
    total_api_errors = 0

    for entry in entries:
        for tu in entry.tool_uses:
            tool_counts[tu.name] += 1
            total_tool_calls += 1
            if tu.is_mcp:
                total_mcp_calls += 1
        total_thinking_chars += entry.thinking_chars
        if entry.is_compaction:
            total_compactions += 1
        if entry.is_api_error:
            total_api_errors += 1

    # Per-day aggregation
    day_entries: dict[str, list[ParsedEntry]] = defaultdict(list)
    for entry in entries:
        date_str = entry.timestamp.strftime("%Y-%m-%d")
        day_entries[date_str].append(entry)

    days = []
    for date_str in sorted(day_entries.keys()):
        d_entries = day_entries[date_str]
        d_sessions = split_sessions(d_entries, idle_threshold_min)

        d_tool_calls = sum(len(e.tool_uses) for e in d_entries)
        d_mcp_calls = sum(
            1 for e in d_entries for tu in e.tool_uses if tu.is_mcp
        )
        d_compactions = sum(1 for e in d_entries if e.is_compaction)
        d_api_errors = sum(1 for e in d_entries if e.is_api_error)
        d_active = sum(s.active_minutes for s in d_sessions)
        d_wall = sum(s.wall_clock_minutes for s in d_sessions)

        days.append(DayMetrics(
            date=date_str,
            active_minutes=d_active,
            wall_clock_minutes=d_wall,
            session_count=len(d_sessions),
            message_count=len(d_entries),
            tool_calls=d_tool_calls,
            mcp_calls=d_mcp_calls,
            compactions=d_compactions,
            api_errors=d_api_errors,
        ))

    totals = TotalMetrics(
        active_minutes=sum(s.active_minutes for s in sessions),
        session_count=len(sessions),
        message_count=len(entries),
        tool_calls=total_tool_calls,
        mcp_calls=total_mcp_calls,
        thinking_chars=total_thinking_chars,
        days_covered=len(days),
        api_errors=total_api_errors,
    )

    return MetricsResult(
        days=days,
        totals=totals,
        tool_breakdown=dict(tool_counts),
    )
