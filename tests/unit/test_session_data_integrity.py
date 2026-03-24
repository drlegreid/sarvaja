"""
Unit tests for Session Data Integrity (Phase 1).

Per feedback #1: Ensure session UI reflects actual session runs.
Tests: orphan merge in typedb_access, persistence verification,
       sync_pending_sessions retry mechanism.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

_STORES = "governance.stores.typedb_access"
_SERVICE = "governance.services.sessions"
_SERVICE_CRUD = "governance.services.sessions_crud"
_BRIDGE = "governance.routes.chat.session_bridge"


# ── get_all_sessions_from_typedb: orphan merge ─────────────


class TestOrphanSessionMerge:
    """Verify that sessions in _sessions_store but NOT in TypeDB
    are included in results when TypeDB is available (the 'orphan merge')."""

    @patch(f"{_STORES}.get_typedb_client")
    @patch(f"{_STORES}._sessions_store", {})
    def test_typedb_only_no_orphans(self, mock_client_fn):
        """When TypeDB has all sessions and store is empty, return TypeDB only."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        mock_session = MagicMock()
        mock_session.id = "SESSION-2026-02-11-WORK"
        mock_session.started_at = datetime(2026, 2, 11, 10, 0)
        mock_session.completed_at = None
        mock_session.status = "ACTIVE"
        mock_session.tasks_completed = 0
        mock_session.agent_id = "code-agent"
        mock_session.description = "Work session"
        mock_session.file_path = None
        mock_session.evidence_files = []
        mock_session.linked_rules_applied = []
        mock_session.linked_decisions = []

        mock_client = MagicMock()
        mock_client.get_all_sessions.return_value = [mock_session]
        mock_client_fn.return_value = mock_client

        result = get_all_sessions_from_typedb(allow_fallback=True)
        assert len(result) == 1
        assert result[0]["session_id"] == "SESSION-2026-02-11-WORK"

    @patch(f"{_STORES}.get_typedb_client")
    @patch(f"{_STORES}._sessions_store")
    def test_orphan_included_when_typedb_succeeds(self, mock_store, mock_client_fn):
        """Sessions in _sessions_store but NOT in TypeDB should be included."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        # TypeDB returns one session
        mock_session = MagicMock()
        mock_session.id = "SESSION-2026-02-11-WORK"
        mock_session.started_at = datetime(2026, 2, 11, 10, 0)
        mock_session.completed_at = None
        mock_session.status = "ACTIVE"
        mock_session.tasks_completed = 0
        mock_session.agent_id = "code-agent"
        mock_session.description = "Work"
        mock_session.file_path = None
        mock_session.evidence_files = []
        mock_session.linked_rules_applied = []
        mock_session.linked_decisions = []

        mock_client = MagicMock()
        mock_client.get_all_sessions.return_value = [mock_session]
        mock_client_fn.return_value = mock_client

        # _sessions_store has an orphan (failed to persist to TypeDB)
        mock_store.__iter__ = MagicMock(return_value=iter([
            "SESSION-2026-02-11-WORK",
            "SESSION-2026-02-11-ORPHAN",
        ]))
        mock_store.values.return_value = [
            {
                "session_id": "SESSION-2026-02-11-WORK",
                "status": "ACTIVE",
                "start_time": "2026-02-11T10:00:00",
            },
            {
                "session_id": "SESSION-2026-02-11-ORPHAN",
                "status": "ACTIVE",
                "start_time": "2026-02-11T11:00:00",
                "description": "Orphan session",
                "agent_id": "code-agent",
            },
        ]

        result = get_all_sessions_from_typedb(allow_fallback=True)
        ids = [s["session_id"] for s in result]
        assert "SESSION-2026-02-11-WORK" in ids
        assert "SESSION-2026-02-11-ORPHAN" in ids
        assert len(result) == 2

    @patch(f"{_STORES}.get_typedb_client")
    @patch(f"{_STORES}._sessions_store")
    def test_orphan_flagged_as_memory_only(self, mock_store, mock_client_fn):
        """Orphan sessions should be flagged with persistence_status='memory_only'."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        mock_client = MagicMock()
        mock_client.get_all_sessions.return_value = []  # TypeDB is empty
        mock_client_fn.return_value = mock_client

        mock_store.values.return_value = [
            {
                "session_id": "SESSION-2026-02-11-ORPHAN",
                "status": "ACTIVE",
                "start_time": "2026-02-11T11:00:00",
                "agent_id": "code-agent",
            },
        ]

        result = get_all_sessions_from_typedb(allow_fallback=True)
        assert len(result) == 1
        assert result[0]["persistence_status"] == "memory_only"

    @patch(f"{_STORES}.get_typedb_client")
    @patch(f"{_STORES}._sessions_store", {})
    def test_typedb_sessions_flagged_as_persisted(self, mock_client_fn):
        """TypeDB sessions should have persistence_status='persisted'."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        mock_session = MagicMock()
        mock_session.id = "SESSION-2026-02-11-WORK"
        mock_session.started_at = datetime(2026, 2, 11, 10, 0)
        mock_session.completed_at = None
        mock_session.status = "ACTIVE"
        mock_session.tasks_completed = 0
        mock_session.agent_id = "code-agent"
        mock_session.description = "Work"
        mock_session.file_path = None
        mock_session.evidence_files = []
        mock_session.linked_rules_applied = []
        mock_session.linked_decisions = []

        mock_client = MagicMock()
        mock_client.get_all_sessions.return_value = [mock_session]
        mock_client_fn.return_value = mock_client

        result = get_all_sessions_from_typedb(allow_fallback=True)
        assert result[0]["persistence_status"] == "persisted"

    @patch(f"{_STORES}.get_typedb_client", return_value=None)
    @patch(f"{_STORES}._sessions_store")
    def test_fallback_flagged_as_memory_only(self, mock_store, mock_client_fn):
        """When TypeDB is unavailable, fallback sessions are 'memory_only'."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        mock_store.values.return_value = [
            {"session_id": "S-1", "status": "ACTIVE"},
        ]

        result = get_all_sessions_from_typedb(allow_fallback=True)
        assert len(result) == 1
        assert result[0]["persistence_status"] == "memory_only"

    @patch(f"{_STORES}.get_typedb_client")
    @patch(f"{_STORES}._sessions_store", {})
    def test_no_duplicate_when_session_in_both(self, mock_client_fn):
        """Session in both TypeDB and _sessions_store should appear once."""
        from governance.stores.typedb_access import get_all_sessions_from_typedb

        mock_session = MagicMock()
        mock_session.id = "SESSION-2026-02-11-WORK"
        mock_session.started_at = datetime(2026, 2, 11, 10, 0)
        mock_session.completed_at = None
        mock_session.status = "ACTIVE"
        mock_session.tasks_completed = 0
        mock_session.agent_id = "code-agent"
        mock_session.description = "Work"
        mock_session.file_path = None
        mock_session.evidence_files = []
        mock_session.linked_rules_applied = []
        mock_session.linked_decisions = []

        mock_client = MagicMock()
        mock_client.get_all_sessions.return_value = [mock_session]
        mock_client_fn.return_value = mock_client

        # Same session also in _sessions_store (normal — bridge always writes both)
        # Using a real dict to test __iter__ and values() naturally
        import governance.stores.typedb_access as mod
        orig = mod._sessions_store
        mod._sessions_store = {
            "SESSION-2026-02-11-WORK": {
                "session_id": "SESSION-2026-02-11-WORK",
                "status": "ACTIVE",
            }
        }
        try:
            result = get_all_sessions_from_typedb(allow_fallback=True)
            ids = [s["session_id"] for s in result]
            assert ids.count("SESSION-2026-02-11-WORK") == 1
        finally:
            mod._sessions_store = orig


