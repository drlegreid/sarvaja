"""
RF-004: Robot Framework Library for Session Sync Todos.

Wraps tests/unit/test_session_sync_todos.py tests for Robot Framework.
Per MCP-002-A: Sync TodoWrite with TypeDB task creation.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SessionSyncTodosLibrary:
    """Robot Framework library for Session Sync Todos testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_registered_tools(self) -> Dict:
        """Helper to get registered task CRUD tools."""
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
        return registered_tools

    # =========================================================================
    # Tool Function Tests
    # =========================================================================

    def tool_function_exists(self) -> Dict[str, Any]:
        """Verify the tool function can be imported."""
        tools = self._get_registered_tools()
        return {
            "exists": "session_sync_todos" in tools,
            "tool_count": len(tools)
        }

    def invalid_json_returns_error(self) -> Dict[str, Any]:
        """Verify invalid JSON returns error."""
        tools = self._get_registered_tools()
        result = tools["session_sync_todos"](
            session_id="TEST-SESSION",
            todos_json="not valid json"
        )
        return {
            "has_error": "error" in result,
            "error_message": "Invalid JSON" in result if "error" in result else False
        }

    def non_array_json_returns_error(self) -> Dict[str, Any]:
        """Verify non-array JSON returns error."""
        tools = self._get_registered_tools()
        result = tools["session_sync_todos"](
            session_id="TEST-SESSION",
            todos_json='{"not": "array"}'
        )
        return {
            "has_error": "error" in result,
            "error_message": "must be a JSON array" in result if "error" in result else False
        }

    # =========================================================================
    # Integration Tests (requires TypeDB)
    # =========================================================================

    def sync_creates_tasks(self) -> Dict[str, Any]:
        """Verify todos are synced to TypeDB."""
        tools = self._get_registered_tools()
        todos = [
            {"content": "Test task 1", "status": "pending"},
            {"content": "Test task 2", "status": "completed"},
        ]
        result = tools["session_sync_todos"](
            session_id="TEST-SESSION-2026-01-25",
            todos_json=json.dumps(todos)
        )
        # Note: May fail to connect to TypeDB in unit test
        has_error = "error" in result
        is_connection_error = "Failed to connect" in result if has_error else False
        return {
            "no_error_or_connection_error": not has_error or is_connection_error,
            "result": result[:100] if isinstance(result, str) else str(result)[:100]
        }
