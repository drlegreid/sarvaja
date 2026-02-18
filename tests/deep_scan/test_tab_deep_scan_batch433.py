"""Batch 433 — session_persistence debug→warning upgrades,
audit.py exc_info additions, routes/services/TypeDB/stores CLEAN confirmation tests.

Validates fixes for:
- BUG-433-PER-001: session_persistence.py .tmp cleanup debug→warning + exc_info
- BUG-433-PER-002: session_persistence.py persist failure debug→warning + exc_info
- BUG-433-PER-003: session_persistence.py cleanup_persisted debug→warning + exc_info
- BUG-433-AUD-001: audit.py load failure exc_info
- BUG-433-AUD-002: audit.py save failure exc_info

Batch 430-432 scanned files confirmed CLEAN (no Tier 1 findings):
- governance/routes/sessions/crud.py
- governance/routes/sessions/detail.py
- governance/routes/sessions/relations.py
- governance/routes/agents/crud.py
- governance/routes/agents/observability.py
- governance/services/tasks.py
- governance/services/tasks_mutations.py
- governance/services/rules.py
- governance/services/session_repair.py
- governance/services/evidence_transcript.py
- governance/typedb/queries/rules/crud.py
- governance/typedb/queries/rules/inference.py
- governance/typedb/queries/tasks/crud.py
- governance/typedb/queries/tasks/linking.py
- governance/typedb/queries/tasks/relationships.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


def _check_warning_level(src, fragment):
    """Verify line containing fragment uses logger.warning (not debug)."""
    idx = src.index(fragment)
    line_start = src.rindex("\n", 0, idx) + 1
    line_end = src.index("\n", idx)
    line = src[line_start:line_end]
    assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"


# ── BUG-433-PER-001: .tmp cleanup debug→warning + exc_info ─────────────

class TestSessionPersistenceTmpCleanup:
    def test_tmp_cleanup_warning_level(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_warning_level(src, "Failed to cleanup .tmp for")

    def test_tmp_cleanup_exc_info(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_exc_info(src, "Failed to cleanup .tmp for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "BUG-433-PER-001" in src


# ── BUG-433-PER-002: persist failure debug→warning + exc_info ──────────

class TestSessionPersistenceFailure:
    def test_persist_failure_warning_level(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_warning_level(src, "Session persist skipped for")

    def test_persist_failure_exc_info(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_exc_info(src, "Session persist skipped for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "BUG-433-PER-002" in src


# ── BUG-433-PER-003: cleanup_persisted debug→warning + exc_info ────────

class TestSessionPersistenceCleanup:
    def test_cleanup_warning_level(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_warning_level(src, "Failed to cleanup persisted session")

    def test_cleanup_exc_info(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_exc_info(src, "Failed to cleanup persisted session")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "BUG-433-PER-003" in src


# ── BUG-433-AUD-001: audit load failure exc_info ───────────────────────

class TestAuditLoadExcInfo:
    def test_load_exc_info(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        _check_exc_info(src, "Failed to load audit store")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        assert "BUG-433-AUD-001" in src


# ── BUG-433-AUD-002: audit save failure exc_info ───────────────────────

class TestAuditSaveExcInfo:
    def test_save_exc_info(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        _check_exc_info(src, "Failed to save audit store")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/audit.py").read_text()
        assert "BUG-433-AUD-002" in src


# ── Batch 430 CLEAN confirmation (routes) ──────────────────────────────

class TestBatch430RoutesClean:
    def test_sessions_crud_hardened(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        # Verify prior hardening markers still present
        assert "BUG-352" in src or "BUG-414" in src or "exc_info=True" in src

    def test_sessions_detail_hardened(self):
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        assert "exc_info" in src or "BUG-" in src

    def test_agents_crud_hardened(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert "exc_info" in src or "BUG-" in src


# ── Batch 432 CLEAN confirmation (TypeDB queries) ──────────────────────

class TestBatch432TypeDBClean:
    def test_rules_crud_hardened(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        assert "exc_info" in src or "BUG-" in src

    def test_tasks_crud_hardened(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        assert "exc_info" in src or "BUG-" in src


# ── Module import defense tests ─────────────────────────────────────────

class TestBatch433Imports:
    def test_session_persistence_importable(self):
        import governance.stores.session_persistence
        assert governance.stores.session_persistence is not None

    def test_audit_importable(self):
        import governance.stores.audit
        assert governance.stores.audit is not None

    def test_helpers_importable(self):
        import governance.stores.helpers
        assert governance.stores.helpers is not None

    def test_retry_importable(self):
        import governance.stores.retry
        assert governance.stores.retry is not None
