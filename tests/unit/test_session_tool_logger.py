"""
Unit Tests for Session Tool Logger Hook.

Per GAP-SESSION-THOUGHT-001: Hook integration for auto-logging.
Per TEST-FIX-01-v1: Tests first, then implementation.
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSessionToolLoggerInput:
    """Test parsing of hook input data."""

    @pytest.mark.unit
    def test_parse_tool_input_from_env(self):
        """GIVEN CLAUDE_TOOL_INPUT env var with JSON
        WHEN parse_tool_input() is called
        THEN returns parsed dict with tool name and args"""
        from hooks_utils.session_tool_logger import parse_tool_input

        input_data = {
            "command": "ls -la",
            "timeout": 30000
        }
        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": json.dumps(input_data)}):
            result = parse_tool_input()
            assert result["command"] == "ls -la"
            assert result["timeout"] == 30000

    @pytest.mark.unit
    def test_parse_empty_tool_input(self):
        """GIVEN empty CLAUDE_TOOL_INPUT
        WHEN parse_tool_input() is called
        THEN returns empty dict"""
        from hooks_utils.session_tool_logger import parse_tool_input

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": ""}, clear=True):
            result = parse_tool_input()
            assert result == {}

    @pytest.mark.unit
    def test_parse_invalid_json(self):
        """GIVEN invalid JSON in CLAUDE_TOOL_INPUT
        WHEN parse_tool_input() is called
        THEN returns dict with raw value"""
        from hooks_utils.session_tool_logger import parse_tool_input

        with patch.dict(os.environ, {"CLAUDE_TOOL_INPUT": "not-json"}):
            result = parse_tool_input()
            assert result.get("raw") == "not-json"

    @pytest.mark.unit
    def test_get_tool_name_from_env(self):
        """GIVEN CLAUDE_TOOL_NAME env var
        WHEN get_tool_name() is called
        THEN returns the tool name"""
        from hooks_utils.session_tool_logger import get_tool_name

        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Bash"}):
            assert get_tool_name() == "Bash"


class TestSessionToolLoggerSession:
    """Test session detection and logging."""

    @pytest.mark.unit
    def test_get_active_session_from_state(self):
        """GIVEN an active session in session state
        WHEN get_active_session_id() is called
        THEN returns the session ID"""
        from hooks_utils.session_tool_logger import get_active_session_id

        state = {
            "active_sessions": ["SESSION-2026-01-21-QUALITY"],
            "last_session": "SESSION-2026-01-21-QUALITY"
        }
        with patch('hooks_utils.session_tool_logger.load_session_state', return_value=state):
            result = get_active_session_id()
            assert result == "SESSION-2026-01-21-QUALITY"

    @pytest.mark.unit
    def test_no_active_session_returns_none(self):
        """GIVEN no active session
        WHEN get_active_session_id() is called
        THEN returns None (silent fail)"""
        from hooks_utils.session_tool_logger import get_active_session_id

        with patch('hooks_utils.session_tool_logger.load_session_state', return_value={}):
            result = get_active_session_id()
            assert result is None


class TestSessionToolLoggerWrite:
    """Test TypeDB write operations."""

    @pytest.mark.unit
    def test_log_tool_call_success(self):
        """GIVEN active session and valid tool call
        WHEN log_tool_call() is called
        THEN writes to TypeDB and returns True"""
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
            assert result is True
            mock_collector.capture_tool_call.assert_called_once()

    @pytest.mark.unit
    def test_log_tool_call_silent_fail_no_session(self):
        """GIVEN no active session
        WHEN log_tool_call() is called
        THEN returns False without error"""
        from hooks_utils.session_tool_logger import log_tool_call

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=None):
            result = log_tool_call(
                tool_name="Bash",
                arguments={},
                duration_ms=0,
                success=True
            )
            assert result is False

    @pytest.mark.unit
    def test_log_tool_call_silent_fail_typedb_down(self):
        """GIVEN TypeDB unavailable
        WHEN log_tool_call() is called
        THEN returns False without raising exception"""
        from hooks_utils.session_tool_logger import log_tool_call

        mock_collector = Mock()
        mock_collector.capture_tool_call = Mock(side_effect=ConnectionError("TypeDB down"))

        with patch('hooks_utils.session_tool_logger.get_session_collector', return_value=mock_collector):
            # Should not raise, just return False
            result = log_tool_call(
                tool_name="Bash",
                arguments={},
                duration_ms=0,
                success=True
            )
            assert result is False


class TestSessionToolLoggerPerformance:
    """Test performance requirements."""

    @pytest.mark.unit
    def test_hook_completes_under_500ms(self):
        """GIVEN normal conditions
        WHEN hook executes
        THEN completes in under 500ms"""
        import time
        from hooks_utils.session_tool_logger import main

        # Mock everything to be fast
        with patch('hooks_utils.session_tool_logger.get_active_session_id', return_value=None):
            with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Test", "CLAUDE_TOOL_INPUT": "{}"}):
                start = time.time()
                main()
                elapsed = (time.time() - start) * 1000
                assert elapsed < 500, f"Hook took {elapsed}ms, exceeds 500ms limit"


class TestSessionToolLoggerIntegration:
    """Integration tests with session collector."""

    @pytest.mark.integration
    def test_full_flow_with_mock_collector(self):
        """GIVEN active session with mock collector
        WHEN tool call is logged
        THEN captures all required fields"""
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

            assert captured["tool_name"] == "Read"
            assert captured["arguments"]["file_path"] == "/test.py"
            assert captured["duration_ms"] == 150
            assert captured["success"] is True
