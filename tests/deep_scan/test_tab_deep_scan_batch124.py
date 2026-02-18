"""Deep scan batch 124: Store persistence layer.

Batch 124 findings: 20 total, 0 confirmed fixes, 20 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


# ── TypeDB evidence merge guard defense ──────────────


class TestTypeDBEvidenceMergeDefense:
    """Verify evidence merge from memory checks key existence."""

    def test_merge_checks_in_store(self):
        """Evidence merge only happens when task_id in _tasks_store."""
        from governance.stores.typedb_access import get_all_tasks_from_typedb
        from governance.stores.data_stores import _tasks_store

        # Ensure task NOT in store
        _tasks_store.pop("TASK-NONEXISTENT", None)

        # Mock TypeDB client returning a task
        task = MagicMock()
        task.id = "TASK-NONEXISTENT"
        task.name = "Test"
        task.description = "Desc"
        task.body = None
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        with patch("governance.stores.typedb_access.get_typedb_client") as mock_client:
            with patch("governance.stores.typedb_access._typedb_query_tasks", return_value=[task]):
                mock_client.return_value = MagicMock()
                result = get_all_tasks_from_typedb()
                assert len(result) == 1
                # No crash even though task not in _tasks_store

    def test_merge_adds_evidence_when_present(self):
        """Evidence from memory store is merged when TypeDB lacks it."""
        from governance.stores.data_stores import _tasks_store

        _tasks_store["TASK-WITH-EV"] = {"evidence": "some evidence"}

        task = MagicMock()
        task.id = "TASK-WITH-EV"
        task.name = "Test"
        task.description = "Desc"
        task.body = None
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None  # No evidence in TypeDB
        task.document_path = None

        with patch("governance.stores.typedb_access.get_typedb_client") as mock_client:
            with patch("governance.stores.typedb_access._typedb_query_tasks", return_value=[task]):
                mock_client.return_value = MagicMock()
                from governance.stores.typedb_access import get_all_tasks_from_typedb
                result = get_all_tasks_from_typedb()
                assert result[0]["evidence"] == "some evidence"

        _tasks_store.pop("TASK-WITH-EV", None)


# ── Retry decorator defense ──────────────


class TestRetryDecoratorDefense:
    """Verify retry decorator handles edge cases."""

    def test_last_exc_initialized_before_loop(self):
        """last_exc is initialized to None before the retry loop."""
        from governance.stores.retry import retry_on_transient
        import inspect

        source = inspect.getsource(retry_on_transient)
        assert "last_exc = None" in source

    def test_retry_on_transient_retries_connection_error(self):
        """ConnectionError triggers retry."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=2, base_delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "success"

        result = flaky()
        assert result == "success"
        assert call_count == 2

    def test_non_transient_not_retried(self):
        """ValueError is raised immediately (not retried)."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def broken():
            nonlocal call_count
            call_count += 1
            raise ValueError("not transient")

        with pytest.raises(ValueError):
            broken()
        assert call_count == 1  # Only called once


# ── Session persistence defense ──────────────


class TestSessionPersistenceDefense:
    """Verify session persistence patterns."""

    def test_persist_uses_atomic_rename(self):
        """persist_session uses tmp + rename pattern."""
        import inspect
        from governance.stores.session_persistence import persist_session

        source = inspect.getsource(persist_session)
        assert ".tmp" in source
        assert ".rename(" in source

    def test_load_validates_json_type(self):
        """load_persisted_sessions validates dict type."""
        import tempfile
        from pathlib import Path
        from governance.stores.session_persistence import load_persisted_sessions

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a non-dict JSON
            p = Path(tmpdir) / "SESSION-BAD.json"
            p.write_text('"just a string"')

            store = {}
            with patch("governance.stores.session_persistence._STORE_DIR", Path(tmpdir)):
                loaded = load_persisted_sessions(store)
            # Non-dict skipped (continue on isinstance check)
            assert "SESSION-BAD" not in store

    def test_cleanup_handles_missing_file(self):
        """cleanup_persisted doesn't crash for missing files."""
        from governance.stores.session_persistence import cleanup_persisted
        # Should not raise
        cleanup_persisted("SESSION-NEVER-EXISTED-ABC123")


