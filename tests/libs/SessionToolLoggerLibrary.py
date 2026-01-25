"""
RF-004: Robot Framework Library for Session Tool Logger.

Wraps hooks_utils/session_tool_logger.py for Robot Framework tests.
Per GAP-SESSION-THOUGHT-001: Hook integration for auto-logging.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SessionToolLoggerLibrary:
    """Robot Framework library for Session Tool Logger testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._captured = {}
        self._env_patches = []

    def module_imports_successfully(self) -> bool:
        """Verify module can be imported."""
        try:
            from hooks_utils import session_tool_logger
            return True
        except ImportError:
            return False

    def parse_tool_input_with_env(self, json_str: str) -> Dict[str, Any]:
        """Parse tool input from JSON string.

        Args:
            json_str: JSON string to set in CLAUDE_TOOL_INPUT

        Returns:
            Parsed dict from parse_tool_input()
        """
        from hooks_utils.session_tool_logger import parse_tool_input

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json_str}):
            return parse_tool_input()

    def parse_tool_input_empty(self) -> Dict[str, Any]:
        """Parse empty tool input."""
        from hooks_utils.session_tool_logger import parse_tool_input

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": ""}, clear=True):
            return parse_tool_input()

    def parse_tool_input_invalid(self, invalid_str: str) -> Dict[str, Any]:
        """Parse invalid JSON tool input."""
        from hooks_utils.session_tool_logger import parse_tool_input

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": invalid_str}):
            return parse_tool_input()

    def get_tool_name_with_env(self, tool_name: str) -> str:
        """Get tool name from environment.

        Args:
            tool_name: Name to set in CLAUDE_TOOL_NAME

        Returns:
            Result from get_tool_name()
        """
        from hooks_utils.session_tool_logger import get_tool_name

        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": tool_name}):
            return get_tool_name()

    def get_active_session_with_state(self, session_id: str) -> Optional[str]:
        """Get active session ID from mocked state.

        Args:
            session_id: Session ID to include in state

        Returns:
            Result from get_active_session_id()
        """
        from hooks_utils.session_tool_logger import get_active_session_id

        state = {
            "active_sessions": [session_id],
            "last_session": session_id
        }
        with patch('hooks_utils.session_tool_logger.load_session_state', return_value=state):
            return get_active_session_id()

    def get_active_session_no_state(self) -> Optional[str]:
        """Get active session ID with empty state."""
        from hooks_utils.session_tool_logger import get_active_session_id

        with patch('hooks_utils.session_tool_logger.load_session_state', return_value={}):
            return get_active_session_id()

    def log_tool_call_success(self) -> bool:
        """Test successful tool call logging."""
        from hooks_utils.session_tool_logger import log_tool_call

        mock_collector = Mock()
        mock_collector.capture_tool_call = Mock(return_value={"logged": True})

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=mock_collector):
            result = log_tool_call(
                tool_name="Bash",
                arguments={"command": "ls"},
                duration_ms=100,
                success=True
            )
            return result is True

    def log_tool_call_no_session(self) -> bool:
        """Test tool call logging with no session returns False."""
        from hooks_utils.session_tool_logger import log_tool_call

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=None):
            result = log_tool_call(
                tool_name="Bash",
                arguments={},
                duration_ms=0,
                success=True
            )
            return result is False

    def log_tool_call_typedb_down(self) -> bool:
        """Test tool call logging when TypeDB is down returns False without error."""
        from hooks_utils.session_tool_logger import log_tool_call

        mock_collector = Mock()
        mock_collector.capture_tool_call = Mock(side_effect=ConnectionError("TypeDB down"))

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=mock_collector):
            try:
                result = log_tool_call(
                    tool_name="Bash",
                    arguments={},
                    duration_ms=0,
                    success=True
                )
                return result is False
            except ConnectionError:
                return False  # Should not raise

    def hook_completes_under_500ms(self) -> Dict[str, Any]:
        """Test hook completes in under 500ms.

        Returns:
            Dict with 'passed' bool and 'elapsed_ms' float
        """
        from hooks_utils.session_tool_logger import main

        with patch('hooks_utils.session_tool_logger.get_active_session_id', return_value=None):
            with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Test", "CLAUDE_TOOL_INPUT": "{}"}):
                start = time.time()
                main()
                elapsed_ms = (time.time() - start) * 1000
                return {
                    "passed": elapsed_ms < 500,
                    "elapsed_ms": elapsed_ms
                }

    def full_flow_captures_all_fields(self) -> Dict[str, Any]:
        """Test full flow captures all required fields.

        Returns:
            Dict with captured fields and 'all_present' bool
        """
        from hooks_utils.session_tool_logger import log_tool_call

        captured = {}

        def mock_capture(tool_name, arguments, result, duration_ms, success, correlation_id, applied_rules):
            captured.update({
                "tool_name": tool_name,
                "arguments": arguments,
                "duration_ms": duration_ms,
                "success": success
            })
            return {"logged": True}

        mock_collector = Mock()
        mock_collector.capture_tool_call = mock_capture

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=mock_collector):
            log_tool_call(
                tool_name="Read",
                arguments={"file_path": "/test.py"},
                duration_ms=150,
                success=True
            )

        all_present = (
            captured.get("tool_name") == "Read" and
            captured.get("arguments", {}).get("file_path") == "/test.py" and
            captured.get("duration_ms") == 150 and
            captured.get("success") is True
        )

        return {
            "captured": captured,
            "all_present": all_present
        }
