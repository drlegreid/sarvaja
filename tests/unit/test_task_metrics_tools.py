"""
Unit tests for Task Metrics MCP Tools.

Per EPIC-H: Tests for task_metrics and task_search MCP tool functions.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from governance.mcp_tools.task_metrics import register_task_metrics_tools


def _json_format(data, **kw):
    """Force JSON output instead of TOON."""
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.task_metrics.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture
def mcp_tools():
    mcp = _CaptureMCP()
    register_task_metrics_tools(mcp)
    return mcp.tools


def _make_task(task_id, status="OPEN", agent_id=None, phase="backlog",
               created_days_ago=1):
    """Helper to create a mock task dict."""
    created = (datetime.now() - timedelta(days=created_days_ago)).isoformat()
    return {
        "task_id": task_id,
        "status": status,
        "agent_id": agent_id,
        "phase": phase,
        "description": f"Task {task_id}",
        "created_at": created,
        "updated_at": created,
    }


# ---------------------------------------------------------------------------
# task_metrics
# ---------------------------------------------------------------------------
class TestTaskMetrics:
    """Tests for task_metrics() tool."""

    @patch("governance.services.tasks.list_tasks")
    def test_empty_tasks(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": []}
        result = json.loads(mcp_tools["task_metrics"]())
        assert result["total_tasks"] == 0
        assert result["velocity"] == 0
        assert result["completion_rate_pct"] == 0

    @patch("governance.services.tasks.list_tasks")
    def test_with_tasks(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", status="DONE", agent_id="code-agent"),
            _make_task("T-2", status="OPEN", agent_id="code-agent"),
            _make_task("T-3", status="DONE"),
        ]}
        result = json.loads(mcp_tools["task_metrics"](days=7))
        assert result["total_tasks"] == 3
        assert result["completion_rate_pct"] == pytest.approx(66.7, abs=0.1)
        assert result["velocity"] == pytest.approx(2 / 7, abs=0.1)

    @patch("governance.services.tasks.list_tasks")
    def test_status_distribution(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", status="DONE"),
            _make_task("T-2", status="DONE"),
            _make_task("T-3", status="OPEN"),
            _make_task("T-4", status="IN_PROGRESS"),
        ]}
        result = json.loads(mcp_tools["task_metrics"]())
        dist = result["status_distribution"]
        assert dist["DONE"] == 2
        assert dist["OPEN"] == 1
        assert dist["IN_PROGRESS"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_agent_performance(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", status="DONE", agent_id="code-agent"),
            _make_task("T-2", status="OPEN", agent_id="code-agent"),
            _make_task("T-3", status="DONE", agent_id="rules-curator"),
        ]}
        result = json.loads(mcp_tools["task_metrics"]())
        agents = result["agent_performance"]
        assert agents["code-agent"]["total"] == 2
        assert agents["code-agent"]["done"] == 1
        assert agents["rules-curator"]["done"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_unassigned_agent(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", status="OPEN"),
        ]}
        result = json.loads(mcp_tools["task_metrics"]())
        assert "(unassigned)" in result["agent_performance"]

    @patch("governance.services.tasks.list_tasks")
    def test_old_tasks_filtered(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", status="DONE", created_days_ago=1),
            _make_task("T-2", status="DONE", created_days_ago=30),
        ]}
        result = json.loads(mcp_tools["task_metrics"](days=7))
        assert result["total_tasks"] == 1  # Only recent one
        assert result["all_tasks_total"] == 2  # Both in total

    @patch("governance.services.tasks.list_tasks")
    def test_completed_status_counts(self, mock_list, mcp_tools):
        """COMPLETED status also counts as done."""
        mock_list.return_value = {"items": [
            _make_task("T-1", status="COMPLETED"),
            _make_task("T-2", status="DONE"),
        ]}
        result = json.loads(mcp_tools["task_metrics"]())
        assert result["completion_rate_pct"] == 100.0

    @patch("governance.services.tasks.list_tasks")
    def test_phase_distribution(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("T-1", phase="backlog"),
            _make_task("T-2", phase="validate"),
            _make_task("T-3", phase="backlog"),
        ]}
        result = json.loads(mcp_tools["task_metrics"]())
        assert result["phase_distribution"]["backlog"] == 2
        assert result["phase_distribution"]["validate"] == 1


# ---------------------------------------------------------------------------
# task_search
# ---------------------------------------------------------------------------
class TestTaskSearch:
    """Tests for task_search() tool."""

    @patch("governance.services.tasks.list_tasks")
    def test_search_by_id(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task("GAP-UI-001"),
            _make_task("GAP-MCP-002"),
            _make_task("TASK-003"),
        ]}
        result = json.loads(mcp_tools["task_search"](query="GAP-UI"))
        assert result["total_matches"] == 1
        assert result["results"][0]["task_id"] == "GAP-UI-001"

    @patch("governance.services.tasks.list_tasks")
    def test_search_by_description(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "Fix login bug", "status": "OPEN",
             "phase": "impl", "agent_id": None, "created_at": datetime.now().isoformat(),
             "updated_at": datetime.now().isoformat()},
            {"task_id": "T-2", "description": "Add dashboard", "status": "DONE",
             "phase": "done", "agent_id": None, "created_at": datetime.now().isoformat(),
             "updated_at": datetime.now().isoformat()},
        ]}
        result = json.loads(mcp_tools["task_search"](query="login"))
        assert result["total_matches"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_search_no_match(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [_make_task("T-1")]}
        result = json.loads(mcp_tools["task_search"](query="nonexistent"))
        assert result["total_matches"] == 0
        assert result["results"] == []

    @patch("governance.services.tasks.list_tasks")
    def test_search_case_insensitive(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [_make_task("GAP-UI-001")]}
        result = json.loads(mcp_tools["task_search"](query="gap-ui"))
        assert result["total_matches"] == 1

    @patch("governance.services.tasks.list_tasks")
    def test_search_limit(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            _make_task(f"GAP-{i}") for i in range(20)
        ]}
        result = json.loads(mcp_tools["task_search"](query="GAP", limit=5))
        assert len(result["results"]) == 5
        assert result["total_matches"] == 20

    @patch("governance.services.tasks.list_tasks")
    def test_search_relevance_ranking(self, mock_list, mcp_tools):
        """ID match (score 3) ranks higher than description match (score 2)."""
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "Fix the login flow",
             "status": "OPEN", "phase": "impl", "agent_id": None,
             "created_at": datetime.now().isoformat(),
             "updated_at": datetime.now().isoformat()},
            {"task_id": "login-fix", "description": "Some task",
             "status": "OPEN", "phase": "impl", "agent_id": None,
             "created_at": datetime.now().isoformat(),
             "updated_at": datetime.now().isoformat()},
        ]}
        result = json.loads(mcp_tools["task_search"](query="login"))
        assert len(result["results"]) == 2
        # ID match should be first (higher relevance)
        assert result["results"][0]["task_id"] == "login-fix"

    @patch("governance.services.tasks.list_tasks")
    def test_search_truncates_description(self, mock_list, mcp_tools):
        mock_list.return_value = {"items": [
            {"task_id": "T-1", "description": "A" * 200,
             "status": "OPEN", "phase": "impl", "agent_id": None,
             "created_at": datetime.now().isoformat(),
             "updated_at": datetime.now().isoformat()},
        ]}
        result = json.loads(mcp_tools["task_search"](query="AAAA"))
        assert len(result["results"][0]["description"]) <= 150
