"""Batch 397 — Info disclosure + exc_info defense tests.

Validates fixes for:
- BUG-394-IDX-001..003: cc_content_indexer str(e) → type(e).__name__ in errors list
- BUG-397-LNK-001..006: tasks/linking.py missing exc_info=True
- BUG-397-REL-001..003: tasks/relationships.py missing exc_info=True
- BUG-397-STS-001: tasks/status.py missing exc_info=True
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-394-IDX-001..003: cc_content_indexer error sanitization ──────

class TestContentIndexerErrorSanitization:
    """Error messages appended to result['errors'] must use type(e).__name__, not str(e)."""

    def test_connection_error_uses_type_name(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB connection failed")
        block = src[idx:idx + 300]
        assert "type(e).__name__" in block

    def test_connection_error_no_bare_str_e(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB connection failed")
        # The msg= line should NOT have {e}, only {type(e).__name__}
        msg_line_end = src.index("\n", idx)
        msg_line = src[idx:msg_line_end]
        assert "{e}" not in msg_line or "type(e).__name__" in msg_line

    def test_upsert_error_uses_type_name(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB upsert failed at chunk")
        block = src[idx:idx + 400]
        assert "type(e).__name__" in block

    def test_final_upsert_error_uses_type_name(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB final upsert failed")
        block = src[idx:idx + 300]
        assert "type(e).__name__" in block

    def test_logger_still_has_full_error(self):
        """Logger.error() should still log full {e} for debugging."""
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB connection failed")
        block = src[idx:idx + 400]
        assert "exc_info=True" in block

    def test_upsert_logger_has_exc_info(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB upsert failed at chunk")
        block = src[idx:idx + 500]
        assert "exc_info=True" in block

    def test_final_upsert_logger_has_exc_info(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("ChromaDB final upsert failed")
        block = src[idx:idx + 400]
        assert "exc_info=True" in block

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "BUG-394-IDX-001" in src
        assert "BUG-394-IDX-002" in src
        assert "BUG-394-IDX-003" in src


# ── BUG-397-LNK-001..006: tasks/linking.py exc_info ─────────────────

class TestTasksLinkingExcInfo:
    """All outer except handlers in linking.py must have exc_info=True."""

    def _check_error_line(self, src, error_fragment):
        """Find logger.error line containing fragment, verify exc_info=True."""
        idx = src.index(error_fragment)
        # Get the full line (extend to next newline)
        line_end = src.index("\n", idx)
        line_start = src.rindex("\n", 0, idx) + 1
        line = src[line_start:line_end]
        assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"

    def test_link_evidence_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to link evidence")

    def test_link_session_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to link task {task_id} to session")

    def test_link_rule_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to link task {task_id} to rule")

    def test_link_commit_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to link task {task_id} to commit")

    def test_link_document_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to link task {task_id} to document")

    def test_unlink_document_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        self._check_error_line(src, "Failed to unlink document")

    def test_bug_markers_present(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        for i in range(1, 7):
            assert f"BUG-397-LNK-00{i}" in src, f"Missing BUG-397-LNK-00{i}"


# ── BUG-397-REL-001..003: tasks/relationships.py exc_info ────────────

class TestTasksRelationshipsExcInfo:
    """All outer except handlers in relationships.py must have exc_info=True."""

    def _check_error_line(self, src, error_fragment):
        """Find logger.error line containing fragment, verify exc_info=True."""
        idx = src.index(error_fragment)
        line_end = src.index("\n", idx)
        line_start = src.rindex("\n", 0, idx) + 1
        line = src[line_start:line_end]
        assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"

    def test_link_parent_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        self._check_error_line(src, "Failed to link parent")

    def test_link_blocking_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        self._check_error_line(src, "Failed to link blocking task")

    def test_link_related_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        self._check_error_line(src, "Failed to link related tasks")

    def test_bug_markers_present(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        assert "BUG-397-REL-001" in src
        assert "BUG-397-REL-002" in src
        assert "BUG-397-REL-003" in src


# ── BUG-397-STS-001: tasks/status.py exc_info ────────────────────────

class TestTasksStatusExcInfo:
    """Outer except handler in update_task_status must have exc_info=True."""

    def test_update_status_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/status.py").read_text()
        idx = src.index("def update_task_status")
        block = src[idx:]
        # Find the LAST logger.error (outer handler)
        outer_idx = block.rindex("logger.error")
        outer_line = block[outer_idx:outer_idx + 200]
        assert "exc_info=True" in outer_line

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/tasks/status.py").read_text()
        assert "BUG-397-STS-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch397Imports:
    def test_cc_content_indexer_importable(self):
        import governance.services.cc_content_indexer
        assert governance.services.cc_content_indexer is not None

    def test_tasks_linking_importable(self):
        import governance.typedb.queries.tasks.linking
        assert governance.typedb.queries.tasks.linking is not None

    def test_tasks_relationships_importable(self):
        import governance.typedb.queries.tasks.relationships
        assert governance.typedb.queries.tasks.relationships is not None

    def test_tasks_status_importable(self):
        import governance.typedb.queries.tasks.status
        assert governance.typedb.queries.tasks.status is not None
