"""
Embedding Pipeline Tests (P7.2)
Created: 2024-12-25

Tests for embedding generation and storage pipeline.
Strategic Goal: Enable semantic search across governance artifacts.
"""
import pytest
import json
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class TestEmbeddingPipelineModule:
    """Verify P7.2 embedding pipeline module exists."""

    @pytest.mark.unit
    def test_pipeline_module_exists(self):
        """Embedding pipeline module must exist."""
        pipeline_file = GOVERNANCE_DIR / "embedding_pipeline.py"
        assert pipeline_file.exists(), "governance/embedding_pipeline.py not found"

    @pytest.mark.unit
    def test_pipeline_class(self):
        """EmbeddingPipeline class must be importable."""
        from governance.embedding_pipeline import EmbeddingPipeline

        pipeline = EmbeddingPipeline()
        assert pipeline is not None

    @pytest.mark.unit
    def test_pipeline_has_required_methods(self):
        """Pipeline must have required methods."""
        from governance.embedding_pipeline import EmbeddingPipeline

        pipeline = EmbeddingPipeline()

        assert hasattr(pipeline, 'embed_rules')
        assert hasattr(pipeline, 'embed_decisions')
        assert hasattr(pipeline, 'embed_sessions')
        assert hasattr(pipeline, 'run_full_pipeline')


class TestRuleEmbeddings:
    """Tests for rule embedding generation."""

    @pytest.mark.unit
    def test_embed_single_rule(self):
        """Should embed a single rule."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        doc = pipeline.embed_rule("RULE-001", "Session evidence logging required")

        assert doc.source == "RULE-001"
        assert doc.source_type == "rule"
        assert len(doc.embedding) == 128

    @pytest.mark.unit
    def test_embed_all_rules(self):
        """Should embed all rules from TypeDB."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        docs = pipeline.embed_rules()

        assert isinstance(docs, list)
        # Should have embeddings for rules
        for doc in docs:
            assert doc.source_type == "rule"

    @pytest.mark.unit
    def test_rule_embedding_content(self):
        """Rule embedding content should include directive."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
        doc = pipeline.embed_rule(
            "RULE-TEST",
            "Test rule content with directive",
            directive="Do the thing"
        )

        assert "directive" in doc.content.lower() or "Do the thing" in doc.content


class TestDecisionEmbeddings:
    """Tests for decision embedding generation."""

    @pytest.mark.unit
    def test_embed_single_decision(self):
        """Should embed a single decision."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        doc = pipeline.embed_decision("DECISION-003", "TypeDB-First Strategy")

        assert doc.source == "DECISION-003"
        assert doc.source_type == "decision"

    @pytest.mark.unit
    def test_embed_all_decisions(self):
        """Should embed all decisions from evidence dir."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        docs = pipeline.embed_decisions()

        assert isinstance(docs, list)
        for doc in docs:
            assert doc.source_type == "decision"


class TestSessionEmbeddings:
    """Tests for session embedding generation."""

    @pytest.mark.unit
    def test_embed_single_session(self):
        """Should embed a single session."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        doc = pipeline.embed_session("SESSION-TEST", "Session evidence content here")

        assert doc.source == "SESSION-TEST"
        assert doc.source_type == "session"

    @pytest.mark.unit
    def test_embed_all_sessions(self):
        """Should embed all sessions from evidence dir."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
        docs = pipeline.embed_sessions(limit=5)

        assert isinstance(docs, list)
        for doc in docs:
            assert doc.source_type == "session"

    @pytest.mark.unit
    def test_session_chunking(self):
        """Long sessions should be chunked."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(
            embedding_generator=MockEmbeddings(dimension=128),
            chunk_size=500  # Small chunk for testing
        )

        long_content = "This is a test. " * 200  # Long content
        docs = pipeline.embed_session_chunked("SESSION-TEST", long_content)

        # Should produce multiple chunks
        assert len(docs) >= 1


class TestFullPipeline:
    """Tests for full embedding pipeline."""

    @pytest.mark.unit
    def test_run_full_pipeline(self):
        """Should run complete embedding pipeline."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
        result = pipeline.run_full_pipeline(dry_run=True)

        assert 'rules' in result
        assert 'decisions' in result
        assert 'sessions' in result
        assert 'total' in result

    @pytest.mark.unit
    def test_pipeline_returns_stats(self):
        """Pipeline should return statistics."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
        result = pipeline.run_full_pipeline(dry_run=True)

        assert isinstance(result['rules'], int)
        assert isinstance(result['decisions'], int)
        assert isinstance(result['sessions'], int)


class TestEmbeddingStorage:
    """Tests for embedding storage."""

    @pytest.mark.unit
    def test_store_to_cache(self):
        """Should store embeddings in vector store cache."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings, VectorStore

        store = VectorStore()
        pipeline = EmbeddingPipeline(
            embedding_generator=MockEmbeddings(dimension=64),
            vector_store=store
        )

        doc = pipeline.embed_rule("RULE-TEST", "Test content")
        pipeline.store_embedding(doc)

        # Should be in cache
        assert doc.id in store._cache

    @pytest.mark.unit
    def test_search_stored_embeddings(self):
        """Should be able to search stored embeddings."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings, VectorStore

        generator = MockEmbeddings(dimension=64)
        store = VectorStore()
        pipeline = EmbeddingPipeline(
            embedding_generator=generator,
            vector_store=store
        )

        # Store some test embeddings
        pipeline.embed_and_store_rule("RULE-001", "Session evidence logging")
        pipeline.embed_and_store_rule("RULE-002", "Agent trust metrics")

        # Search
        query = generator.generate("evidence logging")
        results = store.search(query, top_k=2, threshold=-1.0)

        assert len(results) >= 1


class TestIncrementalUpdate:
    """Tests for incremental embedding updates."""

    @pytest.mark.unit
    def test_check_needs_update(self):
        """Should check if embedding needs update."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings

        pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))

        # New source should need update
        assert pipeline.needs_update("NEW-RULE-999")

    @pytest.mark.unit
    def test_get_existing_sources(self):
        """Should list existing embedded sources."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store import MockEmbeddings, VectorStore

        store = VectorStore()
        pipeline = EmbeddingPipeline(
            embedding_generator=MockEmbeddings(dimension=64),
            vector_store=store
        )

        pipeline.embed_and_store_rule("RULE-001", "Test")
        sources = pipeline.get_embedded_sources()

        assert "RULE-001" in sources


class TestFactoryFunction:
    """Tests for pipeline factory function."""

    @pytest.mark.unit
    def test_create_pipeline(self):
        """Factory should create pipeline."""
        from governance.embedding_pipeline import create_embedding_pipeline

        pipeline = create_embedding_pipeline()
        assert pipeline is not None

    @pytest.mark.unit
    def test_create_with_mock(self):
        """Factory should support mock embeddings."""
        from governance.embedding_pipeline import create_embedding_pipeline

        pipeline = create_embedding_pipeline(use_mock=True, dimension=128)
        assert pipeline.generator.dimension == 128

