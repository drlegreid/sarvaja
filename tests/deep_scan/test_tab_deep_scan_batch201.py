"""Batch 201 — Embedding pipeline + audit store defense tests.

Validates fixes for:
- BUG-201-EMBED-001: embed_decisions isinstance guard
- BUG-201-EMBED-002: embed_sessions isinstance guard
- BUG-201-AUDIT-001: Atomic write in _save_audit_store
- BUG-201-AUDIT-002: encoding="utf-8" on audit file open
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-201-EMBED-001: embed_decisions isinstance guard ──────────────

class TestEmbedDecisionsGuard:
    """embed_decisions must handle list result without crashing."""

    def test_embed_decisions_has_isinstance_check(self):
        """Source must have isinstance(result, dict) check."""
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        # Find embed_decisions method
        in_func = False
        found_isinstance = False
        for line in src.splitlines():
            if "def embed_decisions" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "isinstance(result, dict)" in line:
                found_isinstance = True
        assert found_isinstance, "embed_decisions must check isinstance(result, dict)"

    def test_embed_sessions_has_isinstance_check(self):
        """embed_sessions source must have isinstance(result, dict) check."""
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        in_func = False
        found_isinstance = False
        for line in src.splitlines():
            if "def embed_sessions" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "isinstance(result, dict)" in line:
                found_isinstance = True
        assert found_isinstance, "embed_sessions must check isinstance(result, dict)"


# ── BUG-201-AUDIT-001: Atomic write ─────────────────────────────────

class TestAuditAtomicWrite:
    """_save_audit_store must use atomic write pattern."""

    def test_save_uses_temp_file(self):
        """_save_audit_store should write to .tmp then rename."""
        src = (SRC / "governance/stores/audit.py").read_text()
        in_func = False
        found_tmp = False
        found_replace = False
        for line in src.splitlines():
            if "def _save_audit_store" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func:
                if ".tmp" in line or "with_suffix" in line:
                    found_tmp = True
                if ".replace(" in line:
                    found_replace = True
        assert found_tmp, "_save_audit_store must write to temp file first"
        assert found_replace, "_save_audit_store must use atomic replace"


# ── BUG-201-AUDIT-002: Encoding on file open ────────────────────────

class TestAuditEncoding:
    """Audit store must specify encoding on all file opens."""

    def test_load_uses_utf8(self):
        """_load_audit_store must specify encoding='utf-8'."""
        src = (SRC / "governance/stores/audit.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def _load_audit_store" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "open(" in line:
                assert "encoding" in line, f"open() in _load_audit_store missing encoding: {line.strip()}"

    def test_save_uses_utf8(self):
        """_save_audit_store must specify encoding='utf-8'."""
        src = (SRC / "governance/stores/audit.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def _save_audit_store" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "open(" in line:
                assert "encoding" in line, f"open() in _save_audit_store missing encoding: {line.strip()}"


# ── Audit store functional tests ─────────────────────────────────────

class TestAuditStoreFunctional:
    """Functional tests for audit store operations."""

    def test_record_audit_creates_entry(self):
        from governance.stores.audit import record_audit, _audit_store
        initial_count = len(_audit_store)
        entry = record_audit(
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-TEST-201",
            actor_id="test-agent",
        )
        assert entry.audit_id.startswith("AUDIT-")
        assert entry.entity_id == "TASK-TEST-201"
        # Clean up
        while len(_audit_store) > initial_count:
            _audit_store.pop()

    def test_query_audit_trail_filters(self):
        from governance.stores.audit import query_audit_trail, _audit_store, record_audit
        initial_count = len(_audit_store)
        record_audit("UPDATE", "rule", "RULE-TEST-201", actor_id="test-agent")
        results = query_audit_trail(entity_type="rule", entity_id="RULE-TEST-201")
        assert len(results) >= 1
        assert results[0]["entity_id"] == "RULE-TEST-201"
        # Clean up
        while len(_audit_store) > initial_count:
            _audit_store.pop()

    def test_get_audit_summary_returns_dict(self):
        from governance.stores.audit import get_audit_summary
        summary = get_audit_summary()
        assert "total_entries" in summary
        assert "by_action_type" in summary
        assert "retention_days" in summary

    def test_generate_correlation_id_format(self):
        from governance.stores.audit import generate_correlation_id
        cid = generate_correlation_id()
        assert cid.startswith("CORR-")
        assert len(cid) > 15


# ── Embedding pipeline defense ───────────────────────────────────────

class TestEmbeddingPipelineDefense:
    """Defense tests for embedding pipeline components."""

    def test_chunk_content_empty(self):
        from governance.embedding_pipeline.chunking import chunk_content
        result = chunk_content("")
        assert result == [""]

    def test_chunk_content_small(self):
        from governance.embedding_pipeline.chunking import chunk_content
        result = chunk_content("hello world", 2000)
        assert result == ["hello world"]

    def test_truncate_content_within_limit(self):
        from governance.embedding_pipeline.chunking import truncate_content
        assert truncate_content("short", 2000) == "short"

    def test_truncate_content_exceeds_limit(self):
        from governance.embedding_pipeline.chunking import truncate_content
        result = truncate_content("a" * 100, 50)
        assert len(result) == 50
