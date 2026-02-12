"""
Unit tests for Tool Call Correlation.

Per DOC-SIZE-01-v1: Tests for session_metrics/correlation.py module.
Tests: correlate_tool_calls, summarize_correlation.
"""

import pytest
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


def _make_entry(ts_offset_ms=0, tool_uses=None, tool_results=None):
    return ParsedEntry(
        timestamp=datetime(2026, 2, 11, 10, 0, 0) + timedelta(milliseconds=ts_offset_ms),
        entry_type="assistant",
        tool_uses=tool_uses or [],
        tool_results=tool_results or [],
    )


def _make_use(name="Read", tool_use_id="tu-1", is_mcp=False):
    return ToolUseInfo(
        name=name, input_summary="", is_mcp=is_mcp, tool_use_id=tool_use_id,
    )


def _make_result(tool_use_id="tu-1", server_name=None):
    return ToolResultInfo(tool_use_id=tool_use_id, server_name=server_name)


# ---------------------------------------------------------------------------
# correlate_tool_calls
# ---------------------------------------------------------------------------
class TestCorrelateToolCalls:
    """Tests for correlate_tool_calls()."""

    def test_empty_entries(self):
        assert correlate_tool_calls([]) == []

    def test_no_tool_calls(self):
        entries = [_make_entry()]
        assert correlate_tool_calls(entries) == []

    def test_use_without_result(self):
        entries = [_make_entry(tool_uses=[_make_use(tool_use_id="tu-1")])]
        assert correlate_tool_calls(entries) == []

    def test_result_without_use(self):
        entries = [_make_entry(tool_results=[_make_result(tool_use_id="tu-orphan")])]
        assert correlate_tool_calls(entries) == []

    def test_basic_correlation(self):
        entries = [
            _make_entry(ts_offset_ms=0, tool_uses=[_make_use(tool_use_id="tu-1")]),
            _make_entry(ts_offset_ms=500, tool_results=[_make_result(tool_use_id="tu-1")]),
        ]
        result = correlate_tool_calls(entries)
        assert len(result) == 1
        assert result[0].tool_use_id == "tu-1"
        assert result[0].tool_name == "Read"
        assert result[0].latency_ms == 500

    def test_mcp_flag_preserved(self):
        entries = [
            _make_entry(tool_uses=[_make_use(name="mcp__test", tool_use_id="tu-2", is_mcp=True)]),
            _make_entry(ts_offset_ms=100, tool_results=[_make_result(tool_use_id="tu-2")]),
        ]
        result = correlate_tool_calls(entries)
        assert result[0].is_mcp is True

    def test_server_name_from_result(self):
        entries = [
            _make_entry(tool_uses=[_make_use(tool_use_id="tu-3")]),
            _make_entry(ts_offset_ms=200, tool_results=[
                _make_result(tool_use_id="tu-3", server_name="gov-core"),
            ]),
        ]
        result = correlate_tool_calls(entries)
        assert result[0].server_name == "gov-core"

    def test_multiple_correlations(self):
        entries = [
            _make_entry(ts_offset_ms=0, tool_uses=[
                _make_use(name="Read", tool_use_id="tu-a"),
                _make_use(name="Write", tool_use_id="tu-b"),
            ]),
            _make_entry(ts_offset_ms=300, tool_results=[
                _make_result(tool_use_id="tu-a"),
                _make_result(tool_use_id="tu-b"),
            ]),
        ]
        result = correlate_tool_calls(entries)
        assert len(result) == 2

    def test_no_tool_use_id_skipped(self):
        entries = [
            _make_entry(tool_uses=[_make_use(tool_use_id=None)]),
            _make_entry(ts_offset_ms=100, tool_results=[_make_result(tool_use_id="tu-1")]),
        ]
        result = correlate_tool_calls(entries)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# summarize_correlation
# ---------------------------------------------------------------------------
class TestSummarizeCorrelation:
    """Tests for summarize_correlation()."""

    def test_empty_list(self):
        result = summarize_correlation([])
        assert result["total_correlated"] == 0
        assert result["avg_latency_ms"] == 0
        assert result["mcp_avg_latency_ms"] == 0
        assert result["per_server"] == {}
        assert result["per_tool"] == {}

    def test_single_call(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        calls = [CorrelatedToolCall(
            tool_use_id="tu-1", tool_name="Read", is_mcp=False,
            use_timestamp=now, result_timestamp=now + timedelta(milliseconds=200),
            latency_ms=200,
        )]
        result = summarize_correlation(calls)
        assert result["total_correlated"] == 1
        assert result["avg_latency_ms"] == 200
        assert result["mcp_avg_latency_ms"] == 0

    def test_mcp_average(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall(
                tool_use_id="tu-1", tool_name="mcp__rules", is_mcp=True,
                use_timestamp=now, result_timestamp=now + timedelta(milliseconds=100),
                latency_ms=100,
            ),
            CorrelatedToolCall(
                tool_use_id="tu-2", tool_name="mcp__tasks", is_mcp=True,
                use_timestamp=now, result_timestamp=now + timedelta(milliseconds=300),
                latency_ms=300,
            ),
            CorrelatedToolCall(
                tool_use_id="tu-3", tool_name="Read", is_mcp=False,
                use_timestamp=now, result_timestamp=now + timedelta(milliseconds=50),
                latency_ms=50,
            ),
        ]
        result = summarize_correlation(calls)
        assert result["mcp_avg_latency_ms"] == 200  # (100+300)//2

    def test_per_server_breakdown(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall(
                tool_use_id="tu-1", tool_name="X", is_mcp=True,
                use_timestamp=now, result_timestamp=now,
                latency_ms=100, server_name="gov-core",
            ),
            CorrelatedToolCall(
                tool_use_id="tu-2", tool_name="Y", is_mcp=True,
                use_timestamp=now, result_timestamp=now,
                latency_ms=300, server_name="gov-core",
            ),
        ]
        result = summarize_correlation(calls)
        assert "gov-core" in result["per_server"]
        srv = result["per_server"]["gov-core"]
        assert srv["count"] == 2
        assert srv["avg_latency_ms"] == 200
        assert srv["min_latency_ms"] == 100
        assert srv["max_latency_ms"] == 300

    def test_per_tool_breakdown(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        calls = [
            CorrelatedToolCall(
                tool_use_id="tu-1", tool_name="Read", is_mcp=False,
                use_timestamp=now, result_timestamp=now,
                latency_ms=50,
            ),
            CorrelatedToolCall(
                tool_use_id="tu-2", tool_name="Read", is_mcp=False,
                use_timestamp=now, result_timestamp=now,
                latency_ms=150,
            ),
        ]
        result = summarize_correlation(calls)
        assert "Read" in result["per_tool"]
        tool = result["per_tool"]["Read"]
        assert tool["count"] == 2
        assert tool["avg_latency_ms"] == 100

    def test_no_server_name_excluded(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        calls = [CorrelatedToolCall(
            tool_use_id="tu-1", tool_name="Read", is_mcp=False,
            use_timestamp=now, result_timestamp=now,
            latency_ms=50, server_name=None,
        )]
        result = summarize_correlation(calls)
        assert result["per_server"] == {}
