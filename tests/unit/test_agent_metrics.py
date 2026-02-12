"""
Unit tests for Agent Subprocess Analytics.

Per DOC-SIZE-01-v1: Tests for session_metrics/agents.py module.
Tests: calculate_agent_metrics.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from governance.session_metrics.agents import calculate_agent_metrics
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _make_entry(ts_offset_min=0, tools=None, model=None):
    return ParsedEntry(
        timestamp=datetime(2026, 2, 11, 10, 0, 0) + timedelta(minutes=ts_offset_min),
        entry_type="assistant",
        tool_uses=tools or [],
        model=model,
    )


def _make_tool(name="Read"):
    return ToolUseInfo(name=name, input_summary="")


# ---------------------------------------------------------------------------
# calculate_agent_metrics
# ---------------------------------------------------------------------------
class TestCalculateAgentMetrics:
    """Tests for calculate_agent_metrics()."""

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_no_agent_files(self, mock_discover, mock_parse):
        mock_discover.return_value = [Path("session.jsonl")]
        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["agent_count"] == 0
        assert result["total_entries"] == 0
        assert result["per_agent"] == []

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_empty_directory(self, mock_discover, mock_parse):
        mock_discover.return_value = []
        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["agent_count"] == 0

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_single_agent_basic(self, mock_discover, mock_parse):
        agent_file = Path("agent-abc123.jsonl")
        mock_discover.return_value = [agent_file]
        mock_parse.return_value = iter([
            _make_entry(ts_offset_min=0),
            _make_entry(ts_offset_min=5),
        ])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["agent_count"] == 1
        assert result["total_entries"] == 2
        assert result["total_active_minutes"] == 5

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_counts_tool_calls(self, mock_discover, mock_parse):
        agent_file = Path("agent-tool-test.jsonl")
        mock_discover.return_value = [agent_file]
        mock_parse.return_value = iter([
            _make_entry(tools=[_make_tool("Read"), _make_tool("Write")]),
            _make_entry(tools=[_make_tool("Grep")]),
        ])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["total_tool_calls"] == 3
        assert result["tool_breakdown"]["Read"] == 1
        assert result["tool_breakdown"]["Write"] == 1
        assert result["tool_breakdown"]["Grep"] == 1

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_model_breakdown(self, mock_discover, mock_parse):
        agent_file = Path("agent-model-test.jsonl")
        mock_discover.return_value = [agent_file]
        mock_parse.return_value = iter([
            _make_entry(model="claude-opus"),
            _make_entry(model="claude-opus"),
            _make_entry(model="claude-haiku"),
            _make_entry(model=None),
        ])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["model_breakdown"]["claude-opus"] == 2
        assert result["model_breakdown"]["claude-haiku"] == 1
        assert "None" not in result["model_breakdown"]

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_multiple_agents(self, mock_discover, mock_parse):
        a1 = Path("agent-aaa.jsonl")
        a2 = Path("agent-bbb.jsonl")
        mock_discover.return_value = [a1, a2, Path("session.jsonl")]

        def side_effect(f):
            if f == a1:
                return iter([_make_entry(), _make_entry(), _make_entry()])
            return iter([_make_entry()])

        mock_parse.side_effect = side_effect

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["agent_count"] == 2
        assert result["total_entries"] == 4
        assert len(result["per_agent"]) == 2

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_per_agent_details(self, mock_discover, mock_parse):
        agent_file = Path("agent-detail.jsonl")
        mock_discover.return_value = [agent_file]
        mock_parse.return_value = iter([
            _make_entry(ts_offset_min=0, tools=[_make_tool()]),
            _make_entry(ts_offset_min=10, tools=[_make_tool(), _make_tool()]),
        ])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        agent_info = result["per_agent"][0]
        assert agent_info["file_name"] == "agent-detail.jsonl"
        assert agent_info["entry_count"] == 2
        assert agent_info["tool_calls"] == 3
        assert agent_info["active_minutes"] == 10

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_single_entry_zero_duration(self, mock_discover, mock_parse):
        agent_file = Path("agent-single.jsonl")
        mock_discover.return_value = [agent_file]
        mock_parse.return_value = iter([_make_entry()])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["total_active_minutes"] == 0

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_filters_non_agent_files(self, mock_discover, mock_parse):
        mock_discover.return_value = [
            Path("session.jsonl"),
            Path("agent-abc.jsonl"),
            Path("progress.jsonl"),
        ]
        mock_parse.return_value = iter([_make_entry()])

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["agent_count"] == 1

    @patch("governance.session_metrics.agents.parse_log_file")
    @patch("governance.session_metrics.agents.discover_log_files")
    def test_tool_counts_aggregate_across_agents(self, mock_discover, mock_parse):
        a1 = Path("agent-x.jsonl")
        a2 = Path("agent-y.jsonl")
        mock_discover.return_value = [a1, a2]

        def side_effect(f):
            if f == a1:
                return iter([_make_entry(tools=[_make_tool("Read")])])
            return iter([_make_entry(tools=[_make_tool("Read"), _make_tool("Write")])])

        mock_parse.side_effect = side_effect

        result = calculate_agent_metrics(Path("/tmp/logs"))
        assert result["tool_breakdown"]["Read"] == 2
        assert result["tool_breakdown"]["Write"] == 1
