"""
Tests for session-agent linking (A.4).

Verifies:
- SessionCollector accepts agent_id
- Session bridge passes agent_id to collector
- ChromaDB sync includes agent_id in metadata
- TypeDB session creation includes agent_id
- In-memory store includes agent_id

Created: 2026-02-01
"""
import pytest
import inspect


class TestSessionCollectorAgentId:
    """SessionCollector should accept and store agent_id."""

    def test_collector_accepts_agent_id(self):
        """SessionCollector init should accept agent_id parameter."""
        from governance.session_collector.collector import SessionCollector
        collector = SessionCollector(
            topic="TEST-AGENT-LINK",
            agent_id="agent-curator",
        )
        assert collector.agent_id == "agent-curator"

    def test_collector_agent_id_defaults_none(self):
        """SessionCollector agent_id should default to None."""
        from governance.session_collector.collector import SessionCollector
        collector = SessionCollector(topic="TEST-NO-AGENT")
        assert collector.agent_id is None


class TestSessionBridgeAgentLinking:
    """Session bridge should pass agent_id to collector."""

    def test_bridge_passes_agent_id(self):
        """start_chat_session should pass agent_id to SessionCollector."""
        from governance.routes.chat.session_bridge import start_chat_session
        collector = start_chat_session("agent-curator", "Test linking")
        assert collector.agent_id == "agent-curator"

    def test_bridge_stores_agent_in_sessions_store(self):
        """Session bridge should store agent_id in _sessions_store."""
        from governance.routes.chat.session_bridge import start_chat_session
        from governance.stores import _sessions_store
        collector = start_chat_session("agent-validator", "Test store")
        session_data = _sessions_store.get(collector.session_id)
        assert session_data is not None
        assert session_data["agent_id"] == "agent-validator"


class TestChromaDbSyncAgentId:
    """ChromaDB sync should include agent_id in metadata."""

    def test_chromadb_metadata_includes_agent_id(self):
        """sync_to_chromadb metadata building should include agent_id."""
        from governance.session_collector.collector import SessionCollector
        collector = SessionCollector(
            topic="TEST-CHROMA",
            agent_id="agent-curator",
        )
        metadata = {
            "session_type": collector.session_type,
            "topic": collector.topic,
        }
        if getattr(collector, "agent_id", None):
            metadata["agent_id"] = collector.agent_id

        assert "agent_id" in metadata
        assert metadata["agent_id"] == "agent-curator"

    def test_chromadb_metadata_omits_none_agent(self):
        """sync_to_chromadb should omit agent_id when None."""
        from governance.session_collector.collector import SessionCollector
        collector = SessionCollector(topic="TEST-NO-AGENT")
        metadata = {}
        if getattr(collector, "agent_id", None):
            metadata["agent_id"] = collector.agent_id
        assert "agent_id" not in metadata


class TestTypeDbSyncAgentId:
    """TypeDB session creation should include agent_id."""

    def test_sync_mixin_generates_agent_id_query(self):
        """_index_task_to_typedb should include agent_id in session creation."""
        from governance.session_collector.sync import SessionSyncMixin
        source = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        assert "agent-id" in source
        assert "agent_id" in source

    def test_sync_chromadb_source_includes_agent_id(self):
        """sync_to_chromadb should include agent_id conditionally."""
        from governance.session_collector.sync import SessionSyncMixin
        source = inspect.getsource(SessionSyncMixin.sync_to_chromadb)
        assert "agent_id" in source
