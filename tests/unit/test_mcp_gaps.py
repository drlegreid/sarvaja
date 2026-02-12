"""
Unit tests for Gap Backlog MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/gaps.py module.
Tests: register_gap_tools — backlog_get, gaps_summary,
       gaps_critical, backlog_unified.
"""

import json
from unittest.mock import patch, MagicMock

import pytest


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _format_mcp():
    with patch("governance.mcp_tools.gaps.format_mcp_result",
               side_effect=lambda x: json.dumps(x)):
        yield


_P = "governance.mcp_tools.gaps"


def _register():
    from governance.mcp_tools.gaps import register_gap_tools
    mcp = _CaptureMCP()
    register_gap_tools(mcp)
    return mcp.tools


def _make_gap(gap_id="GAP-001", priority="HIGH", status="OPEN"):
    g = MagicMock()
    g.gap_id = gap_id
    g.priority = priority
    g.status = status
    g.to_dict.return_value = {"id": gap_id, "priority": priority, "status": status}
    g.to_todo_format.return_value = f"[{priority}] {gap_id}"
    g.to_work_item.return_value = _make_work_item(gap_id, priority)
    return g


def _make_work_item(item_id="GAP-001", priority="HIGH", item_type_name="GAP"):
    from governance.utils.work_item import WorkItemType
    w = MagicMock()
    w.item_id = item_id
    w.priority = priority
    w.is_open = True
    w.item_type = getattr(WorkItemType, item_type_name, WorkItemType.GAP)
    w.to_dict.return_value = {"id": item_id, "priority": priority}
    w.to_todo_format.return_value = f"[{priority}] {item_id}"
    return w


class TestBacklogGet:
    def test_success(self):
        tools = _register()
        parser = MagicMock()
        parser.get_summary.return_value = {
            "total": 10, "open": 5, "resolved": 5,
            "critical_count": 1, "high_count": 3,
        }
        parser.get_prioritized.return_value = [_make_gap()]
        with patch(f"{_P}.GapParser", return_value=parser):
            result = json.loads(tools["backlog_get"](limit=20))
        assert result["summary"]["total"] == 10
        assert len(result["gaps"]) == 1
        assert len(result["todo_format"]) == 1

    def test_file_not_found(self):
        tools = _register()
        with patch(f"{_P}.GapParser", side_effect=FileNotFoundError("no file")):
            result = json.loads(tools["backlog_get"]())
        assert "error" in result

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.GapParser", side_effect=Exception("parse error")):
            result = json.loads(tools["backlog_get"]())
        assert "Failed to parse" in result["error"]

    def test_custom_limit(self):
        tools = _register()
        parser = MagicMock()
        parser.get_summary.return_value = {
            "total": 10, "open": 5, "resolved": 5,
            "critical_count": 1, "high_count": 3,
        }
        parser.get_prioritized.return_value = []
        with patch(f"{_P}.GapParser", return_value=parser):
            tools["backlog_get"](limit=5)
        parser.get_prioritized.assert_called_with(5)


class TestGapsSummary:
    def test_success(self):
        tools = _register()
        with patch(f"{_P}.get_gap_summary", return_value={"total": 10}):
            result = json.loads(tools["gaps_summary"]())
        assert result["total"] == 10

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.get_gap_summary", side_effect=Exception("fail")):
            result = json.loads(tools["gaps_summary"]())
        assert "error" in result


class TestGapsCritical:
    def test_success(self):
        tools = _register()
        parser = MagicMock()
        parser.get_by_priority.return_value = [_make_gap(priority="CRITICAL")]
        with patch(f"{_P}.GapParser", return_value=parser):
            result = json.loads(tools["gaps_critical"]())
        assert result["count"] == 1
        parser.get_by_priority.assert_called_with("CRITICAL")

    def test_empty(self):
        tools = _register()
        parser = MagicMock()
        parser.get_by_priority.return_value = []
        with patch(f"{_P}.GapParser", return_value=parser):
            result = json.loads(tools["gaps_critical"]())
        assert result["count"] == 0

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.GapParser", side_effect=Exception("fail")):
            result = json.loads(tools["gaps_critical"]())
        assert "error" in result


class TestBacklogUnified:
    def test_gaps_only(self):
        tools = _register()
        parser = MagicMock()
        parser.get_open_gaps.return_value = [_make_gap()]
        with patch(f"{_P}.GapParser", return_value=parser), \
             patch("governance.mcp_tools.common.format_mcp_result",
                   side_effect=lambda x: json.dumps(x)), \
             patch(f"{_P}.sort_by_priority", side_effect=lambda x: x):
            result = json.loads(tools["backlog_unified"](include_tasks=False))
        assert result["summary"]["total"] == 1
        assert result["summary"]["gaps"] == 1

    def test_with_tasks(self):
        tools = _register()
        parser = MagicMock()
        parser.get_open_gaps.return_value = []
        client = MagicMock()
        client.connect.return_value = True
        task = MagicMock()
        client.get_all_tasks.return_value = [task]
        task_item = _make_work_item("T-1", "HIGH", "TASK")
        with patch(f"{_P}.GapParser", return_value=parser), \
             patch("governance.mcp_tools.common.get_typedb_client", return_value=client), \
             patch("governance.mcp_tools.common.format_mcp_result",
                   side_effect=lambda x: json.dumps(x)), \
             patch(f"{_P}.sort_by_priority", side_effect=lambda x: x), \
             patch("governance.utils.work_item.WorkItem.from_task", return_value=task_item):
            result = json.loads(tools["backlog_unified"](include_tasks=True))
        assert result["summary"]["tasks"] == 1

    def test_gap_failure_continues(self):
        tools = _register()
        with patch(f"{_P}.GapParser", side_effect=Exception("fail")), \
             patch("governance.mcp_tools.common.format_mcp_result",
                   side_effect=lambda x: json.dumps(x)), \
             patch("governance.mcp_tools.common.get_typedb_client") as mock_client, \
             patch(f"{_P}.sort_by_priority", side_effect=lambda x: x):
            mock_client.return_value.connect.return_value = False
            result = json.loads(tools["backlog_unified"]())
        assert result["summary"]["total"] == 0

    def test_typedb_failure_continues(self):
        tools = _register()
        parser = MagicMock()
        parser.get_open_gaps.return_value = [_make_gap()]
        with patch(f"{_P}.GapParser", return_value=parser), \
             patch("governance.mcp_tools.common.get_typedb_client",
                   side_effect=Exception("db error")), \
             patch("governance.mcp_tools.common.format_mcp_result",
                   side_effect=lambda x: json.dumps(x)), \
             patch(f"{_P}.sort_by_priority", side_effect=lambda x: x):
            result = json.loads(tools["backlog_unified"]())
        assert result["summary"]["gaps"] == 1
