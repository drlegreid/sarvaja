"""
Unit tests for Session Metrics Tool Call Correlation.

Per DOC-SIZE-01-v1: Tests for session_metrics/correlation.py module.
Tests: correlate_tool_calls(), summarize_correlation().
"""

from datetime import datetime, timedelta

from governance.session_metrics.correlation import (
    correlate_tool_calls,
    summarize_correlation,
)
from governance.session_metrics.models import (
    CorrelatedToolCall,
    ParsedEntry,
    ToolUseInfo,
    ToolResultInfo,
)


def _entry(ts, tool_uses=None, tool_results=None, **kw):
    return ParsedEntry(
        timestamp=ts, entry_type="assistant",
        tool_uses=tool_uses or [], tool_results=tool_results or [],
        **kw,
    )


class TestCorrelateToolCalls:
    def test_basic_correlation(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        t1 = t0 + timedelta(seconds=1)
        entries = [
            _entry(t0, tool_uses=[
                ToolUseInfo(name="Read", input_summary="{}", tool_use_id="tu-1"),
            ]),
            _entry(t1, tool_results=[
                ToolResultInfo(tool_use_id="tu-1"),
            ]),
        ]
        correlated = correlate_tool_calls(entries)
        assert len(correlated) == 1
        assert correlated[0].tool_name == "Read"
        assert correlated[0].latency_ms == 1000

    def test_unmatched_result(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, tool_results=[
                ToolResultInfo(tool_use_id="tu-orphan"),
            ]),
        ]
        assert correlate_tool_calls(entries) == []

    def test_mcp_detection(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        t1 = t0 + timedelta(milliseconds=500)
        entries = [
            _entry(t0, tool_uses=[
                ToolUseInfo(name="mcp__gov-core__rules_query",
                            input_summary="{}", is_mcp=True, tool_use_id="tu-2"),
            ]),
            _entry(t1, tool_results=[
                ToolResultInfo(tool_use_id="tu-2", server_name="gov-core"),
            ]),
        ]
        correlated = correlate_tool_calls(entries)
        assert correlated[0].is_mcp is True
        assert correlated[0].server_name == "gov-core"

    def test_empty_entries(self):
        assert correlate_tool_calls([]) == []


class TestSummarizeCorrelation:
    def test_empty(self):
        result = summarize_correlation([])
        assert result["total_correlated"] == 0
        assert result["avg_latency_ms"] == 0

    def test_basic_stats(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall("tu-1", "Read", False, t0, t0, 100),
            CorrelatedToolCall("tu-2", "Write", False, t0, t0, 200),
        ]
        result = summarize_correlation(calls)
        assert result["total_correlated"] == 2
        assert result["avg_latency_ms"] == 150

    def test_per_tool(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall("tu-1", "Read", False, t0, t0, 100),
            CorrelatedToolCall("tu-2", "Read", False, t0, t0, 200),
        ]
        result = summarize_correlation(calls)
        assert result["per_tool"]["Read"]["count"] == 2
        assert result["per_tool"]["Read"]["avg_latency_ms"] == 150

    def test_per_server(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall("tu-1", "query", True, t0, t0, 50,
                                server_name="gov-core"),
        ]
        result = summarize_correlation(calls)
        assert "gov-core" in result["per_server"]
        assert result["per_server"]["gov-core"]["count"] == 1

    def test_mcp_avg(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall("tu-1", "Read", False, t0, t0, 100),
            CorrelatedToolCall("tu-2", "mcp_query", True, t0, t0, 200),
        ]
        result = summarize_correlation(calls)
        assert result["mcp_avg_latency_ms"] == 200
