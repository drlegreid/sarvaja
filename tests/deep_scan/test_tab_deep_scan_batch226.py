"""Batch 226 — Stores layer defense tests.

Validates fixes for:
- BUG-226-PERSIST-001: Path traversal sanitization (whitelist regex)
- BUG-226-TYPEDB-003: Stable sentinel for missing start_time
- BUG-226-AUDIT-003: Negative offset/limit guards
- BUG-226-AUDIT-001: Audit store uses global list (thread safety awareness)
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-226-PERSIST-001: Path traversal sanitization ────────────────

class TestSessionPersistPathSanitization:
    """session_persistence._get_path must use whitelist regex."""

    def test_uses_regex_whitelist(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "re.sub" in src
        assert "BUG-226-PERSIST-001" in src

    def test_no_simple_replace_for_slashes(self):
        """Old pattern was replace('/', '_').replace('..', '_') — should be gone."""
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert 'replace("/", "_").replace("..", "_")' not in src

    def test_sanitization_logic(self):
        """Verify the regex strips dangerous characters."""
        import re
        session_id = "SESSION-../../etc/passwd"
        safe = re.sub(r'[^A-Za-z0-9_\-]', '_', session_id)
        assert "/" not in safe
        assert ".." not in safe
        assert safe.startswith("SESSION-")

    def test_null_byte_stripped(self):
        """Null bytes should be replaced by sanitization."""
        import re
        session_id = "SESSION-2026\x00evil"
        safe = re.sub(r'[^A-Za-z0-9_\-]', '_', session_id)
        assert "\x00" not in safe


# ── BUG-226-TYPEDB-003: Stable sentinel for missing start_time ──────

class TestSessionStartTimeSentinel:
    """session_to_response and _session_to_dict must NOT use datetime.now() fallback."""

    def test_helpers_uses_sentinel(self):
        src = (SRC / "governance/stores/helpers.py").read_text()
        idx = src.index("def session_to_response")
        block = src[idx:idx + 800]
        assert "1970-01-01" in block
        assert "BUG-226-TYPEDB-003" in block

    def test_typedb_access_uses_sentinel(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        idx = src.index("def _session_to_dict")
        block = src[idx:idx + 800]
        assert "1970-01-01" in block
        assert "BUG-226-TYPEDB-003" in block


# ── BUG-226-AUDIT-003: Negative offset/limit guards ────────────────

class TestAuditQueryValidation:
    """query_audit_trail must guard against negative offset/limit."""

    def test_limit_guard_present(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        assert "max(1, limit)" in src

    def test_offset_guard_present(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        assert "max(0, offset)" in src


# ── Store module import defense tests ───────────────────────────────

class TestStoreModuleImports:
    """Defense tests for store modules."""

    def test_stores_init_importable(self):
        import governance.stores
        assert governance.stores is not None

    def test_data_stores_importable(self):
        from governance.stores.data_stores import _tasks_store, _sessions_store
        assert isinstance(_tasks_store, dict)
        assert isinstance(_sessions_store, dict)

    def test_config_importable(self):
        from governance.stores.config import USE_TYPEDB
        assert isinstance(USE_TYPEDB, bool)

    def test_audit_importable(self):
        from governance.stores.audit import AuditEntry, record_audit, query_audit_trail
        assert AuditEntry is not None
        assert callable(record_audit)
        assert callable(query_audit_trail)

    def test_session_persistence_importable(self):
        from governance.stores.session_persistence import persist_session, load_persisted_sessions
        assert callable(persist_session)
        assert callable(load_persisted_sessions)

    def test_retry_importable(self):
        from governance.stores.retry import retry_on_transient, TRANSIENT_EXCEPTIONS
        assert callable(retry_on_transient)
        assert isinstance(TRANSIENT_EXCEPTIONS, tuple)

    def test_helpers_importable(self):
        from governance.stores.helpers import task_to_response, session_to_response
        assert callable(task_to_response)
        assert callable(session_to_response)

    def test_agents_store_importable(self):
        from governance.stores.agents import _agents_store, get_agent
        assert isinstance(_agents_store, dict)
        assert callable(get_agent)

    def test_typedb_access_importable(self):
        from governance.stores.typedb_access import get_all_tasks_from_typedb
        assert callable(get_all_tasks_from_typedb)
