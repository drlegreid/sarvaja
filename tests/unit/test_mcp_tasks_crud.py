"""
Unit tests for Task CRUD MCP Tools.

Batch 131: Tests for governance/mcp_tools/tasks_crud.py
- _monitor_task: monitoring wrapper
- task_create: insert + session linking
- task_get: fetch by ID
- task_update: field updates + no-change rejection
- task_delete: deletion + monitoring
- tasks_list: filtering, pagination, limit cap
"""

import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

import pytest

from governance.mcp_tools.tasks_crud import (
    _monitor_task,
    register_task_crud_tools,
)


_MOD = "governance.mcp_tools.tasks_crud"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


def _register_tools():
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    # Patch the verify tools import to avoid registering those
    with patch(f"{_MOD}.register_task_verify_tools"):
        register_task_crud_tools(mcp)
    return tools


@dataclass
class FakeTask:
    id: str = "T-1"
    name: str = "Test Task"
    description: str = "A task"
    status: str = "OPEN"
    phase: str = "P10"
    priority: str = "MEDIUM"
    gap_id: str = ""
    linked_rules: list = field(default_factory=list)
    linked_sessions: list = field(default_factory=list)


# ── _monitor_task ────────────────────────────────────────


class TestMonitorTask:

    @patch(f"{_MOD}.log_monitor_event")
    def test_calls_log(self, mock_log):
        _monitor_task("src", "T-1", "create", status="OPEN")
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["event_type"] == "task_event"
        assert mock_log.call_args[1]["details"]["task_id"] == "T-1"


# ── task_create ──────────────────────────────────────────


class TestTaskCreate:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_successful_create(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.insert_task.return_value = True
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_create"](
            task_id="T-1", name="Test", description="Do stuff"))
        assert result["task_id"] == "T-1"
        assert result["message"] == "Task T-1 created successfully"

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_with_session_linking(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.insert_task.return_value = True
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_create"](
            task_id="T-1", name="Test", session_id="S-1"))
        assert result["linked_sessions"] == ["S-1"]
        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["linked_sessions"] == ["S-1"]

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_insert_failure(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.insert_task.return_value = False
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_create"](task_id="T-1", name="Test"))
        assert "error" in result

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_connection_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        mock_ctx.return_value.__enter__ = MagicMock(side_effect=ConnectionError("fail"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_create"](task_id="T-1", name="Test"))
        assert "error" in result

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_body_format_with_description(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.insert_task.return_value = True
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        tools["task_create"](task_id="T-1", name="Test",
                             description="Fix bug", priority="HIGH")
        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["body"] == "[Priority: HIGH] Fix bug"


# ── task_get ─────────────────────────────────────────────


class TestTaskGet:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_found(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.get_task.return_value = FakeTask()
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_get"](task_id="T-1"))
        assert result["id"] == "T-1"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_not_found(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_task.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_get"](task_id="T-MISSING"))
        assert "error" in result


# ── task_update ──────────────────────────────────────────


class TestTaskUpdate:

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_no_fields_returns_error(self, mock_fmt):
        tools = _register_tools()
        result = json.loads(tools["task_update"](task_id="T-1"))
        assert "No update fields" in result["error"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_successful_update(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.update_task.return_value = True
        client.get_task.return_value = FakeTask(status="DONE")
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_update"](task_id="T-1", status="DONE"))
        assert "updated successfully" in result["message"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_update_success_task_not_refetched(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.update_task.return_value = True
        client.get_task.return_value = None  # Re-fetch fails
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_update"](task_id="T-1", status="DONE"))
        assert result["task_id"] == "T-1"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_update_failure(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.update_task.return_value = False
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_update"](task_id="T-1", status="DONE"))
        assert "error" in result


# ── task_delete ──────────────────────────────────────────


class TestTaskDelete:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_successful_delete(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.delete_task.return_value = True
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_delete"](task_id="T-1"))
        assert result["deleted"] is True

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_delete_failure(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.delete_task.return_value = False
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_delete"](task_id="T-1"))
        assert "error" in result


# ── tasks_list ───────────────────────────────────────────


class TestTasksList:

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_returns_all_tasks(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_all_tasks.return_value = [FakeTask(), FakeTask(id="T-2")]
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["tasks_list"]())
        assert result["count"] == 2
        assert result["total"] == 2
        assert result["source"] == "typedb"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_filters_by_status(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_all_tasks.return_value = [
            FakeTask(status="OPEN"), FakeTask(id="T-2", status="DONE")
        ]
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["tasks_list"](status="DONE"))
        assert result["count"] == 1

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_filters_by_phase(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_all_tasks.return_value = [
            FakeTask(phase="P10"), FakeTask(id="T-2", phase="P11")
        ]
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["tasks_list"](phase="P11"))
        assert result["count"] == 1

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_pagination(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        tasks = [FakeTask(id=f"T-{i}") for i in range(10)]
        client.get_all_tasks.return_value = tasks
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["tasks_list"](limit=3, offset=2))
        assert result["count"] == 3
        assert result["total"] == 10
        assert result["has_more"] is True
        assert result["offset"] == 2

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_limit_capped_at_200(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_all_tasks.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["tasks_list"](limit=500))
        assert result["limit"] == 200
