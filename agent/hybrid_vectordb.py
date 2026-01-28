"""
HybridVectorDb - Vector DB adapter for Agent hybrid knowledge layer.
Per RULE-004: TDD Implementation

This adapter wraps the HybridQueryRouter to provide a unified search interface
that routes queries to TypeDB (inference) or ChromaDB (semantic) based on
query content analysis.
"""

from typing import List, Dict, Any, Optional
import os
import logging

# Import the hybrid router from governance module
from governance.hybrid_router import HybridQueryRouter, QueryResult

logger = logging.getLogger(__name__)


class HybridVectorDb:
    """
    Vector database adapter that routes queries between TypeDB and ChromaDB.

    Inference queries (dependencies, conflicts, rules) → TypeDB
    Semantic queries (search, find, about) → ChromaDB

    Implements fallback: if TypeDB fails, falls back to ChromaDB.

    Usage:
        db = HybridVectorDb()
        results = db.search("What depends on RULE-001?")  # → TypeDB
        results = db.search("Tell me about authentication")  # → ChromaDB
    """

    def __init__(
        self,
        typedb_host: Optional[str] = None,
        typedb_port: Optional[int] = None,
        chromadb_host: Optional[str] = None,
        chromadb_port: Optional[int] = None,
        collection_name: str = "sim_ai_knowledge",
        auto_connect: bool = False
    ):
        """
        Initialize HybridVectorDb with optional connection parameters.

        Args:
            typedb_host: TypeDB host (default from TYPEDB_HOST env)
            typedb_port: TypeDB port (default from TYPEDB_PORT env)
            chromadb_host: ChromaDB host (default from CHROMADB_HOST env)
            chromadb_port: ChromaDB port (default from CHROMADB_PORT env)
            collection_name: Default ChromaDB collection
            auto_connect: Attempt to connect on init
        """
        self.collection_name = collection_name

        # Initialize the hybrid router
        self._router = HybridQueryRouter(
            typedb_host=typedb_host or os.getenv("TYPEDB_HOST", "localhost"),
            typedb_port=typedb_port or int(os.getenv("TYPEDB_PORT", "1729")),
            chromadb_host=chromadb_host or os.getenv("CHROMADB_HOST", "localhost"),
            chromadb_port=chromadb_port or int(os.getenv("CHROMADB_PORT", "8001"))
        )

        if auto_connect:
            self.connect()

    def connect(self) -> Dict[str, bool]:
        """
        Connect to both TypeDB and ChromaDB.

        Returns:
            Dict with connection status for each backend
        """
        return self._router.connect()

    def close(self) -> None:
        """Close connections to both backends."""
        self._router.close()

    def search(
        self,
        query: str,
        n_results: int = 10,
        query_type: Optional[str] = None,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using hybrid query routing.

        Automatically detects query type and routes to appropriate backend:
        - Inference queries → TypeDB
        - Semantic queries → ChromaDB

        Args:
            query: Search query text
            n_results: Maximum results to return
            query_type: Force query type ("inference" or "semantic")
            collection: ChromaDB collection (default: self.collection_name)

        Returns:
            List of result documents with metadata
        """
        try:
            # Detect query type if not specified
            detected_type = query_type or self._router._detect_query_type(query)

            # Route to appropriate backend
            if detected_type == "inference":
                return self._route_to_typedb(query, n_results, collection)
            else:
                return self._query_chromadb(query, n_results, collection)

        except Exception as e:
            logger.error(f"Search error: {e}")
            # Return empty results on error
            return []

    def _route_to_typedb(
        self,
        query: str,
        n_results: int = 10,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Route inference query to TypeDB with ChromaDB fallback.

        Args:
            query: Query text
            n_results: Maximum results
            collection: Fallback collection

        Returns:
            List of result documents
        """
        try:
            return self._query_typedb(query, n_results)
        except Exception as e:
            logger.warning(f"TypeDB query failed: {e}, falling back to ChromaDB")
            return self._query_chromadb(query, n_results, collection)

    def _query_typedb(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Execute inference query against TypeDB.

        Args:
            query: Query text
            n_results: Maximum results

        Returns:
            List of result documents
        """
        result = self._router.query(
            query_text=query,
            query_type="inference",
            n_results=n_results
        )
        return self._format_results(result)

    def _query_chromadb(
        self,
        query: str,
        n_results: int = 10,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic query against ChromaDB.

        Args:
            query: Query text
            n_results: Maximum results
            collection: Collection name

        Returns:
            List of result documents
        """
        result = self._router.query(
            query_text=query,
            query_type="semantic",
            n_results=n_results,
            collection=collection or self.collection_name
        )
        return self._format_results(result)

    def _format_results(self, result: QueryResult) -> List[Dict[str, Any]]:
        """
        Format QueryResult into list of document dicts.

        Args:
            result: QueryResult from router

        Returns:
            List of formatted documents
        """
        if not result or not result.results:
            return []

        formatted = []
        for item in result.results:
            if isinstance(item, dict):
                formatted.append(item)
            else:
                # Wrap non-dict results
                formatted.append({"content": str(item)})

        return formatted

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of both backends.

        Returns:
            Health status for TypeDB and ChromaDB
        """
        return self._router.health_check()

    def get_query_type(self, query: str) -> str:
        """
        Detect query type without executing.

        Args:
            query: Query text

        Returns:
            "inference" or "semantic"
        """
        return self._router._detect_query_type(query)

    # Agno VectorDb compatibility methods

    def add(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """
        Add documents to ChromaDB collection.

        Note: TypeDB entities should be managed via governance module.

        Args:
            documents: List of document texts
            ids: Optional document IDs
            metadatas: Optional metadata dicts
        """
        if not self._router._chromadb_client:
            logger.warning("ChromaDB not connected, cannot add documents")
            return

        try:
            collection = self._router._chromadb_client.get_or_create_collection(
                name=self.collection_name
            )

            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]

            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")

    def delete(self, ids: List[str]) -> None:
        """
        Delete documents from ChromaDB collection.

        Args:
            ids: List of document IDs to delete
        """
        if not self._router._chromadb_client:
            logger.warning("ChromaDB not connected, cannot delete documents")
            return

        try:
            collection = self._router._chromadb_client.get_collection(
                name=self.collection_name
            )
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")


# Factory function for creating HybridVectorDb instances
def create_hybrid_vectordb(
    collection: str = "sim_ai_knowledge",
    auto_connect: bool = False
) -> HybridVectorDb:
    """
    Factory function to create HybridVectorDb instance.

    Args:
        collection: ChromaDB collection name
        auto_connect: Attempt to connect on creation

    Returns:
        Configured HybridVectorDb instance
    """
    return HybridVectorDb(
        collection_name=collection,
        auto_connect=auto_connect
    )
