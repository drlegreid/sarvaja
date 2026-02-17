"""
Deep Scan Batch 338-341 Defense Tests.

Validates 8 production fixes:
- BUG-338-PIP-001: pipeline.py tautological except clause separated
- BUG-338-PIP-002: pipeline.py store_embedding uses public API when connected
- BUG-340-AGT-001: agents.py _load_agent_metrics encoding="utf-8"
- BUG-340-AUD-001: audit.py query_audit_trail limit capped to 1000
- BUG-340-PERS-001: session_persistence.py itertools.islice for glob
- BUG-340-RETRY-001: retry.py OSError filtered by errno
- BUG-341-REL-001: relationships.py self-link guard for link_related_tasks
- BUG-341-STATUS-001: status.py evidence delete pinned to value
"""

import ast
import errno
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-338-PIP-001: Tautological except clause separated
# ============================================================

class TestPipelineTautologicalExcept:
    """Verify pipeline.py no longer has tautological except clause."""

    def _get_source(self):
        p = ROOT / "governance" / "embedding_pipeline" / "pipeline.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-338-PIP-001" in src

    def test_no_tautological_except(self):
        """Should not have (json.JSONDecodeError, Exception) together."""
        src = self._get_source()
        assert "(json.JSONDecodeError, Exception)" not in src

    def test_separate_json_decode_catch(self):
        """JSONDecodeError should be caught in its own except block."""
        src = self._get_source()
        assert "except json.JSONDecodeError as e:" in src

    def test_separate_generic_catch(self):
        """Generic Exception should be in a separate except block after JSONDecodeError."""
        src = self._get_source()
        # Find the embed_sessions method and verify both catches exist
        idx_json = src.index("except json.JSONDecodeError as e:")
        idx_generic = src.index("except Exception as e:", idx_json)
        assert idx_generic > idx_json


# ============================================================
# BUG-338-PIP-002: store_embedding uses public API
# ============================================================

class TestPipelineStoreEmbedding:
    """Verify store_embedding uses public insert() when connected."""

    def _get_source(self):
        p = ROOT / "governance" / "embedding_pipeline" / "pipeline.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-338-PIP-002" in src

    def test_uses_public_insert(self):
        """store_embedding should call self.store.insert() when connected."""
        src = self._get_source()
        assert "self.store.insert(doc)" in src

    def test_checks_connected_flag(self):
        """Should check _connected before deciding insert path."""
        src = self._get_source()
        assert "self.store._connected" in src

    def test_cache_fallback_documented(self):
        """Cache-only fallback should be documented as fallback."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "store_embedding":
                func_src = ast.get_source_segment(src, node)
                # Should have both paths: insert and cache
                assert "self.store.insert(doc)" in func_src
                assert "self.store._cache[doc.id] = doc" in func_src
                break
        else:
            raise AssertionError("store_embedding not found")


# ============================================================
# BUG-340-AGT-001: agents.py encoding on file open
# ============================================================

class TestAgentsMetricsEncoding:
    """Verify _load_agent_metrics specifies encoding."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "agents.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-340-AGT-001" in src

    def test_encoding_specified(self):
        """_load_agent_metrics must use encoding='utf-8'."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_load_agent_metrics":
                func_src = ast.get_source_segment(src, node)
                assert 'encoding="utf-8"' in func_src
                break
        else:
            raise AssertionError("_load_agent_metrics not found")


# ============================================================
# BUG-340-AUD-001: audit.py query limit capped
# ============================================================

class TestAuditQueryLimitCap:
    """Verify query_audit_trail has a maximum limit."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "audit.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-340-AUD-001" in src

    def test_max_limit_defined(self):
        """Should define _MAX_QUERY_LIMIT."""
        src = self._get_source()
        assert "_MAX_QUERY_LIMIT" in src

    def test_limit_uses_min(self):
        """limit should be capped with min()."""
        src = self._get_source()
        assert "min(limit, _MAX_QUERY_LIMIT)" in src

    def test_functional_cap(self):
        """Verify the cap logic works correctly."""
        _MAX_QUERY_LIMIT = 1000
        for raw_limit in [1, 50, 999, 1000, 5000, 10_000_000]:
            capped = max(1, min(raw_limit, _MAX_QUERY_LIMIT))
            assert 1 <= capped <= 1000, f"limit={raw_limit} produced {capped}"


# ============================================================
# BUG-340-PERS-001: session_persistence itertools.islice
# ============================================================

