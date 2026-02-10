"""
Tests for MCP Auto-Session Capture (GAP-GOVSESS-CAPTURE-001).

Captures non-chat MCP tool calls in governance sessions automatically.
When MCP tools are called directly (not through chat), an auto-session
is created and tool calls are recorded.

Created: 2026-02-11
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestMCPAutoSessionTracker:
    """Core auto-session tracking logic."""

    def test_tracker_creates_session_on_first_call(self):
        """First MCP tool call should auto-create a session."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        assert tracker.active_session_id is not None
        assert tracker.active_session_id.startswith("SESSION-")
        assert "-MCP-" in tracker.active_session_id

    def test_tracker_reuses_existing_session(self):
        """Subsequent calls within timeout reuse the same session."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        first_id = tracker.active_session_id
        tracker.track("rule_update", "gov-core")
        assert tracker.active_session_id == first_id

    def test_tracker_records_tool_calls(self):
        """Tool calls are recorded in the session."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        tracker.track("task_update", "gov-tasks")
        assert len(tracker.tool_calls) == 2
        assert tracker.tool_calls[0]["tool_name"] == "rule_create"
        assert tracker.tool_calls[1]["tool_name"] == "task_update"

    def test_tracker_creates_new_session_after_timeout(self):
        """After timeout, a new session is created."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker(timeout_seconds=60)
        tracker.track("rule_create", "gov-core")
        first_id = tracker.active_session_id
        # Simulate timeout by backdating last_activity
        tracker._last_activity = datetime.now() - timedelta(seconds=120)
        tracker.track("task_create", "gov-tasks")
        assert tracker.active_session_id != first_id

    def test_tracker_ends_session(self):
        """Ending a session marks it as completed."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        sid = tracker.active_session_id
        summary = tracker.end_session()
        assert summary["session_id"] == sid
        assert summary["tool_call_count"] == 1
        assert tracker.active_session_id is None

    def test_tracker_end_no_session_is_noop(self):
        """Ending when no session is active returns None."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        assert tracker.end_session() is None

    def test_tracker_generates_descriptive_session_id(self):
        """Session ID includes date and MCP indicator."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        sid = tracker.active_session_id
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in sid
        assert "MCP" in sid

    def test_tracker_records_server_name(self):
        """Tool calls include the MCP server name."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core")
        assert tracker.tool_calls[0]["server"] == "gov-core"


class TestMCPAutoSessionPersistence:
    """Integration with session service layer."""

    def test_persist_creates_session_in_store(self):
        """Auto-session should persist to _sessions_store."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        from governance.stores import _sessions_store

        tracker = MCPAutoSessionTracker()
        # Clear any pre-existing test sessions
        test_keys = [k for k in _sessions_store if "MCP-AUTO" in k]
        for k in test_keys:
            _sessions_store.pop(k, None)

        tracker.track("rule_create", "gov-core", persist=True)
        sid = tracker.active_session_id
        assert sid in _sessions_store
        assert _sessions_store[sid]["status"] == "ACTIVE"
        assert "MCP" in _sessions_store[sid].get("description", "")

        # Cleanup
        _sessions_store.pop(sid, None)
        tracker.end_session()

    def test_persist_records_tool_calls_in_store(self):
        """Tool calls should be visible in _sessions_store."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        from governance.stores import _sessions_store

        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core", persist=True)
        tracker.track("task_update", "gov-tasks", persist=True)
        sid = tracker.active_session_id

        store_data = _sessions_store.get(sid, {})
        assert len(store_data.get("tool_calls", [])) == 2

        # Cleanup
        _sessions_store.pop(sid, None)
        tracker.end_session()

    def test_end_session_marks_completed_in_store(self):
        """Ending session should set status=COMPLETED in store."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        from governance.stores import _sessions_store

        tracker = MCPAutoSessionTracker()
        tracker.track("rule_create", "gov-core", persist=True)
        sid = tracker.active_session_id
        tracker.end_session(persist=True)

        store_data = _sessions_store.get(sid, {})
        assert store_data.get("status") == "COMPLETED"

        # Cleanup
        _sessions_store.pop(sid, None)


class TestGlobalMCPTracker:
    """Module-level convenience functions."""

    def test_track_mcp_tool_call_function(self):
        """Module-level track function creates/uses tracker."""
        from governance.mcp_tools import auto_session
        # Reset global tracker
        auto_session._global_tracker = None
        auto_session.track_mcp_tool_call("rule_create", "gov-core")
        assert auto_session._global_tracker is not None
        assert auto_session._global_tracker.active_session_id is not None
        # Cleanup
        auto_session._global_tracker.end_session()
        auto_session._global_tracker = None

    def test_end_mcp_session_function(self):
        """Module-level end function ends active session."""
        from governance.mcp_tools import auto_session
        auto_session._global_tracker = None
        auto_session.track_mcp_tool_call("rule_create", "gov-core")
        result = auto_session.end_mcp_session()
        assert result is not None
        assert result["tool_call_count"] == 1
        auto_session._global_tracker = None
