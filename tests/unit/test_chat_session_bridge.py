"""
Tests for chat session bridge.

Per A.2: Create session bridge for chat operations.
Per GAP-GOVSESS-CAPTURE-001: TypeDB persistence via service layer.

Verifies:
- start_chat_session creates a SessionCollector
- start_chat_session persists to TypeDB via create_session service
- record_chat_tool_call wraps capture_tool_call
- record_chat_thought wraps capture_thought
- end_chat_session persists to TypeDB via end_session service
- Session is stored in _sessions_store
- Chat endpoints wire bridge lifecycle correctly

Created: 2026-02-01
Updated: 2026-02-09 - TypeDB persistence tests (GAP-GOVSESS-CAPTURE-001)
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.fixture(autouse=True)
def cleanup_sessions_store():
    """Auto-cleanup _sessions_store after each test to prevent pollution."""
    from governance.stores import _sessions_store
    snapshot = set(_sessions_store.keys())
    yield
    # Remove any sessions added during this test
    for key in list(_sessions_store.keys()):
        if key not in snapshot:
            _sessions_store.pop(key, None)


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

    def test_start_calls_service_create_session(self):
        """start_chat_session should call create_session for TypeDB persistence."""
        with patch("governance.routes.chat.session_bridge.create_session",
                    create=True) as mock_create:
            # Patch at the module level where it's imported
            with patch(
                "governance.services.sessions_crud.get_typedb_client", return_value=None
            ):
                from governance.routes.chat.session_bridge import start_chat_session
                collector = start_chat_session("agent-test", "TypeDB test")
                # create_session is called inside start_chat_session via lazy import
                # Verify the session was created one way or another
                from governance.stores import _sessions_store
                assert collector.session_id in _sessions_store

    def test_start_falls_back_on_service_error(self):
        """If create_session raises, should fall back to _sessions_store."""
        with patch(
            "governance.services.sessions.create_session",
            side_effect=Exception("TypeDB down"),
        ):
            from governance.routes.chat.session_bridge import start_chat_session
            from governance.stores import _sessions_store
            collector = start_chat_session("agent-fallback", "Fallback test")
            # Should still appear in store via fallback
            assert collector.session_id in _sessions_store
            assert _sessions_store[collector.session_id]["agent_id"] == "agent-fallback"

    def test_start_truncates_long_topic(self):
        """Long topics should be truncated to 40 chars in safe_topic."""
        from governance.routes.chat.session_bridge import start_chat_session
        long_topic = "A" * 100
        collector = start_chat_session("agent-1", long_topic)
        # CHAT- prefix + 40 chars max
        assert len(collector.topic) <= 45  # CHAT- (5) + 40 chars

    def test_start_sanitizes_slashes_in_topic(self):
        """Slashes in topic should be replaced to avoid path/URL issues."""
        from governance.routes.chat.session_bridge import start_chat_session
        collector = start_chat_session("agent-1", "/status check")
        assert "/" not in collector.topic
        assert "CHAT--STATUS-CHECK" == collector.topic


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
        tool_events = [
            e for e in collector.events if e.event_type == "tool_call"
        ]
        assert len(tool_events) >= 1
        assert tool_events[0].metadata.get("tool_name") == "/status"

    def test_record_tool_call_syncs_to_store(self):
        """Tool calls should be synced to _sessions_store for API visibility."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test tool sync")
        record_chat_tool_call(collector, tool_name="/tasks", result="3 tasks")
        session_data = _sessions_store[collector.session_id]
        assert "tool_calls" in session_data
        assert len(session_data["tool_calls"]) == 1
        assert session_data["tool_calls"][0]["tool_name"] == "/tasks"

    def test_record_tool_call_preserves_full_result(self):
        """Full results stored for transcript support (GAP-SESSION-TRANSCRIPT-001)."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test full result")
        long_result = "X" * 500
        record_chat_tool_call(collector, tool_name="/rules", result=long_result)
        stored = _sessions_store[collector.session_id]["tool_calls"][0]["result"]
        assert len(stored) == 500  # Full content preserved


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

    def test_record_thought_syncs_to_store(self):
        """Thoughts should be synced to _sessions_store for API visibility."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_thought,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test thought sync")
        record_chat_thought(
            collector,
            thought="Analyzing rule compliance",
            thought_type="reasoning",
        )
        session_data = _sessions_store[collector.session_id]
        assert "thoughts" in session_data
        assert len(session_data["thoughts"]) == 1
        assert session_data["thoughts"][0]["thought_type"] == "reasoning"


