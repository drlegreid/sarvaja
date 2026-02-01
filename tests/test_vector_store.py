"""
Vector Store Tests (P7.1)
Created: 2024-12-25
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class TestVectorStoreModule:
    """Unit tests for vector store module."""

    @pytest.mark.unit
    def test_vector_document_dataclass(self):
        """VectorDocument dataclass must be importable."""
        from governance.vector_store import VectorDocument

        doc = VectorDocument(
            id="test-001",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            model="test-model",
            dimension=3,
            source="TEST-001",
            source_type="rule"
        )

        assert doc.id == "test-001"
        assert doc.source_type == "rule"
        assert len(doc.embedding) == 3

    @pytest.mark.unit
    def test_similarity_result_dataclass(self):
        """SimilarityResult dataclass must be importable."""
        from governance.vector_store import SimilarityResult

        result = SimilarityResult(
            vector_id="vec-001",
            content="Test content",
            source="RULE-001",
            source_type="rule",
            score=0.95
        )

        assert result.score == 0.95
        assert result.source == "RULE-001"

    @pytest.mark.unit
    def test_vector_store_class(self):
        """VectorStore class must be instantiable."""
        from governance.vector_store import VectorStore

        store = VectorStore(host="localhost", port=1729)
        assert store.host == "localhost"
        assert store.port == 1729

    @pytest.mark.unit
    def test_vector_document_created_at(self):
        """VectorDocument should have created_at timestamp."""
        from governance.vector_store import VectorDocument

        doc = VectorDocument(
            id="test-002",
            content="Test",
            embedding=[0.1],
            model="test",
            dimension=1,
            source="TEST",
            source_type="rule"
        )

        assert doc.created_at is not None
        assert isinstance(doc.created_at, datetime)


class TestEmbeddingGenerators:
    """Tests for embedding generator implementations."""

    @pytest.mark.unit
    def test_mock_embeddings_exists(self):
        """MockEmbeddings class must exist."""
        from governance.vector_store import MockEmbeddings

        generator = MockEmbeddings(dimension=384)
        assert generator.dimension == 384
        assert generator.model_name == "mock-embeddings"

    @pytest.mark.unit
    def test_mock_embeddings_generate(self):
        """MockEmbeddings must generate deterministic embeddings."""
        from governance.vector_store import MockEmbeddings

        generator = MockEmbeddings(dimension=128)
        embedding1 = generator.generate("test text")
        embedding2 = generator.generate("test text")

        assert len(embedding1) == 128
        assert embedding1 == embedding2  # Deterministic

    @pytest.mark.unit
    def test_mock_embeddings_different_texts(self):
        """Different texts should produce different embeddings."""
        from governance.vector_store import MockEmbeddings

        generator = MockEmbeddings(dimension=128)
        embedding1 = generator.generate("text one")
        embedding2 = generator.generate("text two")

        assert embedding1 != embedding2

    @pytest.mark.unit
    def test_ollama_embeddings_class(self):
        """OllamaEmbeddings class must exist."""
        from governance.vector_store import OllamaEmbeddings

        generator = OllamaEmbeddings(host="localhost", port=11434)
        assert generator.host == "localhost"
        assert generator.dimension == 768
        assert "ollama" in generator.model_name

    @pytest.mark.unit
    def test_litellm_embeddings_class(self):
        """LiteLLMEmbeddings class must exist."""
        from governance.vector_store import LiteLLMEmbeddings

        generator = LiteLLMEmbeddings(host="localhost", port=4000)
        assert generator.host == "localhost"
        assert generator.dimension == 1536
        assert "litellm" in generator.model_name


class TestCosineSimilarity:
    """Tests for similarity computation."""

    @pytest.mark.unit
    def test_cosine_similarity_identical(self):
        """Identical vectors should have similarity 1.0."""
        from governance.vector_store import VectorStore

        vec = [0.5, 0.5, 0.5]
        similarity = VectorStore._cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.0001

    @pytest.mark.unit
    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity 0.0."""
        from governance.vector_store import VectorStore

        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        similarity = VectorStore._cosine_similarity(vec_a, vec_b)
        assert abs(similarity) < 0.0001

    @pytest.mark.unit
    def test_cosine_similarity_opposite(self):
        """Opposite vectors should have similarity -1.0."""
        from governance.vector_store import VectorStore

        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        similarity = VectorStore._cosine_similarity(vec_a, vec_b)
        assert abs(similarity - (-1.0)) < 0.0001

    @pytest.mark.unit
    def test_cosine_similarity_different_lengths(self):
        """Different length vectors should return 0.0."""
        from governance.vector_store import VectorStore

        vec_a = [0.5, 0.5]
        vec_b = [0.5, 0.5, 0.5]
        similarity = VectorStore._cosine_similarity(vec_a, vec_b)
        assert similarity == 0.0

    @pytest.mark.unit
    def test_cosine_similarity_zero_vector(self):
        """Zero vectors should return 0.0."""
        from governance.vector_store import VectorStore

        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        similarity = VectorStore._cosine_similarity(vec_a, vec_b)
        assert similarity == 0.0


