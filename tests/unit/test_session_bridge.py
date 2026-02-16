"""
Unit tests for Chat Session Bridge.

Per DOC-SIZE-01-v1: Tests for routes/chat/session_bridge.py module.
Tests: start_chat_session, record_chat_tool_call, record_chat_thought,
       end_chat_session, _run_post_session_checks.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

_P = "governance.routes.chat.session_bridge"


@pytest.fixture(autouse=True)
def _reset_store():
    with patch(f"{_P}._sessions_store", {}) as store:
        yield store


# ── start_chat_session ───────────────────────────────────────────


class TestStartChatSession:
    def test_creates_collector(self, _reset_store):
        from governance.routes.chat.session_bridge import start_chat_session
        with patch(f"{_P}.SessionCollector") as MockCollector, \
             patch("governance.services.sessions.create_session"):
            mock_instance = MagicMock()
            mock_instance.session_id = "SESSION-2026-02-11-CHAT-TEST"
            mock_instance.start_time = datetime(2026, 2, 11)
            MockCollector.return_value = mock_instance
            result = start_chat_session(agent_id="AGENT-001", topic="Test Topic")
        assert result == mock_instance
        assert "SESSION-2026-02-11-CHAT-TEST" in _reset_store

    def test_stores_session_data(self, _reset_store):
        from governance.routes.chat.session_bridge import start_chat_session
        with patch(f"{_P}.SessionCollector") as MockCollector, \
             patch("governance.services.sessions.create_session"):
            mock_instance = MagicMock()
            mock_instance.session_id = "SESSION-TEST"
            mock_instance.start_time = datetime(2026, 2, 11)
            MockCollector.return_value = mock_instance
            start_chat_session(agent_id="AGENT-001", topic="Test Topic")
        assert _reset_store["SESSION-TEST"]["agent_id"] == "AGENT-001"
        assert _reset_store["SESSION-TEST"]["status"] == "ACTIVE"

    def test_typedb_failure_continues(self, _reset_store):
        from governance.routes.chat.session_bridge import start_chat_session
        with patch(f"{_P}.SessionCollector") as MockCollector, \
             patch("governance.services.sessions.create_session", side_effect=Exception("db fail")):
            mock_instance = MagicMock()
            mock_instance.session_id = "SESSION-FAIL"
            mock_instance.start_time = datetime(2026, 2, 11)
            MockCollector.return_value = mock_instance
            result = start_chat_session(agent_id="A-1", topic="Fail test")
        assert result is not None
        assert "SESSION-FAIL" in _reset_store

    def test_sanitizes_topic(self, _reset_store):
        from governance.routes.chat.session_bridge import start_chat_session
        with patch(f"{_P}.SessionCollector") as MockCollector, \
             patch("governance.services.sessions.create_session"):
            mock_instance = MagicMock()
            mock_instance.session_id = "SESSION-TEST"
            mock_instance.start_time = datetime(2026, 2, 11)
            MockCollector.return_value = mock_instance
            start_chat_session(agent_id="A-1", topic="hello world/test")
        # SessionCollector is called with sanitized topic
        call_kwargs = MockCollector.call_args.kwargs
        assert " " not in call_kwargs["topic"]
        assert "/" not in call_kwargs["topic"]


# ── record_chat_tool_call ────────────────────────────────────────


class TestRecordChatToolCall:
    def test_records_tool_call(self, _reset_store):
        from governance.routes.chat.session_bridge import record_chat_tool_call
        collector = MagicMock()
        collector.session_id = "SESSION-TC"
        _reset_store["SESSION-TC"] = {"session_id": "SESSION-TC"}
        record_chat_tool_call(collector, tool_name="/status", arguments={"a": 1})
        collector.capture_tool_call.assert_called_once()
        assert len(_reset_store["SESSION-TC"]["tool_calls"]) == 1

    def test_preserves_full_result(self, _reset_store):
        """Full results stored for transcript support (GAP-SESSION-TRANSCRIPT-001)."""
        from governance.routes.chat.session_bridge import record_chat_tool_call
        collector = MagicMock()
        collector.session_id = "SESSION-TC"
        _reset_store["SESSION-TC"] = {"session_id": "SESSION-TC"}
        long_result = "x" * 300
        record_chat_tool_call(collector, tool_name="/t", result=long_result)
        stored_result = _reset_store["SESSION-TC"]["tool_calls"][0]["result"]
        assert len(stored_result) == 300  # Full content preserved

    def test_no_store_entry(self, _reset_store):
        from governance.routes.chat.session_bridge import record_chat_tool_call
        collector = MagicMock()
        collector.session_id = "SESSION-MISSING"
        record_chat_tool_call(collector, tool_name="/t")
        # No error, just no store update
        assert "SESSION-MISSING" not in _reset_store

    def test_multiple_calls(self, _reset_store):
        from governance.routes.chat.session_bridge import record_chat_tool_call
        collector = MagicMock()
        collector.session_id = "SESSION-TC"
        _reset_store["SESSION-TC"] = {"session_id": "SESSION-TC"}
        record_chat_tool_call(collector, tool_name="/a")
        record_chat_tool_call(collector, tool_name="/b")
        assert len(_reset_store["SESSION-TC"]["tool_calls"]) == 2


# ── record_chat_thought ──────────────────────────────────────────


class TestRecordChatThought:
    def test_records_thought(self, _reset_store):
        from governance.routes.chat.session_bridge import record_chat_thought
        collector = MagicMock()
        collector.session_id = "SESSION-TH"
        _reset_store["SESSION-TH"] = {"session_id": "SESSION-TH"}
        record_chat_thought(collector, thought="Analyzing query",
                            thought_type="reasoning", confidence=0.9)
        collector.capture_thought.assert_called_once()
        assert len(_reset_store["SESSION-TH"]["thoughts"]) == 1
        assert _reset_store["SESSION-TH"]["thoughts"][0]["confidence"] == 0.9

    def test_preserves_full_thought(self, _reset_store):
        """Full thoughts stored for transcript support (GAP-SESSION-TRANSCRIPT-001)."""
        from governance.routes.chat.session_bridge import record_chat_thought
        collector = MagicMock()
        collector.session_id = "SESSION-TH"
        _reset_store["SESSION-TH"] = {"session_id": "SESSION-TH"}
        long_thought = "x" * 600
        record_chat_thought(collector, thought=long_thought)
        stored = _reset_store["SESSION-TH"]["thoughts"][0]["thought"]
        assert len(stored) == 600  # Full content preserved

    def test_no_store_entry(self, _reset_store):
        from governance.routes.chat.session_bridge import record_chat_thought
        collector = MagicMock()
        collector.session_id = "SESSION-MISSING"
        record_chat_thought(collector, thought="test")
        assert "SESSION-MISSING" not in _reset_store


# ── end_chat_session ─────────────────────────────────────────────


class TestEndChatSession:
    def test_ends_session(self, _reset_store):
        from governance.routes.chat.session_bridge import end_chat_session
        collector = MagicMock()
        collector.session_id = "SESSION-END"
        collector.events = []
        collector.generate_session_log.return_value = "/evidence/session.md"
        _reset_store["SESSION-END"] = {"session_id": "SESSION-END", "status": "ACTIVE"}
        with patch("governance.services.sessions.end_session"):
            result = end_chat_session(collector, summary="Done")
        assert result == "/evidence/session.md"
        assert _reset_store["SESSION-END"]["status"] == "COMPLETED"
        assert _reset_store["SESSION-END"]["summary"] == "Done"

    def test_counts_tool_calls(self, _reset_store):
        from governance.routes.chat.session_bridge import end_chat_session
        event1 = MagicMock()
        event1.event_type = "tool_call"
        event2 = MagicMock()
        event2.event_type = "thought"
        collector = MagicMock()
        collector.session_id = "SESSION-END"
        collector.events = [event1, event2]
        collector.generate_session_log.return_value = None
        _reset_store["SESSION-END"] = {"session_id": "SESSION-END", "status": "ACTIVE"}
        with patch("governance.services.sessions.end_session"):
            end_chat_session(collector)
        assert _reset_store["SESSION-END"]["tasks_completed"] == 1

    def test_typedb_failure_continues(self, _reset_store):
        from governance.routes.chat.session_bridge import end_chat_session
        collector = MagicMock()
        collector.session_id = "SESSION-END"
        collector.events = []
        collector.generate_session_log.return_value = None
        _reset_store["SESSION-END"] = {"session_id": "SESSION-END", "status": "ACTIVE"}
        with patch("governance.services.sessions.end_session", side_effect=Exception("fail")):
            end_chat_session(collector)
        assert _reset_store["SESSION-END"]["status"] == "COMPLETED"

    def test_log_generation_failure(self, _reset_store):
        from governance.routes.chat.session_bridge import end_chat_session
        collector = MagicMock()
        collector.session_id = "SESSION-END"
        collector.events = []
        collector.generate_session_log.side_effect = Exception("log fail")
        _reset_store["SESSION-END"] = {"session_id": "SESSION-END", "status": "ACTIVE"}
        with patch("governance.services.sessions.end_session"):
            result = end_chat_session(collector)
        assert result is None

    def test_chromadb_sync_failure(self, _reset_store):
        from governance.routes.chat.session_bridge import end_chat_session
        collector = MagicMock()
        collector.session_id = "SESSION-END"
        collector.events = []
        collector.generate_session_log.return_value = None
        collector.sync_to_chromadb.side_effect = Exception("chroma fail")
        _reset_store["SESSION-END"] = {"session_id": "SESSION-END", "status": "ACTIVE"}
        with patch("governance.services.sessions.end_session"):
            end_chat_session(collector)
        # Should not raise
        assert _reset_store["SESSION-END"]["status"] == "COMPLETED"


# ── _run_post_session_checks ─────────────────────────────────────


class TestPostSessionChecks:
    def test_all_present(self, _reset_store):
        from governance.routes.chat.session_bridge import _run_post_session_checks
        event_tc = MagicMock()
        event_tc.event_type = "tool_call"
        event_th = MagicMock()
        event_th.event_type = "thought"
        collector = MagicMock()
        collector.agent_id = "A-1"
        collector.events = [event_tc, event_th]
        _run_post_session_checks("SESSION-CHK", collector)
        # No assertion needed — just verify no exception

    def test_missing_all(self, _reset_store):
        from governance.routes.chat.session_bridge import _run_post_session_checks
        collector = MagicMock(spec=[])  # no agent_id attribute
        collector.events = []
        _run_post_session_checks("SESSION-CHK", collector)
        # Should log warning but not raise

    def test_exception_handled(self, _reset_store):
        from governance.routes.chat.session_bridge import _run_post_session_checks
        collector = MagicMock()
        type(collector).events = property(lambda self: (_ for _ in ()).throw(Exception("fail")))
        _run_post_session_checks("SESSION-CHK", collector)
        # Should not raise
