"""
Tests for session metrics data models.

Per SESSION-METRICS-01-v1: Session analytics data structures.
Covers ToolUseInfo, ToolResultInfo, CorrelatedToolCall, ParsedEntry,
SessionInfo, DayMetrics, TotalMetrics, MetricsResult.

Created: 2026-01-30
"""

import json
import pytest
from datetime import datetime

from governance.session_metrics.models import (
    ToolUseInfo,
    ToolResultInfo,
    CorrelatedToolCall,
    ParsedEntry,
    SessionInfo,
    DayMetrics,
    TotalMetrics,
    MetricsResult,
)


class TestToolUseInfo:
    """Test ToolUseInfo dataclass."""

    def test_minimal(self):
        t = ToolUseInfo(name="Read", input_summary='{"path": "/f"}')
        assert t.is_mcp is False
        assert t.tool_use_id is None

    def test_mcp_tool(self):
        t = ToolUseInfo(name="mcp__gov-core__health", input_summary="{}", is_mcp=True)
        assert t.is_mcp is True

    def test_from_content_block(self):
        block = {
            "name": "Read",
            "input": {"file_path": "/test.py"},
            "id": "tool_123"
        }
        t = ToolUseInfo.from_content_block(block)
        assert t.name == "Read"
        assert t.tool_use_id == "tool_123"
        assert t.is_mcp is False
        assert "/test.py" in t.input_summary

    def test_from_content_block_mcp(self):
        block = {"name": "mcp__claude-mem__query", "input": {"q": "test"}}
        t = ToolUseInfo.from_content_block(block)
        assert t.is_mcp is True

    def test_from_content_block_truncates_input(self):
        block = {"name": "Write", "input": {"content": "x" * 500}}
        t = ToolUseInfo.from_content_block(block)
        assert len(t.input_summary) <= 200
        assert t.input_summary.endswith("...")

    def test_from_content_block_short_input(self):
        block = {"name": "Read", "input": {}}
        t = ToolUseInfo.from_content_block(block)
        assert t.input_summary == "{}"
        assert not t.input_summary.endswith("...")

    def test_from_content_block_missing_fields(self):
        t = ToolUseInfo.from_content_block({})
        assert t.name == ""
        assert t.tool_use_id is None


class TestToolResultInfo:
    """Test ToolResultInfo dataclass."""

    def test_create(self):
        r = ToolResultInfo(tool_use_id="tool_123")
        assert r.server_name is None

    def test_with_server(self):
        r = ToolResultInfo(tool_use_id="t1", server_name="gov-core")
        assert r.server_name == "gov-core"


class TestCorrelatedToolCall:
    """Test CorrelatedToolCall dataclass."""

    def test_create(self):
        c = CorrelatedToolCall(
            tool_use_id="t1", tool_name="Read", is_mcp=False,
            use_timestamp=datetime(2026, 1, 30, 10, 0),
            result_timestamp=datetime(2026, 1, 30, 10, 0, 1),
            latency_ms=1000
        )
        assert c.latency_ms == 1000
        assert c.server_name is None

    def test_with_server(self):
        c = CorrelatedToolCall(
            tool_use_id="t1", tool_name="mcp__test", is_mcp=True,
            use_timestamp=datetime(2026, 1, 30, 10, 0),
            result_timestamp=datetime(2026, 1, 30, 10, 0, 5),
            latency_ms=5000, server_name="gov-core"
        )
        assert c.server_name == "gov-core"


class TestParsedEntry:
    """Test ParsedEntry dataclass."""

    def test_minimal(self):
        e = ParsedEntry(timestamp=datetime(2026, 1, 30), entry_type="user")
        assert e.tool_uses == []
        assert e.tool_results == []
        assert e.thinking_chars == 0
        assert e.is_compaction is False
        assert e.is_api_error is False
        assert e.model is None

    def test_with_extended_fields(self):
        e = ParsedEntry(
            timestamp=datetime(2026, 1, 30), entry_type="assistant",
            session_id="S1", git_branch="main", text_content="Hello"
        )
        assert e.session_id == "S1"
        assert e.git_branch == "main"

    def test_with_thinking(self):
        e = ParsedEntry(
            timestamp=datetime(2026, 1, 30), entry_type="assistant",
            thinking_chars=500, thinking_content="Let me analyze..."
        )
        assert e.thinking_chars == 500


class TestSessionInfo:
    """Test SessionInfo dataclass."""

    def test_create(self):
        s = SessionInfo(
            start_time=datetime(2026, 1, 30, 9, 0),
            end_time=datetime(2026, 1, 30, 12, 0),
            entry_count=150,
            active_minutes=120,
            wall_clock_minutes=180
        )
        assert s.entry_count == 150
        assert s.active_minutes == 120


class TestDayMetrics:
    """Test DayMetrics dataclass."""

    def test_defaults(self):
        d = DayMetrics(date="2026-01-30")
        assert d.active_minutes == 0
        assert d.tool_calls == 0
        assert d.compactions == 0

    def test_with_data(self):
        d = DayMetrics(
            date="2026-01-30", active_minutes=120,
            message_count=50, tool_calls=200, mcp_calls=30,
            session_count=3, compactions=1, api_errors=2
        )
        assert d.mcp_calls == 30

    def test_to_dict(self):
        d = DayMetrics(date="2026-01-30", active_minutes=60, tool_calls=10)
        result = d.to_dict()
        assert result["date"] == "2026-01-30"
        assert result["active_minutes"] == 60
        assert result["tool_calls"] == 10
        assert "mcp_calls" in result


class TestTotalMetrics:
    """Test TotalMetrics dataclass."""

    def test_defaults(self):
        t = TotalMetrics()
        assert t.active_minutes == 0
        assert t.message_count == 0

    def test_to_dict(self):
        t = TotalMetrics(active_minutes=500, message_count=200,
                        tool_calls=1000, api_errors=5, days_covered=7)
        result = t.to_dict()
        assert result["active_minutes"] == 500
        assert result["error_rate"] == 0.03  # 5/200 = 0.025 → rounds to 0.03

    def test_to_dict_zero_messages(self):
        t = TotalMetrics()
        result = t.to_dict()
        assert result["error_rate"] == 0.0


class TestMetricsResult:
    """Test MetricsResult dataclass."""

    def test_empty(self):
        m = MetricsResult()
        assert m.days == []
        assert m.tool_breakdown == {}

    def test_to_dict(self):
        m = MetricsResult(
            days=[DayMetrics(date="2026-01-30", tool_calls=10)],
            totals=TotalMetrics(tool_calls=10, message_count=5),
            tool_breakdown={"Read": 5, "Write": 3, "Bash": 2}
        )
        result = m.to_dict()
        assert len(result["days"]) == 1
        assert result["days"][0]["date"] == "2026-01-30"
        assert result["totals"]["tool_calls"] == 10
        assert result["tool_breakdown"]["Read"] == 5

    def test_to_dict_serializable(self):
        m = MetricsResult(
            days=[DayMetrics(date="2026-01-30")],
            totals=TotalMetrics()
        )
        json_str = json.dumps(m.to_dict())
        assert "2026-01-30" in json_str
