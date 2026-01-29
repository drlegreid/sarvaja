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
    tool_use_id: Optional[str] = None

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
            tool_use_id=block.get("id"),
        )


@dataclass
class ToolResultInfo:
    """A tool_result block extracted from a log entry."""

    tool_use_id: str
    server_name: Optional[str] = None  # From mcpMeta.serverName


@dataclass
class CorrelatedToolCall:
    """A tool_use joined with its tool_result for latency measurement."""

    tool_use_id: str
    tool_name: str
    is_mcp: bool
    use_timestamp: datetime
    result_timestamp: datetime
    latency_ms: int
    server_name: Optional[str] = None


@dataclass
class ParsedEntry:
    """A single parsed JSONL log entry."""

    timestamp: datetime
    entry_type: str  # user, assistant, system, progress, etc.
    tool_uses: list[ToolUseInfo] = field(default_factory=list)
    tool_results: list[ToolResultInfo] = field(default_factory=list)
    thinking_chars: int = 0
    thinking_content: Optional[str] = None
    user_content: Optional[str] = None  # Always None (privacy)
    is_compaction: bool = False
    is_api_error: bool = False
    model: Optional[str] = None
    # Extended fields (populated by parse_log_file_extended)
    session_id: Optional[str] = None
    git_branch: Optional[str] = None
    text_content: Optional[str] = None  # Concatenated text blocks


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
    api_errors: int = 0

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
            "api_errors": self.api_errors,
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
    api_errors: int = 0

    def to_dict(self) -> dict:
        error_rate = round(self.api_errors / self.message_count, 2) if self.message_count > 0 else 0.0
        return {
            "active_minutes": self.active_minutes,
            "session_count": self.session_count,
            "message_count": self.message_count,
            "tool_calls": self.tool_calls,
            "mcp_calls": self.mcp_calls,
            "thinking_chars": self.thinking_chars,
            "days_covered": self.days_covered,
            "api_errors": self.api_errors,
            "error_rate": error_rate,
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
