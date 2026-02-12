"""
Unit tests for Session Metrics MCP Tools.

Batch 130: Tests for governance/mcp_tools/session_metrics.py
- _resolve_project_dir: explicit path, env var, auto-detect
- session_metrics: JSONL parsing pipeline, error paths
- session_search: entry search with filters
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

import pytest

from governance.mcp_tools.session_metrics import (
    _resolve_project_dir,
    register_session_metrics_tools,
)


_MOD = "governance.mcp_tools.session_metrics"


def _json_fmt(data):
    """Simulate format_mcp_result returning JSON."""
    return json.dumps(data, indent=2, default=str)


def _register_tools():
    """Register tools and return them as a dict."""
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    register_session_metrics_tools(mcp)
    return tools


# ── _resolve_project_dir ─────────────────────────────────


class TestResolveProjectDir:

    def test_explicit_path(self):
        result = _resolve_project_dir("/tmp/my-logs")
        assert result == Path("/tmp/my-logs")

    @patch.dict(os.environ, {"CLAUDE_PROJECT_LOG_DIR": "/env/logs"})
    def test_env_variable(self):
        result = _resolve_project_dir(None)
        assert result == Path("/env/logs")

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.getcwd", return_value="/home/user/project")
    def test_auto_detect_from_cwd(self, mock_cwd):
        # Remove env var if present
        os.environ.pop("CLAUDE_PROJECT_LOG_DIR", None)
        result = _resolve_project_dir(None)
        assert ".claude/projects/" in str(result)
        assert "home-user-project" in str(result)

    def test_explicit_overrides_env(self):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_LOG_DIR": "/env/logs"}):
            result = _resolve_project_dir("/explicit")
            assert result == Path("/explicit")


# ── session_metrics ──────────────────────────────────────


@dataclass
class FakeMetrics:
    """Minimal metrics result for testing."""
    def to_dict(self):
        return {"total_duration_min": 120.5, "session_count": 3}


class TestSessionMetrics:

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_dir_not_found(self, mock_resolve, mock_fmt):
        mock_resolve.return_value = Path("/nonexistent/dir")
        tools = _register_tools()
        result = json.loads(tools["session_metrics"]())
        assert "error" in result
        assert "not found" in result["error"]

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_log_files(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path  # Empty directory
        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[]):
            result = json.loads(tools["session_metrics"]())
            assert "error" in result
            assert "No JSONL" in result["error"]

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_parseable_entries(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        log_file = tmp_path / "session.jsonl"
        log_file.touch()

        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[log_file]):
            with patch("governance.session_metrics.parser.parse_log_file", return_value=iter([])):
                result = json.loads(tools["session_metrics"]())
                assert "error" in result
                assert "No parseable" in result["error"]

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_successful_metrics(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        log_file = tmp_path / "session.jsonl"
        log_file.touch()

        entry = {"ts": "2026-02-12T10:00:00", "type": "human"}
        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[log_file]), \
             patch("governance.session_metrics.parser.parse_log_file", return_value=iter([entry])), \
             patch("governance.session_metrics.calculator.filter_entries_by_days", return_value=[entry]), \
             patch("governance.session_metrics.calculator.calculate_metrics", return_value=FakeMetrics()), \
             patch("governance.session_metrics.correlation.correlate_tool_calls", return_value=[]), \
             patch("governance.session_metrics.correlation.summarize_correlation", return_value={"avg_ms": 0}), \
             patch("governance.session_metrics.agents.calculate_agent_metrics", return_value={}):
            result = json.loads(tools["session_metrics"](days=3))
            assert result["total_duration_min"] == 120.5
            assert result["metadata"]["days_requested"] == 3
            assert result["metadata"]["total_entries_parsed"] == 1
            assert result["correlation"]["avg_ms"] == 0

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_passes_idle_threshold(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        log_file = tmp_path / "session.jsonl"
        log_file.touch()

        entry = {"ts": "2026-02-12T10:00:00"}
        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[log_file]), \
             patch("governance.session_metrics.parser.parse_log_file", return_value=iter([entry])), \
             patch("governance.session_metrics.calculator.filter_entries_by_days", return_value=[entry]), \
             patch("governance.session_metrics.calculator.calculate_metrics", return_value=FakeMetrics()) as mock_calc, \
             patch("governance.session_metrics.correlation.correlate_tool_calls", return_value=[]), \
             patch("governance.session_metrics.correlation.summarize_correlation", return_value={}), \
             patch("governance.session_metrics.agents.calculate_agent_metrics", return_value={}):
            tools["session_metrics"](idle_threshold_min=60)
            mock_calc.assert_called_once_with([entry], idle_threshold_min=60)


# ── session_search ───────────────────────────────────────


class TestSessionSearch:

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_dir_not_found(self, mock_resolve, mock_fmt):
        mock_resolve.return_value = Path("/nonexistent/dir")
        tools = _register_tools()
        result = json.loads(tools["session_search"](query="test"))
        assert "error" in result

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_log_files(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[]):
            result = json.loads(tools["session_search"](query="test"))
            assert "error" in result

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_successful_search(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        log_file = tmp_path / "session.jsonl"
        log_file.touch()

        entry = MagicMock()
        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[log_file]), \
             patch("governance.session_metrics.parser.parse_log_file_extended", return_value=iter([entry])), \
             patch("governance.session_metrics.search.search_entries", return_value=[entry]) as mock_search, \
             patch("governance.session_metrics.search.results_to_dicts", return_value=[{"text": "found"}]):
            result = json.loads(tools["session_search"](
                query="test", session_id="S-1", git_branch="master", max_results=10))
            assert result["total_matches"] == 1
            assert result["metadata"]["query"] == "test"
            mock_search.assert_called_once_with(
                [entry], query="test", session_id="S-1",
                git_branch="master", max_results=10)

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_empty_search_results(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        log_file = tmp_path / "session.jsonl"
        log_file.touch()

        tools = _register_tools()

        with patch("governance.session_metrics.parser.discover_log_files", return_value=[log_file]), \
             patch("governance.session_metrics.parser.parse_log_file_extended", return_value=iter([])), \
             patch("governance.session_metrics.search.search_entries", return_value=[]), \
             patch("governance.session_metrics.search.results_to_dicts", return_value=[]):
            result = json.loads(tools["session_search"](query="nothing"))
            assert result["total_matches"] == 0