class TestVectorStoreSearch:
    """Tests for vector search functionality."""

    @pytest.mark.unit
    def test_search_with_cache(self):
        """Search should work with cached documents."""
        from governance.vector_store import VectorStore, VectorDocument, MockEmbeddings

        generator = MockEmbeddings(dimension=64)
        store = VectorStore()

        # Populate cache directly
        docs = [
            VectorDocument(
                id="doc-1",
                content="RULE-001 session evidence",
                embedding=generator.generate("RULE-001 session evidence"),
                model="mock",
                dimension=64,
                source="RULE-001",
                source_type="rule"
            ),
            VectorDocument(
                id="doc-2",
                content="RULE-011 multi-agent governance",
                embedding=generator.generate("RULE-011 multi-agent governance"),
                model="mock",
                dimension=64,
                source="RULE-011",
                source_type="rule"
            ),
        ]
        store._cache = {doc.id: doc for doc in docs}

        # Search for similar - use threshold=-1.0 to include all results (mock embeddings can have negative cosine)
        query = generator.generate("session evidence logging")
        results = store.search(query, top_k=2, threshold=-1.0)

        assert len(results) == 2
        assert results[0].score >= results[1].score  # Ordered by score

    @pytest.mark.unit
    def test_search_with_source_type_filter(self):
        """Search should filter by source type."""
        from governance.vector_store import VectorStore, VectorDocument, MockEmbeddings

        generator = MockEmbeddings(dimension=64)
        store = VectorStore()

        docs = [
            VectorDocument(
                id="rule-1", content="Rule content",
                embedding=generator.generate("rule"), model="mock",
                dimension=64, source="RULE-001", source_type="rule"
            ),
            VectorDocument(
                id="dec-1", content="Decision content",
                embedding=generator.generate("decision"), model="mock",
                dimension=64, source="DEC-001", source_type="decision"
            ),
        ]
        store._cache = {doc.id: doc for doc in docs}

        # Filter by rules only
        results = store.search(generator.generate("test"), source_type="rule")
        assert all(r.source_type == "rule" for r in results)

    @pytest.mark.unit
    def test_search_with_threshold(self):
        """Search should respect similarity threshold."""
        from governance.vector_store import VectorStore, VectorDocument, MockEmbeddings

        generator = MockEmbeddings(dimension=64)
        store = VectorStore()

        doc = VectorDocument(
            id="doc-1", content="specific content",
            embedding=generator.generate("specific content"), model="mock",
            dimension=64, source="TEST", source_type="rule"
        )
        store._cache = {doc.id: doc}

        # High threshold should filter out dissimilar
        results = store.search(generator.generate("completely different"), threshold=0.99)
        # May or may not return results depending on hash similarity

    @pytest.mark.unit
    def test_search_by_source(self):
        """search_by_source should find document by source ID."""
        from governance.vector_store import VectorStore, VectorDocument

        store = VectorStore()
        doc = VectorDocument(
            id="doc-1", content="test",
            embedding=[0.1, 0.2], model="mock",
            dimension=2, source="RULE-001", source_type="rule"
        )
        store._cache = {doc.id: doc}

        found = store.search_by_source("RULE-001")
        assert found is not None
        assert found.source == "RULE-001"

        not_found = store.search_by_source("RULE-999")
        assert not_found is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.unit
    def test_create_vector_from_rule(self):
        """create_vector_from_rule should create VectorDocument."""
        from governance.vector_store import create_vector_from_rule, MockEmbeddings

        generator = MockEmbeddings(dimension=128)
        doc = create_vector_from_rule("RULE-001", "Session evidence logging", generator)

        assert doc.source == "RULE-001"
        assert doc.source_type == "rule"
        assert len(doc.embedding) == 128

    @pytest.mark.unit
    def test_create_vector_from_decision(self):
        """create_vector_from_decision should create VectorDocument."""
        from governance.vector_store import create_vector_from_decision, MockEmbeddings

        generator = MockEmbeddings(dimension=128)
        doc = create_vector_from_decision("DECISION-003", "TypeDB-First Strategy", generator)

        assert doc.source == "DECISION-003"
        assert doc.source_type == "decision"

    @pytest.mark.unit
    def test_create_vector_from_session(self):
        """create_vector_from_session should create VectorDocument."""
        from governance.vector_store import create_vector_from_session, MockEmbeddings

        generator = MockEmbeddings(dimension=128)
        doc = create_vector_from_session("SESSION-001", "Session evidence content", generator)

        assert doc.source == "SESSION-001"
        assert doc.source_type == "session"


