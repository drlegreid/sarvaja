"""Batch 205 — Session persistence + stores defense tests.

Validates fixes for:
- BUG-205-ITER-001: _sessions_store iteration snapshot
- BUG-205-SYNC-001: sync_pending_sessions marks as persisted
"""
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-205-ITER-001: _sessions_store iteration snapshot ─────────────

class TestSessionStoreIterationSnapshot:
    """_sessions_store iteration must use list() snapshot."""

    def test_typedb_access_uses_snapshot_for_orphan_merge(self):
        """get_all_sessions_from_typedb must snapshot _sessions_store.values()."""
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        in_func = False
        found_snapshot = False
        found_bare = False
        for line in src.splitlines():
            if "def get_all_sessions_from_typedb" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func:
                if "list(_sessions_store.values())" in line:
                    found_snapshot = True
                if "for" in line and "_sessions_store.values()" in line and "list(" not in line:
                    found_bare = True
        assert found_snapshot, "Must use list(_sessions_store.values()) for snapshot"
        assert not found_bare, "Found bare _sessions_store.values() iteration without snapshot"


# ── BUG-205-SYNC-001: sync_pending marks as persisted ────────────────

class TestSyncPendingMarksAsPersisted:
    """sync_pending_sessions must update persistence_status after sync."""

    def test_sync_marks_persistence_status(self):
        """After successful sync, persistence_status must be set to 'persisted'."""
        src = (SRC / "governance/services/sessions.py").read_text()
        in_func = False
        found_mark = False
        for line in src.splitlines():
            if "def sync_pending_sessions" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and '"persisted"' in line and "persistence_status" in line:
                found_mark = True
        assert found_mark, "sync_pending_sessions must mark synced sessions as 'persisted'"


# ── Session persistence defense ──────────────────────────────────────

class TestSessionPersistenceDefense:
    """Defense tests for session persistence module."""

    def test_persist_session_importable(self):
        from governance.stores.session_persistence import persist_session
        assert callable(persist_session)

    def test_load_persisted_sessions_importable(self):
        from governance.stores.session_persistence import load_persisted_sessions
        assert callable(load_persisted_sessions)

    def test_sessions_store_is_dict(self):
        from governance.stores import _sessions_store
        assert isinstance(_sessions_store, dict)


# ── TypeDB access defense ────────────────────────────────────────────

class TestTypeDBAccessDefense:
    """Defense tests for TypeDB access layer."""

    def test_get_all_sessions_function_exists(self):
        from governance.stores.typedb_access import get_all_sessions_from_typedb
        assert callable(get_all_sessions_from_typedb)

    def test_session_to_dict_function_exists(self):
        from governance.stores.typedb_access import _session_to_dict
        assert callable(_session_to_dict)

    def test_get_session_from_typedb_function_exists(self):
        from governance.stores.typedb_access import get_session_from_typedb
        assert callable(get_session_from_typedb)