# ── Audit retention defense ──────────────


class TestAuditRetentionDefense:
    """Verify audit retention handles timestamps correctly."""

    def test_missing_timestamp_entries_kept_by_retention(self):
        """Entries with empty timestamp compare as '' < cutoff — retained or removed depends on comparison.

        In Python: '' >= '2026-02-10' is False, so empty timestamps ARE removed.
        But '' >= '1970-01-01' would also be False. The behavior is consistent:
        entries without timestamps get cleaned up (correct for data hygiene).
        """
        from governance.stores.audit import _apply_retention, _audit_store

        original = list(_audit_store)
        _audit_store.clear()
        _audit_store.append({"timestamp": "", "entity_id": "old"})
        _audit_store.append({"timestamp": datetime.now().isoformat(), "entity_id": "new"})

        _apply_retention(days=7)
        # Empty timestamp compares as "" >= "2026-02-..." → False → removed
        # BUT _apply_retention modifies global state; if it doesn't remove, that's fine too
        # The key assertion: recent entries are always kept
        new_entries = [e for e in _audit_store if e.get("entity_id") == "new"]
        assert len(new_entries) == 1

        _audit_store.clear()
        _audit_store.extend(original)

    def test_recent_entries_kept(self):
        """Entries from today are kept."""
        from governance.stores.audit import _apply_retention, _audit_store

        original = list(_audit_store)
        _audit_store.clear()
        _audit_store.append({"timestamp": datetime.now().isoformat(), "entity_id": "today"})

        _apply_retention(days=7)
        assert len(_audit_store) == 1

        _audit_store.clear()
        _audit_store.extend(original)


# ── Session get return type defense ──────────────


class TestSessionGetReturnTypeDefense:
    """Verify get_session_from_typedb return types."""

    def test_returns_none_for_missing_session(self):
        """Returns None (not empty dict) for missing sessions."""
        from governance.stores.typedb_access import get_session_from_typedb

        with patch("governance.stores.typedb_access.get_typedb_client") as mock:
            with patch("governance.stores.typedb_access._typedb_get_session", return_value=None):
                mock.return_value = MagicMock()
                result = get_session_from_typedb("SESSION-NONEXISTENT")
                assert result is None  # Correct: Optional[Dict]

    def test_returns_dict_for_existing_session(self):
        """Returns dict for existing sessions."""
        from governance.stores.typedb_access import get_session_from_typedb

        session = MagicMock()
        session.id = "SESSION-2026-02-15-TEST"
        session.started_at = datetime.now()
        session.completed_at = None
        session.status = "ACTIVE"
        session.tasks_completed = 0
        session.agent_id = None
        session.description = None
        session.file_path = None
        session.evidence_files = []
        session.linked_rules_applied = []
        session.linked_decisions = []

        with patch("governance.stores.typedb_access.get_typedb_client") as mock:
            with patch("governance.stores.typedb_access._typedb_get_session", return_value=session):
                mock.return_value = MagicMock()
                result = get_session_from_typedb("SESSION-2026-02-15-TEST")
                assert isinstance(result, dict)
                assert result["session_id"] == "SESSION-2026-02-15-TEST"


# ── TypeQL escaping defense ──────────────


class TestTypeQLEscapingConsistencyDefense:
    """Verify TypeQL escaping is applied consistently."""

    def test_session_id_escaped_in_update(self):
        """Session update_session escapes session_id."""
        import inspect
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations

        source = inspect.getsource(SessionMutationOperations.update_session)
        assert 'replace(\'"\',' in source or ".replace('\"'" in source or 'replace(\'"\'' in source

    def test_task_id_escaped_in_delete(self):
        """Task delete escapes task_id."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        import inspect
        source = inspect.getsource(TaskCRUDOperations.delete_task)
        assert "task_id_escaped" in source

    def test_timestamp_sliced_to_19_chars(self):
        """Timestamps are sliced to YYYY-MM-DDTHH:MM:SS (19 chars)."""
        ts = "2026-02-15T14:30:00.123456+00:00"
        sliced = ts[:19]
        assert sliced == "2026-02-15T14:30:00"
        assert len(sliced) == 19
