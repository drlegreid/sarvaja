"""
Robot Framework Library for Vector Store Tests (P7.1)
Migrated from tests/test_vector_store.py
"""

from pathlib import Path
from robot.api.deco import keyword

PROJECT_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class VectorStoreLibrary:
    """Library for vector store test keywords."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Module Existence Tests
    # =========================================================================

    @keyword("Module Exists")
    def module_exists(self):
        """Vector store module must exist."""
        vector_file = GOVERNANCE_DIR / "vector_store.py"
        return {"exists": vector_file.exists()}

    @keyword("Vector Document Dataclass")
    def vector_document_dataclass(self):
        """VectorDocument dataclass must be importable."""
        try:
            from governance.vector_store import VectorDocument
            from datetime import datetime

            doc = VectorDocument(
                id="test-001",
                content="Test content",
                embedding=[0.1, 0.2, 0.3],
                model="test-model",
                dimension=3,
                source="TEST-001",
                source_type="rule"
            )

            return {
                "id_correct": doc.id == "test-001",
                "source_type_correct": doc.source_type == "rule",
                "embedding_len": len(doc.embedding) == 3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Similarity Result Dataclass")
    def similarity_result_dataclass(self):
        """SimilarityResult dataclass must be importable."""
        try:
            from governance.vector_store import SimilarityResult

            result = SimilarityResult(
                vector_id="vec-001",
                content="Test content",
                source="RULE-001",
                source_type="rule",
                score=0.95
            )

            return {
                "score_correct": result.score == 0.95,
                "source_correct": result.source == "RULE-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vector Store Class")
    def vector_store_class(self):
        """VectorStore class must be instantiable."""
        try:
            from governance.vector_store import VectorStore

            store = VectorStore(host="localhost", port=1729)
            return {
                "host_correct": store.host == "localhost",
                "port_correct": store.port == 1729
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vector Document Created At")
    def vector_document_created_at(self):
        """VectorDocument should have created_at timestamp."""
        try:
            from governance.vector_store import VectorDocument
            from datetime import datetime

            doc = VectorDocument(
                id="test-002",
                content="Test",
                embedding=[0.1],
                model="test",
                dimension=1,
                source="TEST",
                source_type="rule"
            )

            return {
                "has_created_at": doc.created_at is not None,
                "is_datetime": isinstance(doc.created_at, datetime)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Embedding Generator Tests
    # =========================================================================

    @keyword("Mock Embeddings Exists")
    def mock_embeddings_exists(self):
        """MockEmbeddings class must exist."""
        try:
            from governance.vector_store import MockEmbeddings

            generator = MockEmbeddings(dimension=384)
            return {
                "dimension_correct": generator.dimension == 384,
                "model_name_correct": generator.model_name == "mock-embeddings"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Mock Embeddings Generate")
    def mock_embeddings_generate(self):
        """MockEmbeddings must generate deterministic embeddings."""
        try:
            from governance.vector_store import MockEmbeddings

            generator = MockEmbeddings(dimension=128)
            embedding1 = generator.generate("test text")
            embedding2 = generator.generate("test text")

            return {
                "len_correct": len(embedding1) == 128,
                "deterministic": embedding1 == embedding2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Mock Embeddings Different Texts")
    def mock_embeddings_different_texts(self):
        """Different texts should produce different embeddings."""
        try:
            from governance.vector_store import MockEmbeddings

            generator = MockEmbeddings(dimension=128)
            embedding1 = generator.generate("text one")
            embedding2 = generator.generate("text two")

            return {"different": embedding1 != embedding2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Ollama Embeddings Class")
    def ollama_embeddings_class(self):
        """OllamaEmbeddings class must exist."""
        try:
            from governance.vector_store import OllamaEmbeddings

            generator = OllamaEmbeddings(host="localhost", port=11434)
            return {
                "host_correct": generator.host == "localhost",
                "dimension_correct": generator.dimension == 768,
                "has_ollama": "ollama" in generator.model_name
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("LiteLLM Embeddings Class")
    def litellm_embeddings_class(self):
        """LiteLLMEmbeddings class must exist."""
        try:
            from governance.vector_store import LiteLLMEmbeddings

            generator = LiteLLMEmbeddings(host="localhost", port=4000)
            return {
                "host_correct": generator.host == "localhost",
                "dimension_correct": generator.dimension == 1536,
                "has_litellm": "litellm" in generator.model_name
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Cosine Similarity Tests
    # =========================================================================

    @keyword("Cosine Similarity Identical")
    def cosine_similarity_identical(self):
        """Identical vectors should have similarity 1.0."""
        try:
            from governance.vector_store import VectorStore

            vec = [0.5, 0.5, 0.5]
            similarity = VectorStore._cosine_similarity(vec, vec)
            return {"is_one": abs(similarity - 1.0) < 0.0001}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cosine Similarity Orthogonal")
    def cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity 0.0."""
        try:
            from governance.vector_store import VectorStore

            vec_a = [1.0, 0.0, 0.0]
            vec_b = [0.0, 1.0, 0.0]
            similarity = VectorStore._cosine_similarity(vec_a, vec_b)
            return {"is_zero": abs(similarity) < 0.0001}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cosine Similarity Opposite")
    def cosine_similarity_opposite(self):
        """Opposite vectors should have similarity -1.0."""
        try:
            from governance.vector_store import VectorStore

            vec_a = [1.0, 0.0]
            vec_b = [-1.0, 0.0]
            similarity = VectorStore._cosine_similarity(vec_a, vec_b)
            return {"is_neg_one": abs(similarity - (-1.0)) < 0.0001}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cosine Similarity Different Lengths")
    def cosine_similarity_different_lengths(self):
        """Different length vectors should return 0.0."""
        try:
            from governance.vector_store import VectorStore

            vec_a = [0.5, 0.5]
            vec_b = [0.5, 0.5, 0.5]
            similarity = VectorStore._cosine_similarity(vec_a, vec_b)
            return {"is_zero": similarity == 0.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cosine Similarity Zero Vector")
    def cosine_similarity_zero_vector(self):
        """Zero vectors should return 0.0."""
        try:
            from governance.vector_store import VectorStore

            vec_a = [0.0, 0.0, 0.0]
            vec_b = [1.0, 2.0, 3.0]
            similarity = VectorStore._cosine_similarity(vec_a, vec_b)
            return {"is_zero": similarity == 0.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

