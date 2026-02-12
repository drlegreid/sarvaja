"""
Unit tests for Task Metrics MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/task_metrics.py module.
Tests: task_metrics(), task_search().
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch

from governance.mcp_tools.task_metrics import register_task_metrics_tools


def _json_format(data, **kwargs):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_task_metrics_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json():
    with patch(
        "governance.mcp_tools.task_metrics.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


class TestRegistration:
    def test_registers_two_tools(self):
        mcp = _register()
        assert "task_metrics" in mcp.tools
        assert "task_search" in mcp.tools


class TestTaskMetrics:
    """Tests for task_metrics()."""

    @patch("governance.services.tasks.list_tasks")
    def test_empty_tasks(self, mock_list):
        mock_list.return_value = {"items": []}
        mcp = _register()
        result = json.loads(mcp.tools["task_metrics"](days=7))
        assert result["total_tasks"] == 0
        assert result["velocity"] == 0

    @patch("governance.services.tasks.list_tasks")
    def test_with_tasks(self, mock_list):
        now = datetime.now().isoformat()
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "status": "DONE", "agent_id": "code-agent",
             "created_at": now, "phase": "P10"},
            {"task_id": "T-2", "status": "TODO", "agent_id": "code-agent",
             "created_at": now, "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_metrics"](days=7))
        assert result["total_tasks"] == 2
        assert result["completion_rate_pct"] == 50.0
        assert result["status_distribution"]["DONE"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_agent_performance(self, mock_list):
        now = datetime.now().isoformat()
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "status": "DONE", "agent_id": "code-agent",
             "created_at": now, "phase": "P10"},
            {"task_id": "T-2", "status": "DONE", "agent_id": "code-agent",
             "created_at": now, "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_metrics"](days=7))
        assert result["agent_performance"]["code-agent"]["done"] == 2

    @patch("governance.services.tasks.list_tasks")
    def test_velocity(self, mock_list):
        now = datetime.now().isoformat()
        mock_list.return_value = {"items": [
            {"task_id": f"T-{i}", "status": "DONE", "agent_id": "a",
             "created_at": now, "phase": "P10"}
            for i in range(7)
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_metrics"](days=7))
        assert result["velocity"] == 1.0

    @patch("governance.services.tasks.list_tasks")
    def test_unassigned_agent(self, mock_list):
        now = datetime.now().isoformat()
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "status": "TODO", "created_at": now, "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_metrics"](days=7))
        assert "(unassigned)" in result["agent_performance"]


class TestTaskSearch:
    """Tests for task_search()."""

    @patch("governance.services.tasks.list_tasks")
    def test_finds_by_id(self, mock_list):
        mock_list.return_value = {"items": [
            {"task_id": "GAP-AUTH-001", "description": "Fix auth", "status": "TODO", "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_search"](query="GAP-AUTH"))
        assert result["total_matches"] == 1
        assert result["results"][0]["relevance"] >= 3

    @patch("governance.services.tasks.list_tasks")
    def test_finds_by_description(self, mock_list):
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "Implement TypeDB migration", "status": "TODO", "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_search"](query="typedb"))
        assert result["total_matches"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_no_matches(self, mock_list):
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "Fix bug", "status": "TODO", "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_search"](query="nonexistent_xyz"))
        assert result["total_matches"] == 0

    @patch("governance.services.tasks.list_tasks")
    def test_limit(self, mock_list):
        mock_list.return_value = {"items": [
            {"task_id": f"T-{i}", "description": "test item", "status": "TODO", "phase": "P10"}
            for i in range(20)
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_search"](query="test", limit=5))
        assert len(result["results"]) == 5

    @patch("governance.services.tasks.list_tasks")
    def test_ranking(self, mock_list):
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "auth module", "status": "TODO", "phase": "auth"},
            {"task_id": "AUTH-001", "description": "unrelated desc", "status": "TODO", "phase": "P10"},
        ]}
        mcp = _register()
        result = json.loads(mcp.tools["task_search"](query="auth"))
        assert result["total_matches"] == 2
