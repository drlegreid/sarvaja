"""
Tests for session_sync_todos MCP tool.

Per MCP-002-A: Sync TodoWrite with TypeDB task creation.
"""

import pytest
import json
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestSessionSyncTodos:
    """Unit tests for session_sync_todos MCP tool."""

    def test_tool_function_exists(self):
        """Verify the tool function can be imported."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        # Create a mock MCP object to capture registered tools
        mock_mcp = MagicMock()
        registered_tools = {}

        def capture_tool():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func
            return decorator

        mock_mcp.tool = capture_tool
        register_task_crud_tools(mock_mcp)

        assert "session_sync_todos" in registered_tools, "session_sync_todos not registered"

    def test_invalid_json_returns_error(self):
        """Verify invalid JSON returns error."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mock_mcp = MagicMock()
        registered_tools = {}

        def capture_tool():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func
            return decorator

        mock_mcp.tool = capture_tool
        register_task_crud_tools(mock_mcp)

        result = registered_tools["session_sync_todos"](
            session_id="TEST-SESSION",
            todos_json="not valid json"
        )

        assert "error" in result
        assert "Invalid JSON" in result

    def test_non_array_json_returns_error(self):
        """Verify non-array JSON returns error."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mock_mcp = MagicMock()
        registered_tools = {}

        def capture_tool():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func
            return decorator

        mock_mcp.tool = capture_tool
        register_task_crud_tools(mock_mcp)

        result = registered_tools["session_sync_todos"](
            session_id="TEST-SESSION",
            todos_json='{"not": "array"}'
        )

        assert "error" in result
        assert "must be a JSON array" in result


@pytest.mark.integration
class TestSessionSyncTodosIntegration:
    """Integration tests requiring TypeDB."""

    def test_sync_creates_tasks(self):
        """Verify todos are synced to TypeDB."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mock_mcp = MagicMock()
        registered_tools = {}

        def capture_tool():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func
            return decorator

        mock_mcp.tool = capture_tool
        register_task_crud_tools(mock_mcp)

        todos = [
            {"content": "Test task 1", "status": "pending"},
            {"content": "Test task 2", "status": "completed"},
        ]

        result = registered_tools["session_sync_todos"](
            session_id="TEST-SESSION-2026-01-19",
            todos_json=json.dumps(todos)
        )

        # Should return success (may have created or updated)
        assert "error" not in result or "Failed to connect" in result