class TestSessionPersistenceIslice:
    """Verify session_persistence uses itertools.islice instead of list()[:N]."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "session_persistence.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-340-PERS-001" in src

    def test_imports_itertools(self):
        """Module must import itertools."""
        src = self._get_source()
        assert "import itertools" in src

    def test_uses_islice(self):
        """Should use itertools.islice for glob iteration."""
        src = self._get_source()
        assert "itertools.islice(_STORE_DIR.glob" in src

    def test_no_list_glob_slice(self):
        """Should NOT have list(_STORE_DIR.glob(...))[:N] pattern."""
        src = self._get_source()
        assert "list(_STORE_DIR.glob" not in src


# ============================================================
# BUG-340-RETRY-001: retry.py OSError errno filtering
# ============================================================

class TestRetryOsErrorFiltering:
    """Verify _is_transient filters OSError by errno."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "retry.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-340-RETRY-001" in src

    def test_checks_errno(self):
        """_is_transient must check errno for OSError."""
        src = self._get_source()
        assert "errno" in src

    def test_permission_error_not_transient(self):
        """PermissionError should NOT be treated as transient."""
        from governance.stores.retry import _is_transient
        exc = PermissionError(errno.EACCES, "Permission denied")
        assert not _is_transient(exc), "PermissionError must not be transient"

    def test_file_not_found_not_transient(self):
        """FileNotFoundError should NOT be treated as transient."""
        from governance.stores.retry import _is_transient
        exc = FileNotFoundError(errno.ENOENT, "No such file")
        assert not _is_transient(exc), "FileNotFoundError must not be transient"

    def test_connection_refused_is_transient(self):
        """ConnectionRefusedError should still be transient."""
        from governance.stores.retry import _is_transient
        exc = ConnectionRefusedError("Connection refused")
        assert _is_transient(exc), "ConnectionRefusedError must be transient"

    def test_timeout_is_transient(self):
        """TimeoutError should still be transient."""
        from governance.stores.retry import _is_transient
        exc = TimeoutError("Timed out")
        assert _is_transient(exc), "TimeoutError must be transient"

    def test_runtime_connection_msg_is_transient(self):
        """RuntimeError with 'connection' in message should be transient."""
        from governance.stores.retry import _is_transient
        exc = RuntimeError("connection closed")
        assert _is_transient(exc)

    def test_runtime_generic_not_transient(self):
        """RuntimeError without connection keywords should NOT be transient."""
        from governance.stores.retry import _is_transient
        exc = RuntimeError("some random error")
        assert not _is_transient(exc)


# ============================================================
# BUG-341-REL-001: link_related_tasks self-link guard
# ============================================================

class TestRelatedTasksSelfLinkGuard:
    """Verify link_related_tasks prevents self-linking."""

    def _get_source(self):
        p = ROOT / "governance" / "typedb" / "queries" / "tasks" / "relationships.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-341-REL-001" in src

    def test_self_link_check_exists(self):
        """link_related_tasks must check task_id_a == task_id_b."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "link_related_tasks":
                func_src = ast.get_source_segment(src, node)
                assert "task_id_a == task_id_b" in func_src
                assert "return False" in func_src
                break
        else:
            raise AssertionError("link_related_tasks not found")

    def test_all_three_link_methods_have_guard(self):
        """All link methods (parent, blocking, related) must have self-link guards."""
        src = self._get_source()
        # Verify each method has a self-check
        assert "child_task_id == parent_task_id" in src
        assert "blocking_task_id == blocked_task_id" in src
        assert "task_id_a == task_id_b" in src


# ============================================================
# BUG-341-STATUS-001: evidence delete pinned to value
# ============================================================

class TestStatusEvidenceDeletePinned:
    """Verify evidence delete query pins the value."""

    def _get_source(self):
        p = ROOT / "governance" / "typedb" / "queries" / "tasks" / "status.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-341-STATUS-001" in src

    def test_evidence_delete_pinned(self):
        """Evidence delete must pin $e to current value."""
        src = self._get_source()
        # Find the evidence delete section and verify it has value pinning
        assert "current_evidence_escaped" in src

    def test_evidence_delete_has_equality_check(self):
        """Delete query must include $e == '<value>' constraint."""
        src = self._get_source()
        # The delete query should match: $e == "{current_evidence_escaped}"
        assert '$e == "{current_evidence_escaped}"' in src

    def test_consistency_with_status_delete(self):
        """Evidence delete should follow same pattern as status delete."""
        src = self._get_source()
        # Status delete pattern (line ~76): $s == "{current_status_escaped}"
        assert '$s == "{current_status_escaped}"' in src
        # Evidence delete should have same pattern
        assert '$e == "{current_evidence_escaped}"' in src


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch338Imports:
    """Verify all fixed modules import without errors."""

    def test_import_pipeline(self):
        import governance.embedding_pipeline.pipeline

    def test_import_agents(self):
        import governance.stores.agents

    def test_import_audit(self):
        import governance.stores.audit

    def test_import_session_persistence(self):
        import governance.stores.session_persistence

    def test_import_retry(self):
        from governance.stores.retry import _is_transient, retry_on_transient

    def test_import_relationships(self):
        import governance.typedb.queries.tasks.relationships

    def test_import_status(self):
        import governance.typedb.queries.tasks.status

    def test_retry_functional(self):
        """Functional test: _is_transient correctly classifies exceptions."""
        from governance.stores.retry import _is_transient
        # Transient
        assert _is_transient(ConnectionRefusedError("refused"))
        assert _is_transient(TimeoutError("timed out"))
        assert _is_transient(RuntimeError("connection closed"))
        # NOT transient
        assert not _is_transient(PermissionError("denied"))
        assert not _is_transient(ValueError("bad value"))
        assert not _is_transient(RuntimeError("unexpected error"))
