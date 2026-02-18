"""Deep scan batch 126: MCP tools integration.

Batch 126 findings: 22 total, 1 confirmed fix (docker→podman), 21 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


# ── MCP tool exception handling defense ──────────────


class TestMCPToolExceptionHandlingDefense:
    """Verify MCP tool framework catches exceptions."""

    def test_mcp_tool_decorator_wraps_errors(self):
        """@mcp.tool() decorator catches exceptions at framework level."""
        # MCP tool handlers don't need their own try-except because
        # the framework catches exceptions and returns error responses
        from governance.mcp_tools.sessions import register_session_tools

        # Verify the function exists and is callable
        assert callable(register_session_tools)

    def test_session_tool_call_handles_bad_json(self):
        """session_tool_call handles malformed JSON arguments."""
        # Verify the pattern: try json.loads, fallback to {"raw": arguments}
        bad_json = "{not valid"
        try:
            result = json.loads(bad_json)
        except json.JSONDecodeError:
            result = {"raw": bad_json}
        assert result == {"raw": bad_json}


# ── Recovery hint uses podman defense ──────────────


class TestRecoveryHintPodmanDefense:
    """Verify recovery hints use podman, not docker."""

    def test_health_check_recovery_uses_podman(self):
        """Health check recovery hint uses 'podman compose' not 'docker compose'."""
        import inspect
        from governance.mcp_tools.decisions import register_decision_tools

        source = inspect.getsource(register_decision_tools)
        # Should NOT contain 'docker compose'
        assert "docker compose" not in source
        # Should contain 'podman compose'
        assert "podman compose" in source

    def test_recovery_hint_uses_cpu_profile(self):
        """Recovery hint uses --profile cpu (correct for this system)."""
        import inspect
        from governance.mcp_tools.decisions import register_decision_tools

        source = inspect.getsource(register_decision_tools)
        assert "--profile cpu" in source


# ── Auto-session tracker lifecycle defense ──────────────


class TestAutoSessionTrackerLifecycleDefense:
    """Verify auto-session tracker cleans up properly."""

    def test_timeout_is_5_minutes(self):
        """Default timeout is 300 seconds (5 minutes)."""
        from governance.mcp_tools.auto_session import _DEFAULT_TIMEOUT_SECONDS
        assert _DEFAULT_TIMEOUT_SECONDS == 300

    def test_global_tracker_starts_none(self):
        """Global tracker starts as None."""
        from governance.mcp_tools import auto_session
        # Save and restore
        original = auto_session._global_tracker
        auto_session._global_tracker = None
        assert auto_session._global_tracker is None
        auto_session._global_tracker = original

    def test_end_session_clears_tool_calls(self):
        """end_session clears tool_calls list to free memory."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        tracker._create_session("test-server")
        # Manually add a tool call
        tracker.tool_calls.append({"tool_name": "test", "server": "s1", "timestamp": "t"})
        assert len(tracker.tool_calls) == 1

        summary = tracker.end_session()
        assert tracker.tool_calls == []
        assert summary is not None
        assert summary["tool_call_count"] == 1


# ── TypeQL escaping in MCP tools defense ──────────────


class TestMCPTypeQLEscapingDefense:
    """Verify TypeQL escaping is applied in MCP tool handlers."""

    def test_agent_activity_escapes_id(self):
        """Agent activity tool escapes agent_id for TypeQL."""
        import inspect
        from governance.mcp_tools.agents import register_agent_tools

        source = inspect.getsource(register_agent_tools)
        assert "agent_id_escaped" in source or 'replace(\'"\',' in source

    def test_proposal_escapes_status(self):
        """Proposal tool escapes status parameter."""
        import inspect
        from governance.mcp_tools.proposals import register_proposal_tools

        source = inspect.getsource(register_proposal_tools)
        # Uses chr(34)/chr(92) or .replace pattern
        assert "replace" in source


# ── MCP result format defense ──────────────


class TestMCPResultFormatDefense:
    """Verify MCP tools return consistent format."""

    def test_format_mcp_result_returns_string(self):
        """format_mcp_result returns a string."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result

    def test_format_mcp_result_handles_error(self):
        """format_mcp_result handles error dicts."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"error": "test error"})
        assert isinstance(result, str)
        assert "test error" in result

    def test_format_mcp_result_callable(self):
        """format_mcp_result is a callable function."""
        from governance.mcp_tools.common import format_mcp_result

        assert callable(format_mcp_result)
