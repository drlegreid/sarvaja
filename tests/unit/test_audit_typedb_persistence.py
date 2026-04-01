"""Unit tests for Audit TypeDB Persistence — SRVJ-FEAT-AUDIT-TRAIL-01 P5.

TDD: Tests written FIRST — implementation follows.

DSE coverage:
- _persist_audit_to_typedb(): writes entity with correct attributes
- _persist_audit_to_typedb(): TypeDB down → silent failure (JSON still works)
- _persist_audit_to_typedb(): duplicate audit_id → idempotent (no crash)
- _persist_audit_to_typedb(): creates task-audit relation when task exists
- _persist_audit_to_typedb(): skips relation when task NOT in TypeDB
- _persist_audit_to_typedb(): creates session-audit relation when session context
- record_audit(): dual-write — JSON + TypeDB
- record_audit(): JSON write succeeds even when TypeDB fails
- record_audit(): TypeDB write is AFTER JSON write (ordering)
- query_audit_trail(): TypeDB-first with JSON fallback
- query_audit_trail(): deduplicates by audit_id when merging
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, call, PropertyMock


# ── Sample data ──────────────────────────────────────────────────────

SAMPLE_ENTRY_DICT = {
    "audit_id": "AUDIT-DEADBEEF",
    "correlation_id": "CORR-20260329-120000-ABC123",
    "timestamp": "2026-03-29T12:00:00",
    "actor_id": "code-agent",
    "action_type": "UPDATE",
    "entity_type": "task",
    "entity_id": "TASK-001",
    "old_value": "OPEN",
    "new_value": "IN_PROGRESS",
    "applied_rules": ["TEST-GUARD-01"],
    "metadata": {
        "source": "mcp",
        "session_id": "SESSION-2026-03-29-P5",
        "field_changes": {"status": {"from": "OPEN", "to": "IN_PROGRESS"}},
    },
}


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_typedb_client():
    """TypeDB client mock that succeeds on all operations."""
    client = MagicMock()
    client._connected = True
    client.is_connected.return_value = True
    client._driver = MagicMock()
    client.database = "sim-ai-governance"
    return client


@pytest.fixture
def mock_disconnected_client():
    """TypeDB client mock that is not connected (simulates TypeDB down)."""
    client = MagicMock()
    client._connected = False
    client.is_connected.return_value = False
    client.connect.return_value = False
    return client


# ── _persist_audit_to_typedb: Happy path ─────────────────────────────

class TestPersistAuditToTypeDB:
    """Unit tests for the TypeDB audit write function."""

    @patch("governance.stores.audit.get_typedb_client")
    def test_writes_entity_with_correct_attributes(self, mock_get_client, mock_typedb_client):
        """Audit entry is inserted as audit-entry entity in TypeDB with all attributes."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        # Check-before-insert returns empty (no existing entry)
        tx_mock.query.return_value.resolve.return_value = iter([])

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        # Verify transaction was opened for WRITE
        assert mock_typedb_client._driver.transaction.called
        # Verify at least one query was executed (the insert)
        assert tx_mock.query.called
        # Verify commit was called
        assert tx_mock.commit.called

    @patch("governance.stores.audit.get_typedb_client")
    def test_insert_query_contains_all_required_attributes(self, mock_get_client, mock_typedb_client):
        """The TypeQL insert contains audit-entry-id, audit-action-type, etc."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        tx_mock.query.return_value.resolve.return_value = iter([])

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        # Collect all query strings
        queries = [str(c[0][0]) for c in tx_mock.query.call_args_list]
        all_queries = " ".join(queries)

        # Must contain key attribute references
        assert "audit-entry-id" in all_queries
        assert "AUDIT-DEADBEEF" in all_queries
        assert "audit-action-type" in all_queries
        assert "audit-entity-id" in all_queries
        assert "audit-actor-id" in all_queries

    @patch("governance.stores.audit.get_typedb_client")
    def test_creates_task_audit_relation_when_task_exists(self, mock_get_client, mock_typedb_client):
        """When entity_type=task and task exists in TypeDB, task-audit relation is created."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        # First call: check audit exists → empty
        # Second call: check task exists → found
        resolve_mock = MagicMock()
        resolve_mock.resolve.side_effect = [
            iter([]),       # audit check → not exists
            None,           # insert entity
            iter(["found"]),  # task exists check
            None,           # insert relation
        ]
        tx_mock.query.return_value = resolve_mock

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        queries = [str(c[0][0]) for c in tx_mock.query.call_args_list]
        all_queries = " ".join(queries)
        assert "task-audit" in all_queries or "audited-task" in all_queries

    @patch("governance.stores.audit.get_typedb_client")
    def test_skips_relation_when_task_not_in_typedb(self, mock_get_client, mock_typedb_client):
        """When entity_type=task but task NOT in TypeDB, relation is skipped (no crash)."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        # Audit check → not exists, task check → not found
        resolve_mock = MagicMock()
        resolve_mock.resolve.side_effect = [
            iter([]),   # audit check → not exists
            None,       # insert entity
            iter([]),   # task exists check → NOT found
        ]
        tx_mock.query.return_value = resolve_mock

        from governance.stores.audit import _persist_audit_to_typedb
        # Should NOT raise
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        # Commit should still be called (entity was inserted even without relation)
        assert tx_mock.commit.called

    @patch("governance.stores.audit.get_typedb_client")
    def test_creates_session_audit_relation_when_session_context(self, mock_get_client, mock_typedb_client):
        """When metadata.session_id present and session exists, session-audit relation created."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        resolve_mock = MagicMock()
        resolve_mock.resolve.side_effect = [
            iter([]),       # audit check → not exists
            None,           # insert entity
            iter(["found"]),  # task exists
            None,           # insert task-audit relation
            iter(["found"]),  # session exists
            None,           # insert session-audit relation
        ]
        tx_mock.query.return_value = resolve_mock

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        queries = [str(c[0][0]) for c in tx_mock.query.call_args_list]
        all_queries = " ".join(queries)
        assert "session-audit" in all_queries or "audit-session" in all_queries


