"""Agent subprocess analytics (GAP-SESSION-METRICS-AGENTS).

Parses agent-*.jsonl files to provide subprocess-level metrics:
entry counts, tool calls, active duration, model usage.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from governance.session_metrics.parser import discover_log_files, parse_log_file


def calculate_agent_metrics(directory: Path) -> dict:
    """Calculate metrics for all agent subprocess log files.

    Args:
        directory: Path to Claude Code project log directory.

    Returns:
        Dict with agent_count, total_entries, total_tool_calls,
        total_active_minutes, per_agent breakdown, tool/model breakdowns.
    """
    directory = Path(directory)
    all_files = discover_log_files(directory, include_agents=True)
    agent_files = [f for f in all_files if f.name.startswith("agent-")]

    if not agent_files:
        return {
            "agent_count": 0,
            "total_entries": 0,
            "total_tool_calls": 0,
            "total_active_minutes": 0,
            "per_agent": [],
            "tool_breakdown": {},
            "model_breakdown": {},
        }

    total_entries = 0
    total_tool_calls = 0
    total_active_minutes = 0
    per_agent = []
    tool_counts: dict[str, int] = defaultdict(int)
    model_counts: dict[str, int] = defaultdict(int)

    for af in agent_files:
        entries = list(parse_log_file(af))
        entry_count = len(entries)
        agent_tool_calls = sum(len(e.tool_uses) for e in entries)

        # Active duration: first to last entry
        active_min = 0
        if len(entries) >= 2:
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            delta = sorted_entries[-1].timestamp - sorted_entries[0].timestamp
            active_min = int(delta.total_seconds() / 60)

        # Tool breakdown
        for e in entries:
            for tu in e.tool_uses:
                tool_counts[tu.name] += 1

        # Model breakdown
        for e in entries:
            if e.model:
                model_counts[e.model] += 1

        total_entries += entry_count
        total_tool_calls += agent_tool_calls
        total_active_minutes += active_min

        per_agent.append({
            "file_name": af.name,
            "entry_count": entry_count,
            "tool_calls": agent_tool_calls,
            "active_minutes": active_min,
        })

    return {
        "agent_count": len(agent_files),
        "total_entries": total_entries,
        "total_tool_calls": total_tool_calls,
        "total_active_minutes": total_active_minutes,
        "per_agent": per_agent,
        "tool_breakdown": dict(tool_counts),
        "model_breakdown": dict(model_counts),
    }
