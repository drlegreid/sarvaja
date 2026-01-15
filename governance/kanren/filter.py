"""
KanrenRAGFilter - RAG Integration with Kanren Validation (KAN-003).

Per KAN-003: Validate ChromaDB/VectorStore chunks before LLM context.
"""

from typing import Any, Dict, List, Optional

from .models import AgentContext, TaskContext
from .rag import filter_rag_chunks
from .assembly import assemble_context


class KanrenRAGFilter:
    """
    RAG retrieval with Kanren constraint validation.

    Per KAN-003: Validate ChromaDB/VectorStore chunks before LLM context.
    Ensures only governance-approved data enters the prompt.

    Example:
        from governance.kanren import KanrenRAGFilter

        rag_filter = KanrenRAGFilter()
        results = rag_filter.search_validated(
            query_embedding=[0.1, 0.2, ...],
            top_k=10
        )
        # Only returns chunks passing Kanren validation
    """

    def __init__(self, vector_store=None):
        """
        Initialize RAG filter.

        Args:
            vector_store: VectorStore instance (default: creates new one)
        """
        self._store = vector_store

    def _get_store(self):
        """Lazy load VectorStore."""
        if self._store is None:
            from governance.vector_store import VectorStore
            self._store = VectorStore()
            self._store.connect()
        return self._store

    def search_validated(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        source_type: Optional[str] = None,
        threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar vectors with Kanren validation.

        Retrieves chunks from VectorStore and filters through Kanren
        constraints before returning.

        Args:
            query_embedding: Query vector
            top_k: Maximum results before filtering
            source_type: Filter by source type (rule, decision, session)
            threshold: Minimum similarity score

        Returns:
            List of validated chunks with metadata
        """
        store = self._get_store()
        results = store.search(query_embedding, top_k, source_type, threshold)

        # Convert to chunk format for Kanren validation
        chunks = self._results_to_chunks(results)

        # Apply Kanren constraints
        validated = filter_rag_chunks(chunks)

        return validated

    def _results_to_chunks(self, results) -> List[Dict]:
        """
        Convert SimilarityResult list to chunk format for Kanren.

        Maps VectorStore fields to Kanren validation fields:
        - source_type -> source (typedb, chromadb, etc.)
        - source_type -> type (rule, evidence, etc.)
        - score > threshold -> verified
        """
        chunks = []
        for r in results:
            # Map source_type to Kanren source categories
            source_map = {
                "rule": "typedb",
                "decision": "typedb",
                "session": "chromadb",
                "document": "typedb"
            }
            chunk = {
                "id": r.vector_id,
                "content": r.content,
                "source": source_map.get(r.source_type, "typedb"),
                "type": r.source_type,
                "verified": r.score > 0.5,  # High similarity = verified
                "score": r.score,
                "original_source": r.source
            }
            chunks.append(chunk)
        return chunks

    def search_for_task(
        self,
        query_text: str,
        task_context: TaskContext,
        agent_context: AgentContext,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Full context assembly for a task with validation.

        Combines:
        1. RAG retrieval with Kanren validation
        2. Agent trust validation
        3. Task evidence requirements

        Args:
            query_text: Natural language query
            task_context: Task being executed
            agent_context: Agent executing the task
            top_k: Maximum chunks to retrieve

        Returns:
            Full validated context dictionary
        """
        # For now, return a mock embedding search
        # In production, this would use the embedding generator
        store = self._get_store()

        # Get all vectors of relevant types
        all_vectors = store.get_all_vectors()

        # Simple text matching for PoC (production would use embeddings)
        chunks = []
        query_lower = query_text.lower()
        for vec in all_vectors:
            if query_lower in vec.content.lower():
                chunks.append({
                    "id": vec.id,
                    "content": vec.content,
                    "source": "typedb" if vec.source_type in ("rule", "decision") else "chromadb",
                    "type": vec.source_type,
                    "verified": True,
                    "score": 0.8,
                    "original_source": vec.source
                })

        # Filter through Kanren
        validated_chunks = filter_rag_chunks(chunks[:top_k])

        # Assemble full context
        return assemble_context(agent_context, task_context, validated_chunks)