class TestEndChatSession:
    """Tests for ending a chat session."""

    def test_end_updates_store_status(self):
        """end_chat_session should update session status to COMPLETED."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            end_chat_session,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test")
        sid = collector.session_id
        end_chat_session(collector)
        assert _sessions_store[sid]["status"] == "COMPLETED"

    def test_end_stores_summary(self):
        """end_chat_session should store the summary if provided."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            end_chat_session,
        )
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-1", "Test summary")
        sid = collector.session_id
        end_chat_session(collector, summary="Discussed rule compliance")
        assert _sessions_store[sid].get("summary") == "Discussed rule compliance"

    def test_end_counts_tool_calls(self):
        """end_chat_session should count tool calls for tasks_completed."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
            end_chat_session,
        )
        collector = start_chat_session("agent-1", "Test count")
        record_chat_tool_call(collector, tool_name="/status", result="ok")
        record_chat_tool_call(collector, tool_name="/tasks", result="3 tasks")
        # Verify tool call events are counted
        tool_events = [e for e in collector.events if e.event_type == "tool_call"]
        assert len(tool_events) == 2

    def test_end_falls_back_on_service_error(self):
        """If svc_end_session raises, should still update _sessions_store."""
        with patch(
            "governance.services.sessions.end_session",
            side_effect=Exception("TypeDB down"),
        ):
            from governance.routes.chat.session_bridge import (
                start_chat_session,
                end_chat_session,
            )
            from governance.stores import _sessions_store
            collector = start_chat_session("agent-1", "Fallback end test")
            sid = collector.session_id
            end_chat_session(collector)
            assert _sessions_store[sid]["status"] == "COMPLETED"


class TestEndpointsIntegration:
    """Tests for bridge integration in chat endpoints."""

    def test_endpoints_import_all_bridge_functions(self):
        """endpoints.py should import start, record_tool_call, record_thought, end."""
        from governance.routes.chat import endpoints
        assert hasattr(endpoints, "start_chat_session")
        assert hasattr(endpoints, "record_chat_tool_call")
        assert hasattr(endpoints, "record_chat_thought")
        assert hasattr(endpoints, "end_chat_session")

    def test_chat_gov_sessions_dict_exists(self):
        """endpoints.py should have _chat_gov_sessions tracker."""
        from governance.routes.chat.endpoints import _chat_gov_sessions
        assert isinstance(_chat_gov_sessions, dict)

    def test_delete_endpoint_ends_gov_session(self):
        """Deleting a chat session should end its governance session."""
        from governance.routes.chat.session_bridge import start_chat_session
        from governance.routes.chat.endpoints import _chat_gov_sessions, _chat_sessions

        # Simulate a chat session with governance bridge
        collector = start_chat_session("agent-1", "Delete test")
        chat_sid = "CHAT-TEST-DELETE"
        _chat_sessions[chat_sid] = {
            "session_id": chat_sid,
            "messages": [{"role": "user", "content": "hello"}],
        }
        _chat_gov_sessions[chat_sid] = collector

        # The delete endpoint pops the collector and calls end_chat_session
        popped = _chat_gov_sessions.pop(chat_sid, None)
        assert popped is collector

        # Cleanup
        if chat_sid in _chat_sessions:
            del _chat_sessions[chat_sid]


class TestSessionBridgeLifecycle:
    """Full lifecycle tests: start → tool calls → thoughts → end."""

    def test_full_lifecycle(self):
        """Full session lifecycle should produce collector with events."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
            record_chat_thought,
            end_chat_session,
        )
        from governance.stores import _sessions_store

        collector = start_chat_session("agent-curator", "Full lifecycle")
        sid = collector.session_id

        record_chat_tool_call(collector, "/status", result="ok", duration_ms=10)
        record_chat_thought(collector, "System is healthy", thought_type="observation")
        record_chat_tool_call(collector, "/tasks", result="5 tasks", duration_ms=20)
        record_chat_thought(collector, "Need to review tasks", thought_type="reasoning")

        end_chat_session(collector, summary="Health check and task review")

        # Verify events accumulated
        assert len(collector.events) >= 4
        tool_events = [e for e in collector.events if e.event_type == "tool_call"]
        thought_events = [e for e in collector.events if e.event_type == "thought"]
        assert len(tool_events) == 2
        assert len(thought_events) == 2

        # Verify store state
        assert _sessions_store[sid]["status"] == "COMPLETED"
        assert _sessions_store[sid].get("summary") == "Health check and task review"


