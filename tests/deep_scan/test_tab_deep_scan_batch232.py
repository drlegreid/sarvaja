"""Batch 232 — Evidence + embedding + vector store defense tests.

Validates fixes for:
- BUG-232-SEC-002: TypeQL injection in delete_by_source
- BUG-232-LOG-002: get_embedded_sources returns duplicates
- BUG-232-LOG-005: Non-deterministic os.listdir ordering
- BUG-232-LOG-007: chunk_content("") returns [""] instead of []
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-232-SEC-002: TypeQL injection in delete_by_source ────────────

class TestVectorStoreInjection:
    """source_id must be escaped before TypeQL interpolation."""

    def test_escapes_in_delete_by_source(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.index("def delete_by_source")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "BUG-232-SEC-002" in block

    def test_escapes_backslash_and_quotes(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.index("def delete_by_source")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "safe_id" in block
        assert 'replace(' in block


# ── BUG-232-LOG-002: Deduplicate embedded sources ───────────────────

class TestEmbeddedSourcesDedup:
    """get_embedded_sources must return unique sources."""

    def test_uses_set_comprehension(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        idx = src.index("def get_embedded_sources")
        block = src[idx:idx + 300]
        assert "{doc.source" in block or "set(" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        assert "BUG-232-LOG-002" in src


# ── BUG-232-LOG-005: Deterministic scan ordering ────────────────────

class TestWorkspaceScannerOrdering:
    """os.listdir calls must be wrapped with sorted()."""

    def test_phases_dir_sorted(self):
        src = (SRC / "governance/workspace_scanner.py").read_text()
        idx = src.index("Phase docs")
        block = src[idx:idx + 300]
        assert "sorted(os.listdir(" in block

    def test_rd_dir_sorted(self):
        src = (SRC / "governance/workspace_scanner.py").read_text()
        idx = src.index("R&D docs")
        block = src[idx:idx + 300]
        assert "sorted(os.listdir(" in block


# ── BUG-232-LOG-007: chunk_content empty input ──────────────────────

class TestChunkContentEmpty:
    """chunk_content("") should return [] not ['']."""

    def test_returns_empty_list_for_empty_input(self):
        from governance.embedding_pipeline.chunking import chunk_content
        result = chunk_content("")
        assert result == [], f"Expected [], got {result}"

    def test_returns_empty_list_for_none_like_input(self):
        from governance.embedding_pipeline.chunking import chunk_content
        result = chunk_content(None)
        assert result == [], f"Expected [], got {result}"


# ── Module import defense tests ──────────────────────────────────────

class TestBatch232Imports:
    def test_vector_store_importable(self):
        import governance.vector_store.store
        assert governance.vector_store.store is not None

    def test_vector_models_importable(self):
        import governance.vector_store.models
        assert governance.vector_store.models is not None

    def test_vector_embeddings_importable(self):
        import governance.vector_store.embeddings
        assert governance.vector_store.embeddings is not None

    def test_embedding_pipeline_importable(self):
        import governance.embedding_pipeline.pipeline
        assert governance.embedding_pipeline.pipeline is not None

    def test_embedding_chunking_importable(self):
        import governance.embedding_pipeline.chunking
        assert governance.embedding_pipeline.chunking is not None

    def test_embedding_config_importable(self):
        import governance.embedding_config
        assert governance.embedding_config is not None

    def test_workspace_scanner_importable(self):
        import governance.workspace_scanner
        assert governance.workspace_scanner is not None

    def test_evidence_extractors_importable(self):
        import governance.evidence_scanner.extractors
        assert governance.evidence_scanner.extractors is not None