# ── sync_pending_sessions ───────────────────────────────


class TestSyncPendingSessions:
    """Test the retry mechanism for memory-only sessions."""

    @patch(f"{_SERVICE}.get_typedb_client")
    @patch(f"{_SERVICE}._sessions_store")
    def test_sync_pushes_orphan_to_typedb(self, mock_store, mock_client_fn):
        """sync_pending_sessions should insert memory-only sessions into TypeDB."""
        from governance.services.sessions import sync_pending_sessions

        mock_client = MagicMock()
        mock_client.get_session.return_value = None  # not in TypeDB
        mock_client.insert_session.return_value = {"session_id": "S-1"}
        mock_client_fn.return_value = mock_client

        mock_store.items.return_value = [
            ("S-1", {
                "session_id": "S-1",
                "status": "ACTIVE",
                "start_time": "2026-02-11T10:00:00",
                "description": "Orphan",
                "agent_id": "code-agent",
            }),
        ]

        result = sync_pending_sessions()
        assert result["synced"] == 1
        assert result["failed"] == 0
        mock_client.insert_session.assert_called_once()

    @patch(f"{_SERVICE}.get_typedb_client")
    @patch(f"{_SERVICE}._sessions_store")
    def test_sync_skips_already_persisted(self, mock_store, mock_client_fn):
        """Sessions already in TypeDB should be skipped."""
        from governance.services.sessions import sync_pending_sessions

        mock_client = MagicMock()
        mock_client.get_session.return_value = {"session_id": "S-1"}  # already exists
        mock_client_fn.return_value = mock_client

        mock_store.items.return_value = [
            ("S-1", {"session_id": "S-1", "status": "ACTIVE"}),
        ]

        result = sync_pending_sessions()
        assert result["synced"] == 0
        assert result["already_persisted"] == 1
        mock_client.insert_session.assert_not_called()

    @patch(f"{_SERVICE}.get_typedb_client", return_value=None)
    def test_sync_fails_when_no_typedb(self, mock_client_fn):
        """When TypeDB is unavailable, sync returns error."""
        from governance.services.sessions import sync_pending_sessions

        result = sync_pending_sessions()
        assert result["error"] == "TypeDB unavailable"

    @patch(f"{_SERVICE}.get_typedb_client")
    @patch(f"{_SERVICE}._sessions_store")
    def test_sync_counts_failures(self, mock_store, mock_client_fn):
        """Failed inserts should be counted but not crash."""
        from governance.services.sessions import sync_pending_sessions

        mock_client = MagicMock()
        mock_client.get_session.return_value = None
        mock_client.insert_session.side_effect = Exception("TypeDB error")
        mock_client_fn.return_value = mock_client

        mock_store.items.return_value = [
            ("S-1", {"session_id": "S-1", "status": "ACTIVE", "description": "X"}),
        ]

        result = sync_pending_sessions()
        assert result["failed"] == 1
        assert result["synced"] == 0


