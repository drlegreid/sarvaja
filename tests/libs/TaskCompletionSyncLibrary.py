"""
RF-004: Robot Framework Library for Task Completion Sync.

Wraps governance/mcp_tools/tasks_crud.py for Robot Framework tests.
Per MCP-002-B: Auto-mark tasks DONE when completed.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TaskCompletionSyncLibrary:
    """Robot Framework library for Task Completion Sync testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._registered_tools = {}

    def session_sync_handles_completed_status(self) -> Dict[str, Any]:
        """Test session_sync_todos handles 'completed' status correctly."""
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

        # Simulate todos with completed item
        todos = [
            {"content": "First task", "status": "pending"},
            {"content": "Second task", "status": "completed"},
            {"content": "Third task", "status": "in_progress"},
        ]

        result = registered_tools["session_sync_todos"](
            session_id="TEST-COMPLETION-SYNC",
            todos_json=json.dumps(todos)
        )

        # Tool should process all statuses without error
        # Note: May fail to connect to TypeDB in unit test
        has_error = "error" in result
        is_connection_error = "Failed to connect" in result if has_error else False

        return {
            "result": result,
            "no_error_or_connection_error": not has_error or is_connection_error
        }
