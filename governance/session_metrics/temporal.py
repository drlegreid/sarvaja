"""Temporal queries for session metrics (SESSION-METRICS-01-v1).

Provides time-based queries: "what was I doing at X?", date range
filtering, and activity timeline generation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from governance.session_metrics.models import ParsedEntry


def _entry_to_dict(entry: ParsedEntry) -> dict:
    """Convert a ParsedEntry to a JSON-serializable dict."""
    return {
        "timestamp": entry.timestamp.isoformat(),
        "entry_type": entry.entry_type,
        "text_content": entry.text_content,
        "session_id": entry.session_id,
        "git_branch": entry.git_branch,
        "tool_names": [tu.name for tu in entry.tool_uses],
        "is_api_error": entry.is_api_error,
    }


def query_at_time(
    entries: list[ParsedEntry],
    target: datetime,
    window_minutes: int = 30,
) -> dict:
    """Find entries near a specific point in time.

    Args:
        entries: Parsed log entries (with extended fields).
        target: The time point to query.
        window_minutes: Minutes before/after target to include.

    Returns:
        Dict with 'entries' list and 'summary' string.
    """
    window = timedelta(minutes=window_minutes)
    start = target - window
    end = target + window

    matched = [
        e for e in entries
        if start <= e.timestamp <= end
    ]

    result_entries = [_entry_to_dict(e) for e in matched]

    # Build summary
    if matched:
        texts = [e.text_content for e in matched if e.text_content]
        tools = set()
        for e in matched:
            for tu in e.tool_uses:
                tools.add(tu.name)
        branches = set(e.git_branch for e in matched if e.git_branch)

        summary_parts = []
        if texts:
            summary_parts.append(texts[0][:100])
        if tools:
            summary_parts.append(f"Tools: {', '.join(sorted(tools))}")
        if branches:
            summary_parts.append(f"Branch: {', '.join(sorted(branches))}")
        summary = " | ".join(summary_parts) if summary_parts else "Activity found"
    else:
        summary = "No activity found at this time"

    return {
        "entries": result_entries,
        "summary": summary,
        "target_time": target.isoformat(),
        "window_minutes": window_minutes,
    }


def query_date_range(
    entries: list[ParsedEntry],
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Return entries within a date range.

    Args:
        entries: Parsed log entries.
        start: Range start (inclusive).
        end: Range end (inclusive).

    Returns:
        List of JSON-serializable entry dicts.
    """
    matched = [
        e for e in entries
        if start <= e.timestamp <= end
    ]
    return [_entry_to_dict(e) for e in matched]


def activity_timeline(entries: list[ParsedEntry]) -> list[dict]:
    """Generate a per-day activity timeline summary.

    Args:
        entries: Parsed log entries.

    Returns:
        Sorted list of day summary dicts with date, entry_count,
        tools_used, branches, and text snippets.
    """
    day_entries: dict[str, list[ParsedEntry]] = defaultdict(list)
    for e in entries:
        date_str = e.timestamp.strftime("%Y-%m-%d")
        day_entries[date_str].append(e)

    timeline = []
    for date_str in sorted(day_entries.keys()):
        day = day_entries[date_str]
        tools = set()
        branches = set()
        snippets = []

        for e in day:
            for tu in e.tool_uses:
                tools.add(tu.name)
            if e.git_branch:
                branches.add(e.git_branch)
            if e.text_content and len(snippets) < 3:
                snippets.append(e.text_content[:100])

        timeline.append({
            "date": date_str,
            "entry_count": len(day),
            "tools_used": sorted(tools),
            "branches": sorted(branches),
            "snippets": snippets,
        })

    return timeline