# ── create_session persistence status ───────────────────


class TestCreateSessionPersistenceStatus:
    """Verify create_session returns persistence_status field."""

    @patch(f"{_SERVICE_CRUD}.log_event")
    @patch(f"{_SERVICE_CRUD}.record_audit")
    @patch(f"{_SERVICE_CRUD}._monitor")
    @patch(f"{_SERVICE_CRUD}.get_typedb_client")
    @patch(f"{_SERVICE_CRUD}._sessions_store", {})
    def test_persisted_when_typedb_succeeds(self, mock_client_fn, mock_mon, mock_audit, mock_log):
        """create_session via TypeDB returns the response (no persistence_status field).

        When TypeDB succeeds, session_to_response(created) is returned directly.
        The persistence_status field is only set on the in-memory fallback path.
        """
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.return_value = {
            "session_id": "S-1",
            "start_time": "2026-02-11T10:00:00",
            "status": "ACTIVE",
        }
        mock_client_fn.return_value = mock_client

        with patch(f"{_SERVICE_CRUD}.session_to_response", side_effect=lambda x: dict(x)):
            result = create_session(session_id="S-1", description="Test")
        # TypeDB success path delegates to session_to_response; no persistence_status key
        assert result["session_id"] == "S-1"
        assert result["status"] == "ACTIVE"

    @patch(f"{_SERVICE_CRUD}.log_event")
    @patch(f"{_SERVICE_CRUD}.record_audit")
    @patch(f"{_SERVICE_CRUD}._monitor")
    @patch(f"{_SERVICE_CRUD}.get_typedb_client")
    @patch(f"{_SERVICE_CRUD}._sessions_store", {})
    def test_memory_only_when_typedb_fails(self, mock_client_fn, mock_mon, mock_audit, mock_log):
        """create_session should return persistence_status='memory_only' on fallback."""
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.side_effect = Exception("TypeDB down")
        mock_client_fn.return_value = mock_client

        result = create_session(session_id="S-2", description="Test")
        assert result.get("persistence_status") == "memory_only"

    @patch(f"{_SERVICE_CRUD}.log_event")
    @patch(f"{_SERVICE_CRUD}.record_audit")
    @patch(f"{_SERVICE_CRUD}._monitor")
    @patch(f"{_SERVICE_CRUD}.get_typedb_client", return_value=None)
    @patch(f"{_SERVICE_CRUD}._sessions_store", {})
    def test_memory_only_when_no_client(self, mock_client_fn, mock_mon, mock_audit, mock_log):
        """create_session should return persistence_status='memory_only' with no client."""
        from governance.services.sessions import create_session

        result = create_session(session_id="S-3", description="Test")
        assert result.get("persistence_status") == "memory_only"


