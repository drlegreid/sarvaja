"""
Vector Store Implementation.

Per RULE-032: Modularized from vector_store.py (531 lines).
Contains: VectorStore class for TypeDB vector storage with Python similarity.
"""

import json
from typing import List, Dict, Optional, Tuple

from .models import VectorDocument, SimilarityResult


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
