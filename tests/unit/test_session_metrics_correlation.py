"""
TDD Test Spec: Session Metrics Tool Call Correlation
=====================================================
Per GAP-SESSION-METRICS-CORRELATION: tool_use → tool_result join
for MCP call latency/duration + server attribution.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_correlation.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures: synthetic JSONL with tool_use + tool_result pairs
# ---------------------------------------------------------------------------

def _assistant_entry(ts: str, tool_uses: list, uuid: str = "a1",
                     model: str = "claude-opus-4-5-20251101") -> dict:
    content = []
    for tu in tool_uses:
        content.append({
            "type": "tool_use", "id": tu["id"],
            "name": tu["name"], "input": tu.get("input", {}),
        })
    return {
        "type": "assistant",
        "timestamp": ts,
        "sessionId": "sess-001",
        "uuid": uuid,
        "message": {"role": "assistant", "content": content, "model": model},
    }


def _tool_result_entry(ts: str, tool_use_id: str,
                       mcp_meta: dict = None, uuid: str = "tr1") -> dict:
    entry = {
        "type": "user",
        "timestamp": ts,
        "sessionId": "sess-001",
        "uuid": uuid,
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id,
                          "content": "result data"}],
        },
    }
    if mcp_meta:
        entry["mcpMeta"] = mcp_meta
    return entry


def _user_entry(ts: str, uuid: str = "u1") -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "sessionId": "sess-001",
        "uuid": uuid,
        "message": {"role": "user", "content": "hello"},
    }


@pytest.fixture
def correlation_log_dir(tmp_path):
    """Log with tool_use → tool_result pairs, some with mcpMeta."""
    entries = [
        _user_entry("2026-01-28T10:00:00Z", uuid="u1"),
        # Assistant makes 2 tool calls: Read (local) + MCP health_check
        _assistant_entry("2026-01-28T10:00:05Z", [
            {"id": "tu1", "name": "Read", "input": {"file_path": "/tmp/test"}},
            {"id": "tu2", "name": "mcp__gov-core__health_check", "input": {}},
        ], uuid="a1"),
        # tool_result for Read (0.5s later)
        _tool_result_entry("2026-01-28T10:00:05.500Z", "tu1", uuid="tr1"),
        # tool_result for MCP health_check (2s later, with mcpMeta)
        _tool_result_entry("2026-01-28T10:00:07Z", "tu2",
                           mcp_meta={"serverName": "gov-core",
                                     "tool": "health_check"},
                           uuid="tr2"),
        # Another assistant with single MCP call
        _assistant_entry("2026-01-28T10:00:10Z", [
            {"id": "tu3", "name": "mcp__gov-sessions__session_start",
             "input": {"description": "test"}},
        ], uuid="a2"),
        # tool_result for session_start (3s later)
        _tool_result_entry("2026-01-28T10:00:13Z", "tu3",
                           mcp_meta={"serverName": "gov-sessions",
                                     "tool": "session_start"},
                           uuid="tr3"),
    ]
    log_file = tmp_path / "correlation-test.jsonl"
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return tmp_path, log_file


@pytest.fixture
def orphan_log_dir(tmp_path):
    """Log with tool_use that has no matching tool_result (orphan)."""
    entries = [
        _user_entry("2026-01-28T10:00:00Z"),
        _assistant_entry("2026-01-28T10:00:05Z", [
            {"id": "tu_orphan", "name": "Bash", "input": {"command": "ls"}},
        ]),
        # No tool_result follows — session ends
        _user_entry("2026-01-28T10:01:00Z", uuid="u2"),
    ]
    log_file = tmp_path / "orphan-test.jsonl"
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return tmp_path, log_file


# ---------------------------------------------------------------------------
# Tests: Parser extracts tool_result info
# ---------------------------------------------------------------------------

class TestToolResultParsing:
    """Test that parser extracts tool_result blocks for correlation."""

    def test_parse_extracts_tool_results(self, correlation_log_dir):
        """Parser extracts tool_result blocks with tool_use_id."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        entries_with_results = [e for e in entries if e.tool_results]
        assert len(entries_with_results) == 3

    def test_tool_result_has_tool_use_id(self, correlation_log_dir):
        """Each tool_result has the tool_use_id it corresponds to."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        results = [tr for e in entries for tr in e.tool_results]
        ids = {tr.tool_use_id for tr in results}
        assert "tu1" in ids
        assert "tu2" in ids
        assert "tu3" in ids

    def test_tool_result_has_mcp_server(self, correlation_log_dir):
        """MCP tool_results carry server name from mcpMeta."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        results = [tr for e in entries for tr in e.tool_results]
        mcp_results = [tr for tr in results if tr.server_name]
        assert len(mcp_results) == 2
        servers = {tr.server_name for tr in mcp_results}
        assert "gov-core" in servers
        assert "gov-sessions" in servers

    def test_local_tool_result_no_server(self, correlation_log_dir):
        """Local (non-MCP) tool results have no server_name."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        results = [tr for e in entries for tr in e.tool_results]
        tu1_result = [tr for tr in results if tr.tool_use_id == "tu1"][0]
        assert tu1_result.server_name is None


# ---------------------------------------------------------------------------
# Tests: Correlation engine
# ---------------------------------------------------------------------------

class TestToolCallCorrelation:
    """Test joining tool_use with tool_result by ID."""

    def test_correlate_returns_all_matches(self, correlation_log_dir):
        """Correlation finds all tool_use → tool_result pairs."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        assert len(correlated) == 3

    def test_correlated_has_tool_name(self, correlation_log_dir):
        """Each correlated call has the tool name from tool_use."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        names = {c.tool_name for c in correlated}
        assert "Read" in names
        assert "mcp__gov-core__health_check" in names
        assert "mcp__gov-sessions__session_start" in names

    def test_correlated_has_latency(self, correlation_log_dir):
        """Each correlated call has latency_ms calculated."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        for c in correlated:
            assert c.latency_ms is not None
            assert c.latency_ms >= 0

    def test_read_latency_500ms(self, correlation_log_dir):
        """Read tool: 10:00:05 → 10:00:05.500 = 500ms."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        read_call = [c for c in correlated if c.tool_name == "Read"][0]
        assert read_call.latency_ms == 500

    def test_mcp_health_check_latency_2000ms(self, correlation_log_dir):
        """MCP health_check: 10:00:05 → 10:00:07 = 2000ms."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        hc = [c for c in correlated
              if c.tool_name == "mcp__gov-core__health_check"][0]
        assert hc.latency_ms == 2000

    def test_correlated_has_server_name(self, correlation_log_dir):
        """MCP correlated calls include server_name."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        hc = [c for c in correlated
              if c.tool_name == "mcp__gov-core__health_check"][0]
        assert hc.server_name == "gov-core"

    def test_correlated_is_mcp_flag(self, correlation_log_dir):
        """Correlated calls have is_mcp flag from tool name."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        read_call = [c for c in correlated if c.tool_name == "Read"][0]
        hc = [c for c in correlated
              if c.tool_name == "mcp__gov-core__health_check"][0]
        assert read_call.is_mcp is False
        assert hc.is_mcp is True

    def test_orphan_tool_use_excluded(self, orphan_log_dir):
        """Tool_use without matching tool_result is excluded from correlation."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        _, log_file = orphan_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        assert len(correlated) == 0


# ---------------------------------------------------------------------------
# Tests: Correlation summary stats
# ---------------------------------------------------------------------------

class TestCorrelationSummary:
    """Test aggregated correlation statistics."""

    def test_summary_has_total_correlated(self, correlation_log_dir):
        """Summary includes total correlated count."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        assert summary["total_correlated"] == 3

    def test_summary_has_avg_latency(self, correlation_log_dir):
        """Summary includes average latency_ms."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        assert "avg_latency_ms" in summary
        # (500 + 2000 + 3000) / 3 = 1833.33
        assert 1800 <= summary["avg_latency_ms"] <= 1900

    def test_summary_has_mcp_avg_latency(self, correlation_log_dir):
        """Summary includes MCP-only average latency."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        assert "mcp_avg_latency_ms" in summary
        # MCP: (2000 + 3000) / 2 = 2500
        assert summary["mcp_avg_latency_ms"] == 2500

    def test_summary_per_server_breakdown(self, correlation_log_dir):
        """Summary has per-server latency breakdown."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        assert "per_server" in summary
        assert "gov-core" in summary["per_server"]
        assert "gov-sessions" in summary["per_server"]
        assert summary["per_server"]["gov-core"]["count"] == 1
        assert summary["per_server"]["gov-core"]["avg_latency_ms"] == 2000
        assert summary["per_server"]["gov-sessions"]["count"] == 1
        assert summary["per_server"]["gov-sessions"]["avg_latency_ms"] == 3000

    def test_summary_per_tool_breakdown(self, correlation_log_dir):
        """Summary has per-tool latency breakdown."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        assert "per_tool" in summary
        assert "Read" in summary["per_tool"]
        assert summary["per_tool"]["Read"]["avg_latency_ms"] == 500

    def test_summary_empty_list(self):
        """Empty correlated list produces safe summary."""
        from governance.session_metrics.correlation import summarize_correlation
        summary = summarize_correlation([])
        assert summary["total_correlated"] == 0
        assert summary["avg_latency_ms"] == 0
        assert summary["mcp_avg_latency_ms"] == 0

    def test_summary_serializable(self, correlation_log_dir):
        """Summary is JSON-serializable."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        _, log_file = correlation_log_dir
        entries = list(parse_log_file(log_file))
        correlated = correlate_tool_calls(entries)
        summary = summarize_correlation(correlated)
        json.dumps(summary)  # Should not raise