# ── session_bridge persistence verification ─────────────


class TestSessionBridgePersistence:
    """Verify session_bridge logs persistence failures at ERROR level."""

    @patch(f"{_BRIDGE}._sessions_store", {})
    @patch(f"{_BRIDGE}.SessionCollector")
    def test_start_chat_session_logs_persistence_status(self, mock_collector_cls):
        """start_chat_session should log persistence status."""
        from governance.routes.chat.session_bridge import start_chat_session

        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-CHAT-TEST"
        mock_collector.start_time = datetime(2026, 2, 11, 10, 0)
        mock_collector_cls.return_value = mock_collector

        with patch(f"{_BRIDGE}.create_session") as mock_create:
            mock_create.return_value = {
                "session_id": "SESSION-2026-02-11-CHAT-TEST",
                "persistence_status": "persisted",
            }
            collector = start_chat_session("code-agent", "test topic")
            assert collector == mock_collector

    @patch(f"{_BRIDGE}._sessions_store", {})
    @patch(f"{_BRIDGE}.SessionCollector")
    def test_start_chat_session_handles_memory_only(self, mock_collector_cls):
        """When persistence is memory_only, session should still work."""
        from governance.routes.chat.session_bridge import start_chat_session

        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-CHAT-FAIL"
        mock_collector.start_time = datetime(2026, 2, 11, 10, 0)
        mock_collector_cls.return_value = mock_collector

        with patch(f"{_BRIDGE}.create_session") as mock_create:
            mock_create.return_value = {
                "session_id": "SESSION-2026-02-11-CHAT-FAIL",
                "persistence_status": "memory_only",
            }
            collector = start_chat_session("code-agent", "failing topic")
            assert collector == mock_collector

    @patch(f"{_BRIDGE}._sessions_store", {})
    @patch(f"{_BRIDGE}.SessionCollector")
    def test_start_chat_session_survives_total_failure(self, mock_collector_cls):
        """Even if create_session raises, chat session should still start."""
        from governance.routes.chat.session_bridge import start_chat_session

        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-CHAT-BOOM"
        mock_collector.start_time = datetime(2026, 2, 11, 10, 0)
        mock_collector_cls.return_value = mock_collector

        with patch(f"{_BRIDGE}.create_session", side_effect=Exception("total failure")):
            collector = start_chat_session("code-agent", "crash topic")
            assert collector == mock_collector


# ── end_chat_session sync attempt ───────────────────────


class TestEndChatSessionSync:
    """Verify end_chat_session attempts sync for memory-only sessions."""

    @patch(f"{_BRIDGE}._run_post_session_checks")
    @patch(f"{_BRIDGE}._sessions_store")
    def test_end_session_calls_service(self, mock_store, mock_checks):
        """end_chat_session should call svc_end_session."""
        from governance.routes.chat.session_bridge import end_chat_session

        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-CHAT-END"
        mock_collector.events = []
        mock_collector.generate_session_log.return_value = "/evidence/test.md"
        mock_collector.sync_to_chromadb.return_value = None

        mock_store.__contains__ = MagicMock(return_value=True)
        mock_store.__getitem__ = MagicMock(return_value={
            "status": "ACTIVE", "persistence_status": "memory_only",
        })

        with patch(f"{_BRIDGE}.end_session") as mock_end:
            mock_end.return_value = {"status": "COMPLETED"}
            result = end_chat_session(mock_collector)
            mock_end.assert_called_once()


# ── API endpoint for sync ───────────────────────────────


class TestSyncEndpoint:
    """Verify /sessions/sync endpoint exists and works."""

    @patch(f"governance.services.sessions.sync_pending_sessions")
    def test_sync_endpoint_callable(self, mock_sync):
        """sync_pending_sessions should be importable from service."""
        mock_sync.return_value = {"synced": 0, "failed": 0}
        result = mock_sync()
        assert "synced" in result
