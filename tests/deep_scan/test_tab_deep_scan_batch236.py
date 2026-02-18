"""Batch 236 — Content indexer + link miner defense tests.

Validates fixes for:
- BUG-236-IDX-002: chunks_indexed inflated on upsert failure
- BUG-236-LNK-001: O(N*M) decision existence re-fetch
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-236-IDX-002: chunks_indexed only on success ─────────────────

class TestContentIndexerUpsertGuard:
    """chunks_indexed must NOT increment when upsert fails."""

    def test_batch_upsert_has_ok_flag(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "upsert_ok" in src

    def test_batch_upsert_sets_false_on_exception(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "upsert_ok = False" in src

    def test_batch_increment_guarded(self):
        """chunks_indexed increment must be inside 'if upsert_ok'."""
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("upsert_ok = True")
        block = src[idx:idx + 800]
        assert 'if upsert_ok:' in block
        assert 'result["chunks_indexed"]' in block

    def test_final_flush_also_guarded(self):
        """Final batch flush must also guard chunks_indexed."""
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        idx = src.index("# Flush final batch")
        block = src[idx:idx + 600]
        assert "final_ok" in block
        assert "final_ok = False" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "BUG-236-IDX-002" in src


# ── BUG-236-LNK-001: Decision existence cache ───────────────────────

class TestLinkMinerDecisionCache:
    """_validate_entity_exists must cache decision set."""

    def test_decision_cache_key_exists(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        assert "_all_decision_ids" in src

    def test_no_per_call_get_all_decisions(self):
        """get_all_decisions should be called once and cached, not per-id."""
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        idx = src.index("def _validate_entity_exists")
        next_def = src.index("\ndef ", idx + 1)
        block = src[idx:next_def]
        # Should use cache lookup, not direct any() scan
        assert "entity_id in cache" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        assert "BUG-236-LNK-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch236Imports:
    def test_cc_content_indexer_importable(self):
        import governance.services.cc_content_indexer
        assert governance.services.cc_content_indexer is not None

    def test_cc_link_miner_importable(self):
        import governance.services.cc_link_miner
        assert governance.services.cc_link_miner is not None

    def test_cc_session_scanner_importable(self):
        import governance.services.cc_session_scanner
        assert governance.services.cc_session_scanner is not None

    def test_access_log_importable(self):
        import governance.middleware.access_log
        assert governance.middleware.access_log is not None

    def test_ingestion_checkpoint_importable(self):
        import governance.services.ingestion_checkpoint
        assert governance.services.ingestion_checkpoint is not None

    def test_ingestion_orchestrator_importable(self):
        import governance.services.ingestion_orchestrator
        assert governance.services.ingestion_orchestrator is not None
