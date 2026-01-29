"""Data models for session metrics (SESSION-METRICS-01-v1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ToolUseInfo:
    """A single tool invocation extracted from a log entry."""

    name: str
    input_summary: str  # JSON string, truncated to 200 chars
    is_mcp: bool = False

    @classmethod
    def from_content_block(cls, block: dict) -> ToolUseInfo:
        raw_input = json.dumps(block.get("input", {}))
        if len(raw_input) > 200:
            raw_input = raw_input[:197] + "..."
        name = block.get("name", "")
        return cls(
            name=name,
            input_summary=raw_input,
            is_mcp=name.startswith("mcp__"),
        )


@dataclass
class ParsedEntry:
    """A single parsed JSONL log entry."""

    timestamp: datetime
    entry_type: str  # user, assistant, system, progress, etc.
    tool_uses: list[ToolUseInfo] = field(default_factory=list)
    thinking_chars: int = 0
    thinking_content: Optional[str] = None
    user_content: Optional[str] = None  # Always None (privacy)
    is_compaction: bool = False
    model: Optional[str] = None


@dataclass
class SessionInfo:
    """A single activity session (burst separated by idle gap)."""

    start_time: datetime
    end_time: datetime
    entry_count: int
    active_minutes: int
    wall_clock_minutes: int


@dataclass
class DayMetrics:
    """Aggregated metrics for a single day."""

    date: str  # YYYY-MM-DD
    active_minutes: int = 0
    wall_clock_minutes: int = 0
    session_count: int = 0
    message_count: int = 0
    tool_calls: int = 0
    mcp_calls: int = 0
    compactions: int = 0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "active_minutes": self.active_minutes,
            "wall_clock_minutes": self.wall_clock_minutes,
            "session_count": self.session_count,
            "message_count": self.message_count,
            "tool_calls": self.tool_calls,
            "mcp_calls": self.mcp_calls,
            "compactions": self.compactions,
        }


@dataclass
class TotalMetrics:
    """Aggregated totals across all days."""

    active_minutes: int = 0
    session_count: int = 0
    message_count: int = 0
    tool_calls: int = 0
    mcp_calls: int = 0
    thinking_chars: int = 0
    days_covered: int = 0

    def to_dict(self) -> dict:
        return {
            "active_minutes": self.active_minutes,
            "session_count": self.session_count,
            "message_count": self.message_count,
            "tool_calls": self.tool_calls,
            "mcp_calls": self.mcp_calls,
            "thinking_chars": self.thinking_chars,
            "days_covered": self.days_covered,
        }


@dataclass
class MetricsResult:
    """Complete metrics output matching SESSION-METRICS-01-v1 schema."""

    days: list[DayMetrics] = field(default_factory=list)
    totals: TotalMetrics = field(default_factory=TotalMetrics)
    tool_breakdown: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "days": [d.to_dict() for d in self.days],
            "totals": self.totals.to_dict(),
            "tool_breakdown": dict(self.tool_breakdown),
        }
