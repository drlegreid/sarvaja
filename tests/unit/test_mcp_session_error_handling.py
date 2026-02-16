"""TDD Tests: MCP session tools error handling.

Gap: MCP tools in sessions_core.py don't wrap collector calls in try/except.
Fix: Catch exceptions, return formatted error instead of crashing.
"""
from unittest.mock import patch, MagicMock

import pytest


def _register_tools():
    """Register MCP tools and return captured tool functions."""
    mock_mcp = MagicMock()
    captured_tools = {}

    def capture_tool():
        def decorator(fn):
            captured_tools[fn.__name__] = fn
            return fn
        return decorator

    mock_mcp.tool = capture_tool

    from governance.mcp_tools.sessions_core import register_session_core_tools
    register_session_core_tools(mock_mcp)
    return captured_tools


class TestMCPSessionStartErrorHandling:
    """session_start returns formatted error on collector failure."""

    @patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", True)
    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    def test_collector_exception_returns_error(self, mock_get_session):
        """If get_or_create_session throws, return error string, don't crash."""
        mock_get_session.side_effect = RuntimeError("TypeDB connection lost")
        tools = _register_tools()

        result = tools["session_start"]("test-topic")
        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "session_start failed" in result


class TestMCPSessionDecisionErrorHandling:
    """session_decision returns formatted error on collector failure."""

    @patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", True)
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    def test_capture_decision_exception_returns_error(self, mock_get_session, mock_list):
        """If capture_decision throws, return error string."""
        mock_list.return_value = ["SESSION-2026-02-15-TEST"]
        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-15-TEST"
        mock_collector.capture_decision.side_effect = RuntimeError("TypeDB write failed")
        mock_get_session.return_value = mock_collector
        tools = _register_tools()

        result = tools["session_decision"](
            "DEC-001", "Test Decision", "context", "rationale"
        )
        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "session_decision failed" in result


class TestMCPSessionEndErrorHandling:
    """session_end returns formatted error on end_session failure."""

    @patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", True)
    @patch("governance.mcp_tools.sessions_core.end_session")
    def test_end_session_exception_returns_error(self, mock_end):
        """If end_session throws, return error string."""
        mock_end.side_effect = RuntimeError("Evidence write failed")
        tools = _register_tools()

        result = tools["session_end"]("test-topic")
        assert isinstance(result, str)
        assert "error" in result.lower()
        assert "session_end failed" in result
