"""Batch 241 — Stores layer defense tests.

Validates fixes for:
- BUG-241-RET-001: RuntimeError filter in retry decorator
- BUG-241-PER-003: Falsy-check fix in session_persistence merge
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-241-RET-001: RuntimeError filter in retry ───────────────────

class TestRetryRuntimeErrorFilter:
    """retry_on_transient must filter RuntimeError by message content."""

    def test_is_transient_function_exists(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        assert "def _is_transient(" in src

    def test_is_transient_checks_disconnect(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        idx = src.index("def _is_transient(")
        block = src[idx:idx + 500]
        assert "disconnect" in block

    def test_is_transient_checks_connection(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        idx = src.index("def _is_transient(")
        block = src[idx:idx + 500]
        assert '"connection"' in block

    def test_decorator_uses_is_transient(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        idx = src.index("def wrapper(")
        block = src[idx:idx + 500]
        assert "_is_transient(e)" in block

    def test_non_transient_runtime_raises(self):
        """Non-transient RuntimeError must re-raise, not retry."""
        src = (SRC / "governance/stores/retry.py").read_text()
        idx = src.index("_is_transient(e)")
        block = src[idx:idx + 100]
        assert "raise" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        assert "BUG-241-RET-001" in src

    def test_is_transient_runtime_positive(self):
        """Connection-related RuntimeError should be detected as transient."""
        from governance.stores.retry import _is_transient
        assert _is_transient(RuntimeError("TypeDB connection closed"))
        assert _is_transient(RuntimeError("server unavailable"))
        assert _is_transient(RuntimeError("disconnect detected"))

    def test_is_transient_runtime_negative(self):
        """Schema/logic RuntimeErrors must NOT be transient."""
        from governance.stores.retry import _is_transient
        assert not _is_transient(RuntimeError("invalid schema"))
        assert not _is_transient(RuntimeError("attribute not found"))
        assert not _is_transient(ValueError("something"))


# ── BUG-241-PER-003: Falsy-check fix in merge ───────────────────────

class TestSessionPersistenceMerge:
    """Merge must use 'key not in entry', not 'not entry.get(key)'."""

    def test_uses_key_not_in_entry(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "key not in entry" in src

    def test_no_not_entry_get_pattern(self):
        """Must not use falsy 'not entry.get(key)' for array merge."""
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        # Find the merge section
        idx = src.index("tool_calls")
        block = src[idx:idx + 200]
        assert "not entry.get(key)" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "BUG-241-PER-003" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch241Imports:
    def test_retry_importable(self):
        import governance.stores.retry
        assert governance.stores.retry is not None

    def test_session_persistence_importable(self):
        import governance.stores.session_persistence
        assert governance.stores.session_persistence is not None

    def test_typedb_access_importable(self):
        import governance.stores.typedb_access
        assert governance.stores.typedb_access is not None

    def test_audit_importable(self):
        import governance.stores.audit
        assert governance.stores.audit is not None

    def test_helpers_importable(self):
        import governance.stores.helpers
        assert governance.stores.helpers is not None

    def test_agents_store_importable(self):
        import governance.stores.agents
        assert governance.stores.agents is not None
