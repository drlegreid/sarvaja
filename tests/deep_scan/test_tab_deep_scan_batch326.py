"""
Deep Scan Batch 326-329 Defense Tests.

Validates 5 production fixes:
- BUG-329-AUD-001: audit.py tmp initialized before try (prevents UnboundLocalError)
- BUG-329-AUD-002: audit.py _apply_retention uses slice assignment (thread-safe)
- BUG-327-AGT-001: agents.py list_agents offset/limit clamped at service layer
- BUG-329-PERSIST-001: session_persistence.py glob load capped at 10000 files
- BUG-328-TASK-001: tasks/crud.py document_path length/type validation
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-329-AUD-001: audit.py tmp initialization before try
# ============================================================

class TestAuditTmpInitialization:
    """Verify audit.py initializes tmp=None before try block."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "audit.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-329-AUD-001" in src

    def test_tmp_initialized_before_try(self):
        """tmp must be initialized to None before the try block."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_save_audit_store":
                func_src = ast.get_source_segment(src, node)
                # tmp = None should appear before try:
                tmp_idx = func_src.index("tmp = None")
                try_idx = func_src.index("try:")
                assert tmp_idx < try_idx, \
                    "tmp = None must appear before try: in _save_audit_store"
                break
        else:
            raise AssertionError("_save_audit_store not found")

    def test_tmp_guarded_in_except(self):
        """tmp.unlink must be guarded by 'if tmp is not None'."""
        src = self._get_source()
        assert "if tmp is not None" in src, \
            "tmp.unlink must be guarded by 'if tmp is not None'"


# ============================================================
# BUG-329-AUD-002: audit.py slice assignment in retention
# ============================================================

class TestAuditRetentionSliceAssignment:
    """Verify _apply_retention uses slice assignment instead of rebinding."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "audit.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-329-AUD-002" in src

    def test_slice_assignment_used(self):
        """_apply_retention must use _audit_store[:] = [...] not _audit_store = [...]."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_apply_retention":
                func_src = ast.get_source_segment(src, node)
                assert "_audit_store[:] =" in func_src, \
                    "_apply_retention must use slice assignment _audit_store[:] ="
                break
        else:
            raise AssertionError("_apply_retention not found")


# ============================================================
# BUG-327-AGT-001: agents.py list_agents service-layer bounds
# ============================================================

class TestAgentsListBounds:
    """Verify agents.py list_agents clamps offset/limit at service layer."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "agents.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-327-AGT-001" in src

    def test_offset_clamped(self):
        src = self._get_source()
        assert "max(0, offset)" in src

    def test_limit_upper_bound(self):
        src = self._get_source()
        assert "min(limit, 200)" in src

    def test_limit_lower_bound(self):
        src = self._get_source()
        # Check that limit has a lower bound of 1
        assert "max(1," in src


# ============================================================
# BUG-329-PERSIST-001: session_persistence.py glob load cap
# ============================================================

class TestSessionPersistenceGlobCap:
    """Verify session_persistence.py caps the glob load on startup."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "session_persistence.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-329-PERSIST-001" in src

    def test_max_session_files_constant(self):
        src = self._get_source()
        assert "_MAX_SESSION_FILES" in src

    def test_glob_result_sliced(self):
        """glob("*.json") result must be sliced to cap file count."""
        src = self._get_source()
        assert "[:_MAX_SESSION_FILES]" in src


# ============================================================
# BUG-328-TASK-001: tasks/crud.py document_path validation
# ============================================================

class TestTaskDocumentPathValidation:
    """Verify tasks/crud.py validates document_path in link endpoint."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "tasks" / "crud.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-328-TASK-001" in src

    def test_length_validation(self):
        src = self._get_source()
        assert "500" in src, "document_path should be capped at 500 chars"

    def test_type_validation(self):
        src = self._get_source()
        assert "isinstance(document_path, str)" in src, \
            "document_path should be type-checked as string"

    def test_422_on_invalid(self):
        """Invalid document_path should return 422."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "link_task_to_document":
                func_src = ast.get_source_segment(src, node)
                assert "422" in func_src
                assert "document_path must be" in func_src
                break


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch326Imports:
    """Verify all fixed modules import without errors."""

    def test_import_audit(self):
        import governance.stores.audit
        assert hasattr(governance.stores.audit, 'record_audit')

    def test_import_agents(self):
        import governance.services.agents
        assert hasattr(governance.services.agents, 'list_agents')

    def test_import_session_persistence(self):
        import governance.stores.session_persistence
        assert hasattr(governance.stores.session_persistence, 'load_persisted_sessions')

    def test_import_tasks_crud(self):
        import governance.routes.tasks.crud
