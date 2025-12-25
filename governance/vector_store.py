"""
TypeDB Vector Store Bridge (P7.1)
Created: 2024-12-25

PURPOSE:
Bridge layer for vector embeddings in TypeDB 2.x (which lacks native vector support).
Stores embeddings as JSON strings and performs similarity computation in Python.

MIGRATION PATH:
When TypeDB 3.x is stable, this module will be refactored to use native vector types:
- vector-embedding: string → double[]
- similarity queries: Python → TypeQL `near` operator

See DECISION-003: TypeDB-First Strategy for full migration plan.

Per RULE-010: Evidence-Based Wisdom - measure before optimize.
"""
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class VectorDocument:
    """Vector document entity for TypeDB storage."""
    id: str
    content: str
    embedding: List[float]
    model: str
    dimension: int
    source: str
    source_type: str  # rule, decision, session, document
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_typedb_insert(self) -> str:
        """Generate TypeQL insert statement."""
        embedding_json = json.dumps(self.embedding)
        created_at = self.created_at.isoformat() if self.created_at else datetime.now().isoformat()

        return f"""
            insert $v isa vector-document,
                has vector-id "{self.id}",
                has vector-content "{self._escape(self.content)}",
                has vector-embedding "{self._escape(embedding_json)}",
                has vector-model "{self.model}",
                has vector-dimension {self.dimension},
                has vector-source "{self.source}",
                has vector-source-type "{self.source_type}",
                has vector-created-at {created_at};
        """

    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for TypeQL string literals."""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


@dataclass
class SimilarityResult:
    """Result from similarity search."""
    vector_id: str
    content: str
    source: str
    source_type: str
    score: float


class VectorStore:
    """
    Vector store backed by TypeDB with Python similarity computation.

    Example:
        store = VectorStore()
        store.connect()

        # Add embedding
        doc = VectorDocument(
            id=str(uuid.uuid4()),
            content="RULE-001 requires session evidence",
            embedding=[0.1, 0.2, ...],
            model="text-embedding-3-small",
            dimension=1536,
            source="RULE-001",
            source_type="rule"
        )
        store.insert(doc)

        # Search similar
        results = store.search([0.1, 0.2, ...], top_k=5)
    """

    def __init__(self, host: str = "localhost", port: int = 1729, database: str = "sim-ai-governance"):
        self.host = host
        self.port = port
        self.database = database
        self._client = None
        self._connected = False
        self._cache: Dict[str, VectorDocument] = {}

    def connect(self) -> bool:
        """Connect to TypeDB."""
        try:
            from typedb.driver import TypeDB
            address = f"{self.host}:{self.port}"
            self._client = TypeDB.core_driver(address)
            self._connected = True
            return True
        except ImportError:
            print("TypeDB driver not installed. Run: pip install typedb-driver==2.29.2")
            return False
        except Exception as e:
            print(f"Failed to connect to TypeDB: {e}")
            return False

    def close(self):
        """Close connection."""
        if self._client:
            self._client.close()
            self._connected = False

    def insert(self, doc: VectorDocument) -> bool:
        """Insert vector document into TypeDB."""
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    tx.query.insert(doc.to_typedb_insert())
                    tx.commit()

            # Cache for similarity search
            self._cache[doc.id] = doc
            return True
        except Exception as e:
            print(f"Insert failed: {e}")
            return False

    def insert_batch(self, docs: List[VectorDocument]) -> int:
        """Insert multiple documents. Returns count of successful inserts."""
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType

        success_count = 0
        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                for doc in docs:
                    try:
                        tx.query.insert(doc.to_typedb_insert())
                        self._cache[doc.id] = doc
                        success_count += 1
                    except Exception as e:
                        print(f"Failed to insert {doc.id}: {e}")
                tx.commit()

        return success_count

    def get_all_vectors(self) -> List[VectorDocument]:
        """Retrieve all vector documents from TypeDB."""
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType

        query = """
            match $v isa vector-document,
                has vector-id $id,
                has vector-content $content,
                has vector-embedding $embedding,
                has vector-model $model,
                has vector-dimension $dimension,
                has vector-source $source,
                has vector-source-type $source_type;
            get $id, $content, $embedding, $model, $dimension, $source, $source_type;
        """

        results = []
        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as tx:
                for result in tx.query.get(query):
                    try:
                        embedding_json = result.get("embedding").as_attribute().get_value()
                        embedding = json.loads(embedding_json)

                        doc = VectorDocument(
                            id=result.get("id").as_attribute().get_value(),
                            content=result.get("content").as_attribute().get_value(),
                            embedding=embedding,
                            model=result.get("model").as_attribute().get_value(),
                            dimension=result.get("dimension").as_attribute().get_value(),
                            source=result.get("source").as_attribute().get_value(),
                            source_type=result.get("source_type").as_attribute().get_value()
                        )
                        results.append(doc)
                        self._cache[doc.id] = doc
                    except Exception as e:
                        print(f"Failed to parse vector: {e}")

        return results

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_type: Optional[str] = None,
        threshold: float = 0.0
    ) -> List[SimilarityResult]:
        """
        Search for similar vectors using cosine similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            source_type: Filter by source type (rule, decision, session)
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of SimilarityResult ordered by score descending
        """
        # Load vectors from TypeDB if cache is empty
        if not self._cache:
            self.get_all_vectors()

        # Compute similarities
        similarities: List[Tuple[str, float]] = []
        for doc_id, doc in self._cache.items():
            if source_type and doc.source_type != source_type:
                continue

            score = self._cosine_similarity(query_embedding, doc.embedding)
            if score >= threshold:
                similarities.append((doc_id, score))

        # Sort by score descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k results
        results = []
        for doc_id, score in similarities[:top_k]:
            doc = self._cache[doc_id]
            results.append(SimilarityResult(
                vector_id=doc_id,
                content=doc.content,
                source=doc.source,
                source_type=doc.source_type,
                score=score
            ))

        return results

    def search_by_source(self, source_id: str) -> Optional[VectorDocument]:
        """Find vector document by source ID."""
        if not self._cache:
            self.get_all_vectors()

        for doc in self._cache.values():
            if doc.source == source_id:
                return doc
        return None

    def delete_by_source(self, source_id: str) -> bool:
        """Delete vector document by source ID."""
        if not self._connected:
            raise RuntimeError("Not connected to TypeDB")

        from typedb.driver import SessionType, TransactionType

        query = f"""
            match $v isa vector-document, has vector-source "{source_id}";
            delete $v isa vector-document;
        """

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    tx.query.delete(query)
                    tx.commit()

            # Remove from cache
            to_remove = [k for k, v in self._cache.items() if v.source == source_id]
            for k in to_remove:
                del self._cache[k]

            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# =============================================================================
# EMBEDDING GENERATORS
# =============================================================================

class EmbeddingGenerator:
    """
    Abstract embedding generator interface.

    Implementations:
    - OpenAIEmbeddings: text-embedding-3-small (1536 dims)
    - OllamaEmbeddings: nomic-embed-text (768 dims)
    - MockEmbeddings: for testing
    """

    def generate(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.generate(text) for text in texts]

    @property
    def model_name(self) -> str:
        """Return model name."""
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        raise NotImplementedError


class MockEmbeddings(EmbeddingGenerator):
    """Mock embeddings for testing."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def generate(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        import hashlib
        # Create deterministic embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to floats in range [-1, 1]
        embedding = []
        for i in range(self._dimension):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] - 128) / 128.0
            embedding.append(value)
        return embedding

    @property
    def model_name(self) -> str:
        return "mock-embeddings"

    @property
    def dimension(self) -> int:
        return self._dimension


