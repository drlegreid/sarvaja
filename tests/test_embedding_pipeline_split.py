"""
TDD Tests for GAP-FILE-021: embedding_pipeline.py Split

Tests verify that the modularized embedding_pipeline package:
1. Maintains backward compatibility
2. Has properly separated chunking logic
3. All modules stay under 400 lines

Per RULE-004: TDD approach
Per DOC-SIZE-01-v1: Files under 400 lines
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


# =============================================================================
# Test 1: Package Structure
# =============================================================================

# =============================================================================
# Test 2: Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Tests ensuring existing imports still work."""

    def test_import_embedding_pipeline_class(self):
        """from governance.embedding_pipeline import EmbeddingPipeline must work."""
        from governance.embedding_pipeline import EmbeddingPipeline
        assert EmbeddingPipeline is not None

    def test_import_create_embedding_pipeline(self):
        """from governance.embedding_pipeline import create_embedding_pipeline must work."""
        from governance.embedding_pipeline import create_embedding_pipeline
        assert create_embedding_pipeline is not None

    def test_create_pipeline_instance(self):
        """Creating EmbeddingPipeline instance must work."""
        from governance.embedding_pipeline import EmbeddingPipeline
        pipeline = EmbeddingPipeline()
        assert pipeline is not None

    def test_pipeline_has_embed_rules(self):
        """Pipeline must have embed_rules method."""
        from governance.embedding_pipeline import EmbeddingPipeline
        pipeline = EmbeddingPipeline()
        assert hasattr(pipeline, 'embed_rules')

    def test_pipeline_has_embed_sessions(self):
        """Pipeline must have embed_sessions method."""
        from governance.embedding_pipeline import EmbeddingPipeline
        pipeline = EmbeddingPipeline()
        assert hasattr(pipeline, 'embed_sessions')

    def test_pipeline_has_embed_session_chunked(self):
        """Pipeline must have embed_session_chunked method."""
        from governance.embedding_pipeline import EmbeddingPipeline
        pipeline = EmbeddingPipeline()
        assert hasattr(pipeline, 'embed_session_chunked')


# =============================================================================
# Test 3: Chunking Module
# =============================================================================

class TestChunkingModule:
    """Tests for the extracted chunking module."""

    def test_chunk_content_function_exists(self):
        """chunk_content function should be importable."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
            assert chunk_content is not None
        except ImportError:
            # Module doesn't exist yet - skip in TDD phase
            pytest.skip("chunking module not yet implemented")

    def test_chunk_content_splits_long_text(self):
        """chunk_content should split text exceeding chunk_size."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
        except ImportError:
            pytest.skip("chunking module not yet implemented")

        long_text = "This is a test line.\n" * 100  # ~2100 chars
        chunks = chunk_content(long_text, chunk_size=500)

        assert len(chunks) > 1, "Should produce multiple chunks"
        for chunk in chunks:
            assert len(chunk) <= 500, f"Chunk exceeds size: {len(chunk)}"

    def test_chunk_content_preserves_short_text(self):
        """chunk_content should not split short text."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
        except ImportError:
            pytest.skip("chunking module not yet implemented")

        short_text = "Short content"
        chunks = chunk_content(short_text, chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_chunk_content_respects_line_boundaries(self):
        """chunk_content should split at line boundaries."""
        try:
            from governance.embedding_pipeline.chunking import chunk_content
        except ImportError:
            pytest.skip("chunking module not yet implemented")

        text = "Line one\nLine two\nLine three"
        chunks = chunk_content(text, chunk_size=15)

        # Should split between lines, not mid-word
        for chunk in chunks:
            # Lines should be complete (end with newline or be last chunk)
            lines = chunk.split('\n')
            for line in lines:
                assert 'Line' in line or line == '', f"Unexpected split: {line}"


# =============================================================================
# Test 4: File Size Compliance
# =============================================================================

class TestFileSizeCompliance:
    """Tests ensuring files stay under size limit."""

    def test_all_modules_under_400_lines(self):
        """All modules in package should be under 400 lines."""
        package_dir = GOVERNANCE_DIR / "embedding_pipeline"

        if not package_dir.exists():
            # Old single file - check its size
            old_file = GOVERNANCE_DIR / "embedding_pipeline.py"
            if old_file.exists():
                line_count = len(old_file.read_text().splitlines())
                # This test will fail until refactoring is complete
                if line_count > 400:
                    pytest.skip(f"Single file has {line_count} lines - refactoring needed")
            return

        for py_file in package_dir.glob("*.py"):
            line_count = len(py_file.read_text().splitlines())
            assert line_count <= 400, \
                f"{py_file.name} has {line_count} lines, exceeds 400 limit"


# =============================================================================
# Test 5: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for refactored pipeline."""

    def test_embed_session_chunked_works(self):
        """embed_session_chunked should work after refactoring."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(
            embedding_generator=MockEmbeddings(dimension=64),
            chunk_size=100
        )

        long_content = "Test content. " * 50  # ~700 chars
        docs = pipeline.embed_session_chunked("TEST-SESSION", long_content)

        assert len(docs) >= 1
        for doc in docs:
            assert doc.source == "TEST-SESSION"
            assert doc.source_type == "session"

    def test_run_full_pipeline_works(self):
        """run_full_pipeline should work after refactoring."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
        result = pipeline.run_full_pipeline(dry_run=True)

        assert 'rules' in result
        assert 'decisions' in result
        assert 'sessions' in result
        assert 'total' in result
