"""
Unit tests for Session Metrics MCP Tools.

Batch 122: Tests for governance/mcp_tools/session_metrics.py
- _resolve_project_dir() path resolution logic
- session_metrics() tool: directory validation, parsing, metrics
- session_search() tool: query, filtering, results
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.mcp_tools.session_metrics"
# Lazy imports inside closures — patch at source module
_PARSER = "governance.session_metrics.parser"
_CALC = "governance.session_metrics.calculator"
_CORR = "governance.session_metrics.correlation"
_AGENTS = "governance.session_metrics.agents"
_SEARCH = "governance.session_metrics.search"
# Mock format_mcp_result to return plain JSON
_FMT = "governance.mcp_tools.session_metrics.format_mcp_result"


def _json_fmt(data):
    """Test-friendly format_mcp_result replacement."""
    return json.dumps(data, default=str)


# ── _resolve_project_dir ────────────────────────────────────


class TestResolveProjectDir:
    """Tests for _resolve_project_dir path resolution."""

    def test_explicit_path_returned(self):
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        result = _resolve_project_dir("/explicit/path")
        assert result == Path("/explicit/path")

    def test_env_var_used_when_no_explicit(self):
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        with patch.dict(os.environ, {"CLAUDE_PROJECT_LOG_DIR": "/env/dir"}):
            result = _resolve_project_dir()
            assert result == Path("/env/dir")

    def test_explicit_overrides_env(self):
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        with patch.dict(os.environ, {"CLAUDE_PROJECT_LOG_DIR": "/env/dir"}):
            result = _resolve_project_dir("/explicit")
            assert result == Path("/explicit")

    @patch.dict(os.environ, {}, clear=True)
    @patch(f"{_MOD}.os.getcwd", return_value="/home/user/project")
    def test_auto_detect_from_cwd(self, mock_cwd):
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        os.environ.pop("CLAUDE_PROJECT_LOG_DIR", None)
        result = _resolve_project_dir()
        assert ".claude" in str(result)
        assert "projects" in str(result)

    def test_explicit_empty_string_uses_fallback(self):
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        with patch.dict(os.environ, {"CLAUDE_PROJECT_LOG_DIR": "/env/path"}):
            result = _resolve_project_dir("")
            assert result == Path("/env/path")


# ── session_metrics() ───────────────────────────────────────


class TestSessionMetricsTool:
    """Tests for session_metrics MCP tool."""

    def _register_and_get(self):
        """Helper to register tools and extract session_metrics."""
        from governance.mcp_tools.session_metrics import register_session_metrics_tools
        mcp = MagicMock()
        tools = {}

        def tool_decorator():
            def wrapper(fn):
                tools[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_session_metrics_tools(mcp)
        return tools["session_metrics"]

    @patch(_FMT, side_effect=_json_fmt)
    def test_dir_not_found(self, mock_fmt):
        fn = self._register_and_get()
        with patch(f"{_MOD}._resolve_project_dir", return_value=Path("/nonexistent")):
            result = fn(project_path="/nonexistent")
            data = json.loads(result)
            assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_log_files(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        with patch(f"{_PARSER}.discover_log_files", return_value=[]):
            result = fn(project_path=str(tmp_path))
            data = json.loads(result)
            assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_parseable_entries(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        mock_file = MagicMock()
        mock_file.name = "test.jsonl"

        with patch(f"{_PARSER}.discover_log_files", return_value=[mock_file]), \
             patch(f"{_PARSER}.parse_log_file", return_value=iter([])):
            result = fn(project_path=str(tmp_path))
            data = json.loads(result)
            assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_successful_metrics(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        mock_file = MagicMock()
        mock_file.name = "test.jsonl"
        mock_entry = MagicMock()

        mock_metrics = MagicMock()
        mock_metrics.to_dict.return_value = {"sessions": 3, "total_duration": 100}

        with patch(f"{_PARSER}.discover_log_files", return_value=[mock_file]), \
             patch(f"{_PARSER}.parse_log_file", return_value=iter([mock_entry])), \
             patch(f"{_CALC}.filter_entries_by_days", return_value=[mock_entry]), \
             patch(f"{_CALC}.calculate_metrics", return_value=mock_metrics), \
             patch(f"{_CORR}.correlate_tool_calls", return_value=[]), \
             patch(f"{_CORR}.summarize_correlation", return_value={}), \
             patch(f"{_AGENTS}.calculate_agent_metrics", return_value={}):
            result = fn(project_path=str(tmp_path))
            data = json.loads(result)
            assert "metadata" in data
            assert data["sessions"] == 3

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_metadata_includes_log_info(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        mock_file = MagicMock()
        mock_file.name = "session.jsonl"
        mock_entry = MagicMock()

        mock_metrics = MagicMock()
        mock_metrics.to_dict.return_value = {}

        with patch(f"{_PARSER}.discover_log_files", return_value=[mock_file]), \
             patch(f"{_PARSER}.parse_log_file", return_value=iter([mock_entry])), \
             patch(f"{_CALC}.filter_entries_by_days", return_value=[mock_entry]), \
             patch(f"{_CALC}.calculate_metrics", return_value=mock_metrics), \
             patch(f"{_CORR}.correlate_tool_calls", return_value=[]), \
             patch(f"{_CORR}.summarize_correlation", return_value={}), \
             patch(f"{_AGENTS}.calculate_agent_metrics", return_value={}):
            result = fn(days=3, project_path=str(tmp_path))
            data = json.loads(result)
            assert data["metadata"]["days_requested"] == 3
            assert data["metadata"]["log_files"] == ["session.jsonl"]

    def test_default_days_is_5(self):
        fn = self._register_and_get()
        import inspect
        sig = inspect.signature(fn)
        assert sig.parameters["days"].default == 5

    def test_default_idle_threshold_is_30(self):
        fn = self._register_and_get()
        import inspect
        sig = inspect.signature(fn)
        assert sig.parameters["idle_threshold_min"].default == 30


# ── session_search() ────────────────────────────────────────


class TestSessionSearchTool:
    """Tests for session_search MCP tool."""

    def _register_and_get(self):
        from governance.mcp_tools.session_metrics import register_session_metrics_tools
        mcp = MagicMock()
        tools = {}

        def tool_decorator():
            def wrapper(fn):
                tools[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_session_metrics_tools(mcp)
        return tools["session_search"]

    @patch(_FMT, side_effect=_json_fmt)
    def test_dir_not_found(self, mock_fmt):
        fn = self._register_and_get()
        with patch(f"{_MOD}._resolve_project_dir", return_value=Path("/nonexistent")):
            result = fn(query="test", project_path="/nonexistent")
            data = json.loads(result)
            assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_no_log_files(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        with patch(f"{_PARSER}.discover_log_files", return_value=[]):
            result = fn(query="test")
            data = json.loads(result)
            assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_successful_search(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        mock_file = MagicMock()
        mock_entry = MagicMock()

        with patch(f"{_PARSER}.discover_log_files", return_value=[mock_file]), \
             patch(f"{_PARSER}.parse_log_file_extended", return_value=iter([mock_entry])), \
             patch(f"{_SEARCH}.search_entries", return_value=[mock_entry]), \
             patch(f"{_SEARCH}.results_to_dicts", return_value=[{"text": "match"}]):
            result = fn(query="test", max_results=10)
            data = json.loads(result)
            assert data["total_matches"] == 1
            assert data["metadata"]["query"] == "test"

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}._resolve_project_dir")
    def test_search_passes_filters(self, mock_resolve, mock_fmt, tmp_path):
        mock_resolve.return_value = tmp_path
        fn = self._register_and_get()
        mock_file = MagicMock()

        with patch(f"{_PARSER}.discover_log_files", return_value=[mock_file]), \
             patch(f"{_PARSER}.parse_log_file_extended", return_value=iter([])), \
             patch(f"{_SEARCH}.search_entries", return_value=[]) as mock_search, \
             patch(f"{_SEARCH}.results_to_dicts", return_value=[]):
            fn(query="find me", session_id="S-1", git_branch="main")
            mock_search.assert_called_once()
            call_kwargs = mock_search.call_args
            assert call_kwargs[1]["query"] == "find me"
            assert call_kwargs[1]["session_id"] == "S-1"
            assert call_kwargs[1]["git_branch"] == "main"

    def test_default_max_results_is_50(self):
        fn = self._register_and_get()
        import inspect
        sig = inspect.signature(fn)
        assert sig.parameters["max_results"].default == 50
