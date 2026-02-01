"""
Tests for chat session bridge.

Per A.2: Create session bridge for chat operations.
Verifies:
- start_chat_session creates a SessionCollector
- record_chat_tool_call wraps capture_tool_call
- record_chat_thought wraps capture_thought
- end_chat_session generates log and syncs
- Session is stored in _sessions_store

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestStartChatSession:
    """Tests for starting a governance session from chat."""

    def test_start_creates_collector(self):
        """start_chat_session should create a SessionCollector instance."""
        from governance.routes.chat.session_bridge import start_chat_session
        collector = start_chat_session("agent-curator", "Testing governance")
        assert collector is not None
        assert hasattr(collector, "session_id")
        assert hasattr(collector, "capture_tool_call")

    def test_start_sets_topic(self):
        """Session topic should be derived from the chat topic."""
        from governance.routes.chat.session_bridge import start_chat_session
        collector = start_chat_session("agent-curator", "Reviewing rules")
        assert "CHAT" in collector.topic or "chat" in collector.topic.lower()

    def test_start_registers_in_sessions_store(self):
        """Started session should appear in _sessions_store."""
        from governance.routes.chat.session_bridge import start_chat_session
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-curator", "Test session")
        assert collector.session_id in _sessions_store
        session_data = _sessions_store[collector.session_id]
        assert session_data["agent_id"] == "agent-curator"
        assert session_data["status"] == "ACTIVE"


class TestRecordToolCall:
    """Tests for recording tool calls during chat."""

    def test_record_tool_call_delegates(self):
        """record_chat_tool_call should delegate to collector.capture_tool_call."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
        )
        collector = start_chat_session("agent-1", "Test")
        record_chat_tool_call(
            collector,
            tool_name="/status",
            result="System Status: ...",
            duration_ms=50,
        )
        # Should have at least one tool_call event
        tool_events = [
            e for e in collector.events if e.event_type == "tool_call"
        ]
        assert len(tool_events) >= 1
        assert tool_events[0].metadata.get("tool_name") == "/status"


class TestRecordThought:
    """Tests for recording thoughts during chat."""

    def test_record_thought_delegates(self):
        """record_chat_thought should delegate to collector.capture_thought."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_thought,
        )
        collector = start_chat_session("agent-1", "Test")
        record_chat_thought(
            collector,
            thought="User asked about session data",
            thought_type="observation",
        )
        thought_events = [
            e for e in collector.events if e.event_type == "thought"
        ]
        assert len(thought_events) >= 1


class TestEndChatSession:
    """Tests for ending a chat session."""

    def test_end_updates_store_status(self):
        """end_chat_session should update session status to ENDED."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            end_chat_session,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test")
        sid = collector.session_id
        end_chat_session(collector)
        assert _sessions_store[sid]["status"] == "ENDED"
        assert "end_time" in _sessions_store[sid]