class OllamaEmbeddings(EmbeddingGenerator):
    """Ollama embeddings using nomic-embed-text model."""

    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "nomic-embed-text"):
        self.host = host
        self.port = port
        self.model = model
        self._dimension = 768  # nomic-embed-text dimension

    def generate(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        import httpx

        url = f"http://{self.host}:{self.port}/api/embeddings"
        response = httpx.post(url, json={"model": self.model, "prompt": text}, timeout=30)
        response.raise_for_status()
        return response.json()["embedding"]

    @property
    def model_name(self) -> str:
        return f"ollama/{self.model}"

    @property
    def dimension(self) -> int:
        return self._dimension


class LiteLLMEmbeddings(EmbeddingGenerator):
    """LiteLLM embeddings using configured model."""

    def __init__(self, host: str = "localhost", port: int = 4000, model: str = "text-embedding-3-small"):
        self.host = host
        self.port = port
        self.model = model
        self._dimension = 1536  # OpenAI default

    def generate(self, text: str) -> List[float]:
        """Generate embedding using LiteLLM proxy."""
        import httpx

        url = f"http://{self.host}:{self.port}/embeddings"
        response = httpx.post(
            url,
            json={"model": self.model, "input": text},
            headers={"Authorization": "Bearer sk-litellm-master-key-change-me"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    @property
    def model_name(self) -> str:
        return f"litellm/{self.model}"

    @property
    def dimension(self) -> int:
        return self._dimension


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_vector_from_rule(rule_id: str, rule_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a governance rule."""
    embedding = generator.generate(rule_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=rule_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=rule_id,
        source_type="rule"
    )


def create_vector_from_decision(decision_id: str, decision_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a strategic decision."""
    embedding = generator.generate(decision_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=decision_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=decision_id,
        source_type="decision"
    )


def create_vector_from_session(session_id: str, session_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a session evidence file."""
    embedding = generator.generate(session_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=session_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=session_id,
        source_type="session"
    )


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TypeDB Vector Store Test (P7.1)")
    print("=" * 60)

    # Test with mock embeddings
    generator = MockEmbeddings(dimension=384)
    print(f"\nUsing: {generator.model_name} ({generator.dimension} dims)")

    # Create test vectors
    docs = [
        create_vector_from_rule(
            "RULE-001",
            "Session Evidence Logging: All sessions must produce evidence artifacts",
            generator
        ),
        create_vector_from_rule(
            "RULE-011",
            "Multi-Agent Governance: Trust-weighted voting for rule changes",
            generator
        ),
        create_vector_from_decision(
            "DECISION-003",
            "TypeDB-First Strategy: Unify semantic and logical queries",
            generator
        ),
    ]

    print(f"\nCreated {len(docs)} test vectors")

    # Test similarity search (without TypeDB connection)
    store = VectorStore()
    store._cache = {doc.id: doc for doc in docs}

    query = generator.generate("evidence and logging requirements")
    results = store.search(query, top_k=3)

    print("\n--- Similarity Search Results ---")
    for r in results:
        print(f"  [{r.score:.4f}] {r.source}: {r.content[:50]}...")

    print("\n[OK] Vector store test complete!")