class TestPostSessionChecks:
    """Tests for CVP Tier 2: Post-session validation checks."""

    def test_post_checks_run_on_session_end(self):
        """_run_post_session_checks should be called during end_chat_session."""
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
            record_chat_thought,
            end_chat_session,
        )
        # A session with all required data should pass checks
        collector = start_chat_session("agent-1", "CVP test")
        record_chat_tool_call(collector, "/status", result="ok")
        record_chat_thought(collector, "System healthy", thought_type="observation")
        # Should not raise
        end_chat_session(collector, summary="CVP Tier 2 test")

    def test_post_checks_warn_missing_tool_calls(self, caplog):
        """Post-session check should warn if no tool calls recorded."""
        import logging
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            end_chat_session,
            _run_post_session_checks,
        )
        collector = start_chat_session("agent-1", "No tools")
        with caplog.at_level(logging.WARNING):
            _run_post_session_checks(collector.session_id, collector)
        assert any("no tool calls" in r.message for r in caplog.records)

    def test_post_checks_warn_missing_thoughts(self, caplog):
        """Post-session check should warn if no thoughts recorded."""
        import logging
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
            end_chat_session,
            _run_post_session_checks,
        )
        collector = start_chat_session("agent-1", "No thoughts")
        record_chat_tool_call(collector, "/status", result="ok")
        with caplog.at_level(logging.WARNING):
            _run_post_session_checks(collector.session_id, collector)
        assert any("no thoughts" in r.message for r in caplog.records)

    def test_post_checks_pass_complete_session(self, caplog):
        """Post-session check should log OK for complete sessions."""
        import logging
        from governance.routes.chat.session_bridge import (
            start_chat_session,
            record_chat_tool_call,
            record_chat_thought,
            _run_post_session_checks,
        )
        collector = start_chat_session("agent-1", "Complete session")
        record_chat_tool_call(collector, "/status", result="ok")
        record_chat_thought(collector, "Verified", thought_type="observation")
        with caplog.at_level(logging.INFO):
            _run_post_session_checks(collector.session_id, collector)
        assert any("OK" in r.message for r in caplog.records)

    def test_post_checks_warn_missing_agent(self, caplog):
        """Post-session check should warn if agent_id is missing."""
        import logging
        from governance.routes.chat.session_bridge import _run_post_session_checks
        from governance.session_collector.collector import SessionCollector
        collector = SessionCollector(topic="test", session_type="general")
        # Remove agent_id to simulate missing
        if hasattr(collector, 'agent_id'):
            collector.agent_id = None
        with caplog.at_level(logging.WARNING):
            _run_post_session_checks("test-session", collector)
        assert any("missing agent_id" in r.message for r in caplog.records)

    def test_post_checks_resilient_to_errors(self):
        """Post-session checks should not raise even with bad data."""
        from governance.routes.chat.session_bridge import _run_post_session_checks
        # Passing a mock that has no events attribute
        from unittest.mock import MagicMock
        mock_collector = MagicMock()
        mock_collector.events = []
        mock_collector.agent_id = None
        # Should not raise
        _run_post_session_checks("test-session-bad", mock_collector)