# ── _persist_audit_to_typedb: Failure modes ──────────────────────────

class TestPersistAuditFailureModes:
    """TypeDB failures must be silent — never crash the audit store."""

    @patch("governance.stores.audit.get_typedb_client")
    def test_typedb_down_silent_failure(self, mock_get_client, mock_disconnected_client):
        """TypeDB not connected → silent return, no exception."""
        mock_get_client.return_value = mock_disconnected_client

        from governance.stores.audit import _persist_audit_to_typedb
        # Must NOT raise
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

    @patch("governance.stores.audit.get_typedb_client")
    def test_typedb_no_client_silent_failure(self, mock_get_client):
        """get_typedb_client returns None → silent return."""
        mock_get_client.return_value = None

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

    @patch("governance.stores.audit.get_typedb_client")
    def test_typedb_write_exception_silent(self, mock_get_client, mock_typedb_client):
        """TypeDB write throws exception → caught, logged, no propagation."""
        mock_get_client.return_value = mock_typedb_client
        mock_typedb_client._driver.transaction.side_effect = RuntimeError("connection lost")

        from governance.stores.audit import _persist_audit_to_typedb
        # Must NOT raise
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

    @patch("governance.stores.audit.get_typedb_client")
    def test_duplicate_audit_id_idempotent(self, mock_get_client, mock_typedb_client):
        """Duplicate audit_id insert → idempotent skip (no crash)."""
        mock_get_client.return_value = mock_typedb_client
        tx_mock = MagicMock()
        mock_typedb_client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx_mock)
        mock_typedb_client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        # Check returns existing entry
        tx_mock.query.return_value.resolve.return_value = iter(["already_exists"])

        from governance.stores.audit import _persist_audit_to_typedb
        _persist_audit_to_typedb(SAMPLE_ENTRY_DICT)

        # Should have checked, found existing, and NOT inserted
        # Commit may or may not be called (early return is fine)


# ── record_audit(): Dual-write integration ───────────────────────────

