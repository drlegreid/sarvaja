"""
Unit tests for MCP Structured Logging.

Per MCP-LOGGING-01-v1: Tests for MCPMetrics, log_tool_call context manager,
and convenience functions.
"""

import json
import os
import tempfile
import time
import pytest
from unittest.mock import MagicMock, patch

from governance.mcp_logging import (
    MCPMetrics,
    log_tool_call,
    log_server_start,
    log_server_stop,
    TRACE,
    LOG_LEVEL_MAP,
)


# ---------------------------------------------------------------------------
# TRACE level
# ---------------------------------------------------------------------------
class TestTraceLevel:
    """Tests for custom TRACE log level."""

    def test_trace_level_value(self):
        assert TRACE == 5

    def test_trace_in_log_level_map(self):
        assert "TRACE" in LOG_LEVEL_MAP
        assert LOG_LEVEL_MAP["TRACE"] == 5


# ---------------------------------------------------------------------------
# MCPMetrics
# ---------------------------------------------------------------------------
class TestMCPMetrics:
    """Tests for MCPMetrics collector class."""

    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"MCP_METRICS_FILE": f"{tmpdir}/metrics.jsonl"}):
                metrics = MCPMetrics("test-server")
        assert metrics.server_name == "test-server"
        assert metrics._tool_calls == {}

    def test_record_tool_call_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf  # ensure uses temp
            metrics.record_tool_call("health_check", 15.5, True)
            assert metrics._tool_calls["health_check"]["count"] == 1
            assert metrics._tool_calls["health_check"]["errors"] == 0
            assert metrics._tool_calls["health_check"]["total_ms"] == 15.5

    def test_record_tool_call_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf
            metrics.record_tool_call("broken_tool", 100.0, False, error="timeout")
            assert metrics._tool_calls["broken_tool"]["errors"] == 1

    def test_record_multiple_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf
            metrics.record_tool_call("tool_a", 10.0, True)
            metrics.record_tool_call("tool_a", 20.0, True)
            metrics.record_tool_call("tool_a", 30.0, False)
            assert metrics._tool_calls["tool_a"]["count"] == 3
            assert metrics._tool_calls["tool_a"]["errors"] == 1
            assert metrics._tool_calls["tool_a"]["total_ms"] == 60.0

    def test_record_startup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf
            metrics.record_startup(15, 250.5)
            with open(mf) as f:
                lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["metric_type"] == "startup"
            assert data["tools"] == 15
            assert data["startup_ms"] == 250.5

    def test_get_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf
            metrics.record_tool_call("tool_a", 10.0, True)
            summary = metrics.get_summary()
            assert summary["server"] == "test-server"
            assert "uptime_seconds" in summary
            assert "tool_a" in summary["tool_stats"]

    def test_write_metric_creates_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = mf
            metrics.record_tool_call("test", 5.0, True)
            with open(mf) as f:
                data = json.loads(f.readline())
            assert data["tool"] == "test"
            assert data["success"] is True

    def test_write_metric_error_swallowed(self):
        """Write errors should be silently caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mf = f"{tmpdir}/metrics.jsonl"
            with patch.dict(os.environ, {"MCP_METRICS_FILE": mf}):
                metrics = MCPMetrics("test-server")
            metrics.metrics_file = "/nonexistent/path/metrics.jsonl"
            # Should not raise
            metrics.record_tool_call("test", 5.0, True)


# ---------------------------------------------------------------------------
# log_tool_call context manager
# ---------------------------------------------------------------------------
class TestLogToolCall:
    """Tests for log_tool_call context manager."""

    def test_success_yields_call_id(self):
        logger = MagicMock()
        with log_tool_call(logger, "health_check") as call_id:
            assert call_id.startswith("health_check-")

    def test_success_logs_start_and_success(self):
        logger = MagicMock()
        with log_tool_call(logger, "my_tool", args={"key": "val"}):
            pass
        logger.debug.assert_called_once()
        logger.info.assert_called_once()
        # Check start log
        start_call = logger.debug.call_args
        assert start_call[0][0] == "tool_call_start"
        assert start_call[1]["tool"] == "my_tool"
        # Check success log
        success_call = logger.info.call_args
        assert success_call[0][0] == "tool_call_success"
        assert "duration_ms" in success_call[1]

    def test_error_logs_error_and_reraises(self):
        logger = MagicMock()
        with pytest.raises(ValueError, match="boom"):
            with log_tool_call(logger, "failing_tool"):
                raise ValueError("boom")
        logger.error.assert_called_once()
        error_call = logger.error.call_args
        assert error_call[0][0] == "tool_call_error"
        assert error_call[1]["error"] == "ValueError"
        assert error_call[1]["error_type"] == "ValueError"

    def test_duration_measured(self):
        logger = MagicMock()
        with log_tool_call(logger, "slow_tool"):
            time.sleep(0.01)
        success_call = logger.info.call_args
        assert success_call[1]["duration_ms"] >= 5  # at least some time passed


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------
class TestConvenienceFunctions:
    """Tests for log_server_start and log_server_stop."""

    def test_log_server_start(self):
        logger = MagicMock()
        log_server_start(logger, "gov-core", 15, "2.0.0")
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert call_args[0][0] == "server_started"
        assert call_args[1]["server"] == "gov-core"
        assert call_args[1]["tools"] == 15
        assert call_args[1]["version"] == "2.0.0"

    def test_log_server_stop(self):
        logger = MagicMock()
        log_server_stop(logger, "gov-core")
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert call_args[0][0] == "server_stopped"
        assert call_args[1]["server"] == "gov-core"
