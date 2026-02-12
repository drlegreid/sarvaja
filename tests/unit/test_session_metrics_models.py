"""
Unit tests for Session Metrics Data Models.

Per DOC-SIZE-01-v1: Tests for session_metrics/models.py module.
Tests: ToolUseInfo, ToolResultInfo, ParsedEntry, DayMetrics, TotalMetrics, MetricsResult.
"""

import json
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
    def test_from_content_block(self):
        block = {"name": "Read", "input": {"path": "/foo"}, "id": "tu-1"}
        info = ToolUseInfo.from_content_block(block)
        assert info.name == "Read"
        assert info.is_mcp is False
        assert info.tool_use_id == "tu-1"
        assert "/foo" in info.input_summary

    def test_mcp_detection(self):
        block = {"name": "mcp__gov-core__rules_query", "input": {}}
        info = ToolUseInfo.from_content_block(block)
        assert info.is_mcp is True

    def test_input_truncation(self):
        block = {"name": "Write", "input": {"content": "x" * 300}}
        info = ToolUseInfo.from_content_block(block)
        assert len(info.input_summary) <= 200
        assert info.input_summary.endswith("...")

    def test_missing_fields(self):
        info = ToolUseInfo.from_content_block({})
        assert info.name == ""
        assert info.is_mcp is False


class TestToolResultInfo:
    def test_basic(self):
        info = ToolResultInfo(tool_use_id="tu-1", server_name="gov-core")
        assert info.tool_use_id == "tu-1"
        assert info.server_name == "gov-core"


class TestCorrelatedToolCall:
    def test_basic(self):
        now = datetime.now()
        call = CorrelatedToolCall(
            tool_use_id="tu-1", tool_name="Read",
            is_mcp=False, use_timestamp=now,
            result_timestamp=now, latency_ms=50,
        )
        assert call.latency_ms == 50


class TestParsedEntry:
    def test_defaults(self):
        entry = ParsedEntry(timestamp=datetime.now(), entry_type="assistant")
        assert entry.tool_uses == []
        assert entry.tool_results == []
        assert entry.thinking_chars == 0
        assert entry.is_compaction is False
        assert entry.user_content is None


class TestSessionInfo:
    def test_basic(self):
        now = datetime.now()
        info = SessionInfo(
            start_time=now, end_time=now,
            entry_count=10, active_minutes=5, wall_clock_minutes=10,
        )
        assert info.entry_count == 10


class TestDayMetrics:
    def test_to_dict(self):
        dm = DayMetrics(date="2026-02-11", active_minutes=30,
                         message_count=100, tool_calls=50)
        d = dm.to_dict()
        assert d["date"] == "2026-02-11"
        assert d["active_minutes"] == 30
        assert d["tool_calls"] == 50

    def test_defaults(self):
        dm = DayMetrics(date="2026-01-01")
        assert dm.api_errors == 0
        assert dm.compactions == 0


class TestTotalMetrics:
    def test_to_dict(self):
        tm = TotalMetrics(message_count=100, api_errors=5, days_covered=3)
        d = tm.to_dict()
        assert d["error_rate"] == 0.05
        assert d["days_covered"] == 3

    def test_zero_messages(self):
        tm = TotalMetrics(message_count=0, api_errors=0)
        d = tm.to_dict()
        assert d["error_rate"] == 0.0


class TestMetricsResult:
    def test_to_dict(self):
        mr = MetricsResult(
            days=[DayMetrics(date="2026-02-11")],
            totals=TotalMetrics(message_count=10),
            tool_breakdown={"Read": 5, "Write": 3},
        )
        d = mr.to_dict()
        assert len(d["days"]) == 1
        assert d["tool_breakdown"]["Read"] == 5

    def test_empty(self):
        mr = MetricsResult()
        d = mr.to_dict()
        assert d["days"] == []
        assert d["tool_breakdown"] == {}