class TestRecordAuditDualWrite:
    """record_audit must write JSON first, then attempt TypeDB."""

    @patch("governance.stores.audit._persist_audit_to_typedb")
    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_dual_write_calls_both(self, _retention, _save, mock_typedb):
        """record_audit calls both JSON save AND TypeDB persist."""
        from governance.stores.audit import record_audit
        entry = record_audit(
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-DW-001",
            actor_id="code-agent",
        )
        _save.assert_called_once()
        mock_typedb.assert_called_once()

    @patch("governance.stores.audit._persist_audit_to_typedb")
    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_json_write_before_typedb(self, _retention, mock_save, mock_typedb):
        """JSON write (step 2) happens BEFORE TypeDB write (step 3)."""
        call_order = []
        mock_save.side_effect = lambda: call_order.append("json")
        mock_typedb.side_effect = lambda entry: call_order.append("typedb")

        from governance.stores.audit import record_audit
        record_audit(
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-ORDER-001",
        )
        assert call_order == ["json", "typedb"]

    @patch("governance.stores.audit._persist_audit_to_typedb")
    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_json_succeeds_when_typedb_fails(self, _retention, mock_save, mock_typedb):
        """TypeDB write failure does NOT prevent JSON write."""
        mock_typedb.side_effect = RuntimeError("TypeDB exploded")

        from governance.stores.audit import record_audit
        entry = record_audit(
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-SAFE-001",
        )
        # JSON save was called (before TypeDB)
        mock_save.assert_called_once()
        # Entry was returned despite TypeDB failure
        assert entry.audit_id.startswith("AUDIT-")

    @patch("governance.stores.audit._persist_audit_to_typedb")
    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_entry_dict_passed_to_typedb(self, _retention, _save, mock_typedb):
        """The dict passed to _persist_audit_to_typedb matches the entry."""
        from governance.stores.audit import record_audit
        entry = record_audit(
            action_type="LINK",
            entity_type="task",
            entity_id="TASK-DICT-001",
            actor_id="code-agent",
            metadata={"linked_entity": {"type": "rule", "id": "R-1"}},
        )
        mock_typedb.assert_called_once()
        passed_dict = mock_typedb.call_args[0][0]
        assert passed_dict["audit_id"] == entry.audit_id
        assert passed_dict["action_type"] == "LINK"
        assert passed_dict["entity_id"] == "TASK-DICT-001"
        assert passed_dict["metadata"]["linked_entity"]["type"] == "rule"


# ── query_audit_trail(): TypeDB-first with fallback ──────────────────

class TestQueryAuditTrailTypeDBFirst:
    """query_audit_trail should try TypeDB first, fall back to JSON."""

    @patch("governance.stores.audit._query_audit_from_typedb")
    def test_typedb_first_when_available(self, mock_typedb_query):
        """When TypeDB returns results, JSON is not consulted."""
        mock_typedb_query.return_value = [
            {"audit_id": "AUDIT-TB-001", "action_type": "CREATE",
             "entity_type": "task", "entity_id": "TASK-001",
             "timestamp": "2026-03-29T12:00:00", "actor_id": "system"},
        ]

        from governance.stores.audit import query_audit_trail
        results = query_audit_trail(entity_id="TASK-001")
        assert len(results) >= 1
        assert results[0]["audit_id"] == "AUDIT-TB-001"

    @patch("governance.stores.audit._query_audit_from_typedb")
    def test_json_fallback_when_typedb_fails(self, mock_typedb_query):
        """When TypeDB query fails, falls back to JSON in-memory store."""
        mock_typedb_query.side_effect = RuntimeError("TypeDB unavailable")

        from governance.stores.audit import query_audit_trail, _audit_store
        # Seed JSON store
        _audit_store.append({
            "audit_id": "AUDIT-JSON-001",
            "action_type": "CREATE",
            "entity_type": "task",
            "entity_id": "TASK-FB-001",
            "timestamp": "2026-03-29T12:00:00",
            "actor_id": "system",
            "correlation_id": "CORR-001",
            "old_value": None,
            "new_value": None,
            "applied_rules": [],
            "metadata": {},
        })
        try:
            results = query_audit_trail(entity_id="TASK-FB-001")
            assert len(results) >= 1
            assert results[0]["audit_id"] == "AUDIT-JSON-001"
        finally:
            # Cleanup
            _audit_store[:] = [e for e in _audit_store if e.get("audit_id") != "AUDIT-JSON-001"]

    @patch("governance.stores.audit._query_audit_from_typedb")
    def test_deduplicates_by_audit_id(self, mock_typedb_query):
        """When both sources return same audit_id, result is deduplicated."""
        mock_typedb_query.return_value = [
            {"audit_id": "AUDIT-DUP-001", "action_type": "CREATE",
             "entity_type": "task", "entity_id": "TASK-DUP",
             "timestamp": "2026-03-29T12:00:00", "actor_id": "system"},
        ]

        from governance.stores.audit import query_audit_trail, _audit_store
        _audit_store.append({
            "audit_id": "AUDIT-DUP-001",
            "action_type": "CREATE",
            "entity_type": "task",
            "entity_id": "TASK-DUP",
            "timestamp": "2026-03-29T12:00:00",
            "actor_id": "system",
            "correlation_id": "CORR-001",
            "old_value": None,
            "new_value": None,
            "applied_rules": [],
            "metadata": {},
        })
        try:
            results = query_audit_trail(entity_id="TASK-DUP")
            ids = [r["audit_id"] for r in results]
            # Should not have duplicates
            assert ids.count("AUDIT-DUP-001") == 1
        finally:
            _audit_store[:] = [e for e in _audit_store if e.get("audit_id") != "AUDIT-DUP-001"]

    @patch("governance.stores.audit._query_audit_from_typedb")
    def test_typedb_none_falls_back(self, mock_typedb_query):
        """When TypeDB query returns None (not configured), uses JSON."""
        mock_typedb_query.return_value = None

        from governance.stores.audit import query_audit_trail
        # Should not crash — just returns JSON results
        results = query_audit_trail(entity_id="NONEXISTENT")
        assert isinstance(results, list)


