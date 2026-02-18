"""
Unit tests for Task Verification & Session Sync MCP Tools.

Per DOC-SIZE-01-v1: Tests for extracted tasks_crud_verify.py.
Tests: task_verify, session_sync_todos.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def force_json_output():
    """Force JSON output format for predictable test results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


def _get_tools():
    """Register tools and return them by name."""
    from governance.mcp_tools.tasks_crud_verify import register_task_verify_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_task_verify_tools(MockMCP())
    return tools


class TestTaskVerify:
    """Tests for task_verify MCP tool."""

    def test_registration(self):
        tools = _get_tools()
        assert "task_verify" in tools

    def test_missing_verification_method(self):
        tools = _get_tools()
        result = json.loads(tools["task_verify"]("T-1", "", "some evidence"))
        assert "error" in result
        assert "verification_method" in result["error"]

    def test_missing_evidence(self):
        tools = _get_tools()
        result = json.loads(tools["task_verify"]("T-1", "pytest", ""))
        assert "error" in result
        assert "evidence" in result["error"]

    def test_failed_verification(self):
        tools = _get_tools()
        result = json.loads(tools["task_verify"]("T-1", "pytest", "output", test_passed=False))
        assert result["status"] == "VERIFICATION_FAILED"
        assert result["task_id"] == "T-1"

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    @patch("governance.mcp_tools.tasks_crud_verify.log_monitor_event")
    def test_successful_verification(self, mock_log, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_client.update_task.return_value = True
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_verify"]("T-1", "pytest", "All passed"))
        assert result["verified"] is True
        assert result["status"] == "DONE"

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    @patch("governance.mcp_tools.tasks_crud_verify.log_monitor_event")
    def test_task_not_in_typedb(self, mock_log, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_client.update_task.return_value = False
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_verify"]("T-NONE", "curl", "200 OK"))
        assert result["verified"] is False
        assert "not found in TypeDB" in result.get("error", "")


class TestSessionSyncTodos:
    """Tests for session_sync_todos MCP tool."""

    def test_registration(self):
        tools = _get_tools()
        assert "session_sync_todos" in tools

    def test_invalid_json(self):
        tools = _get_tools()
        result = json.loads(tools["session_sync_todos"]("S-1", "not json"))
        assert "error" in result
        assert "Invalid JSON" in result["error"]

    def test_non_array_json(self):
        tools = _get_tools()
        result = json.loads(tools["session_sync_todos"]("S-1", '{"a": 1}'))
        assert "error" in result
        assert "array" in result["error"]

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_creates_new_tasks(self, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        todos = json.dumps([
            {"content": "Fix bug", "status": "pending"},
            {"content": "Add test", "status": "completed"},
        ])
        result = json.loads(tools["session_sync_todos"]("S-1", todos))
        assert result["summary"]["created"] == 2
        assert result["summary"]["skipped"] == 0

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_skips_empty_content(self, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        todos = json.dumps([{"content": "", "status": "pending"}])
        result = json.loads(tools["session_sync_todos"]("S-1", todos))
        assert result["summary"]["skipped"] == 1
        assert result["summary"]["created"] == 0

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_updates_existing_task(self, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "pending"
        mock_client.get_task.return_value = mock_task
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        todos = json.dumps([{"content": "Task X", "status": "completed"}])
        result = json.loads(tools["session_sync_todos"]("S-1", todos))
        assert result["summary"]["updated"] == 1

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_skips_unchanged_task(self, mock_ctx):
        tools = _get_tools()
        mock_client = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "TODO"
        mock_client.get_task.return_value = mock_task
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        todos = json.dumps([{"content": "Task X", "status": "pending"}])
        result = json.loads(tools["session_sync_todos"]("S-1", todos))
        assert result["summary"]["skipped"] == 1

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_exception_returns_error(self, mock_ctx):
        """Outer except block returns error when TypeDB connection fails."""
        tools = _get_tools()
        mock_ctx.return_value.__enter__ = MagicMock(
            side_effect=RuntimeError("TypeDB connection refused"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        todos = json.dumps([{"content": "Fix bug", "status": "pending"}])
        result = json.loads(tools["session_sync_todos"]("S-1", todos))
        assert "error" in result
        assert "session_sync_todos failed" in result["error"]

    @patch("governance.mcp_tools.tasks_crud_verify.typedb_client")
    def test_verify_exception_returns_error(self, mock_ctx):
        """task_verify returns error on TypeDB exception."""
        tools = _get_tools()
        mock_ctx.return_value.__enter__ = MagicMock(
            side_effect=RuntimeError("TypeDB timeout"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["task_verify"]("T-1", "pytest", "output"))
        assert "error" in result
        assert "task_verify failed" in result["error"]