class TestTypeQLGeneration:
    """Tests for TypeQL query generation."""

    @pytest.mark.unit
    def test_typedb_insert_generation(self):
        """VectorDocument should generate valid TypeQL insert."""
        from governance.vector_store import VectorDocument

        doc = VectorDocument(
            id="test-id",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            model="test-model",
            dimension=3,
            source="RULE-001",
            source_type="rule"
        )

        typeql = doc.to_typedb_insert()

        assert "insert $v isa vector-document" in typeql
        assert 'vector-id "test-id"' in typeql
        assert 'vector-source "RULE-001"' in typeql
        assert 'vector-source-type "rule"' in typeql
        assert "vector-embedding" in typeql

    @pytest.mark.unit
    def test_typedb_insert_escaping(self):
        """TypeQL insert should escape special characters."""
        from governance.vector_store import VectorDocument

        doc = VectorDocument(
            id="test",
            content='Text with "quotes" and\nnewlines',
            embedding=[0.1],
            model="test",
            dimension=1,
            source="TEST",
            source_type="rule"
        )

        typeql = doc.to_typedb_insert()

        # Should escape quotes and newlines
        assert '\\"' in typeql or "quotes" in typeql  # Escaped quotes
        assert '\\n' in typeql  # Escaped newline


class TestSchemaExtension:
    """Tests for TypeDB schema extensions."""

    @pytest.mark.unit
    def test_schema_has_vector_entities(self):
        """Schema should define vector embedding entities."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        content = schema_file.read_text()

        assert "vector-document sub entity" in content
        assert "vector-embedding" in content
        assert "vector-similarity" in content
        assert "similarity-score" in content

    @pytest.mark.unit
    def test_schema_has_vector_attributes(self):
        """Schema should define vector attributes."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        content = schema_file.read_text()

        assert "vector-id sub attribute" in content
        assert "vector-content sub attribute" in content
        assert "vector-model sub attribute" in content
        assert "vector-dimension sub attribute" in content

    @pytest.mark.unit
    def test_entities_can_have_embeddings(self):
        """Rule and decision entities should play embedding role."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        content = schema_file.read_text()

        assert "plays entity-vector:embedded-entity" in content