# ── _query_audit_from_typedb: Query construction ─────────────────────

class TestQueryAuditFromTypeDB:
    """Tests for the TypeDB audit query function."""

    @patch("governance.stores.audit.get_typedb_client")
    def test_returns_none_when_no_client(self, mock_get_client):
        """No TypeDB client → returns None (signals fallback)."""
        mock_get_client.return_value = None

        from governance.stores.audit import _query_audit_from_typedb
        result = _query_audit_from_typedb(entity_id="TASK-001")
        assert result is None

    @patch("governance.stores.audit.get_typedb_client")
    def test_returns_none_when_disconnected(self, mock_get_client, mock_disconnected_client):
        """Disconnected client → returns None."""
        mock_get_client.return_value = mock_disconnected_client

        from governance.stores.audit import _query_audit_from_typedb
        result = _query_audit_from_typedb(entity_id="TASK-001")
        assert result is None

    @patch("governance.stores.audit.get_typedb_client")
    def test_filters_by_entity_id(self, mock_get_client, mock_typedb_client):
        """Query includes entity_id filter in TypeQL match clause."""
        mock_get_client.return_value = mock_typedb_client
        mock_typedb_client.execute_query.return_value = []

        from governance.stores.audit import _query_audit_from_typedb
        _query_audit_from_typedb(entity_id="TASK-FILTER-001")

        query = mock_typedb_client.execute_query.call_args[0][0]
        assert 'audit-entity-id "TASK-FILTER-001"' in query

    @patch("governance.stores.audit.get_typedb_client")
    def test_filters_by_actor_id(self, mock_get_client, mock_typedb_client):
        """Query includes actor_id filter."""
        mock_get_client.return_value = mock_typedb_client
        mock_typedb_client.execute_query.return_value = []

        from governance.stores.audit import _query_audit_from_typedb
        _query_audit_from_typedb(actor_id="code-agent")

        query = mock_typedb_client.execute_query.call_args[0][0]
        assert 'audit-actor-id "code-agent"' in query

    @patch("governance.stores.audit.get_typedb_client")
    def test_filters_by_action_type(self, mock_get_client, mock_typedb_client):
        """Query includes action_type filter."""
        mock_get_client.return_value = mock_typedb_client
        mock_typedb_client.execute_query.return_value = []

        from governance.stores.audit import _query_audit_from_typedb
        _query_audit_from_typedb(action_type="LINK")

        query = mock_typedb_client.execute_query.call_args[0][0]
        assert 'audit-action-type "LINK"' in query
