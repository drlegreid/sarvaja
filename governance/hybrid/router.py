"""
Hybrid Query Router
===================
Routes queries between TypeDB (inference) and ChromaDB (semantic).

Per RULE-004: Executable Spec
Per RULE-010: Evidence-Based Wisdom
Per GAP-FILE-012: Extracted from hybrid_router.py

Created: 2024-12-28
"""

import os
import re
import time
from typing import Dict, Any, Optional, Literal
from dataclasses import asdict

from .models import QueryType, QueryResult

# Import TypeDB client
try:
    from governance.client import TypeDBClient, quick_health
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from governance.client import TypeDBClient, quick_health


class HybridQueryRouter:
    """
    Routes queries between TypeDB (inference) and ChromaDB (semantic).

    Routing Strategy:
    1. Check query type keywords
    2. Route to appropriate backend
    3. On TypeDB timeout, fallback to ChromaDB
    4. Merge results for combined queries
    """

    # Keywords indicating inference query (TypeDB)
    INFERENCE_KEYWORDS = [
        "depends on", "dependency", "dependencies",
        "conflicts", "conflicting",
        "supersedes", "superseded",
        "affects", "impacted by",
        "related to", "relationship",
        "transitive", "chain"
    ]

    # Keywords indicating semantic query (ChromaDB)
    SEMANTIC_KEYWORDS = [
        "about", "related to", "similar",
        "like", "meaning", "describes",
        "find", "search", "lookup",
        "what is", "explain", "describe"
    ]

    def __init__(
        self,
        typedb_host: str = None,
        typedb_port: int = None,
        chromadb_host: str = None,
        chromadb_port: int = None,
        timeout_ms: int = 5000
    ):
        self.typedb_host = typedb_host or os.getenv("TYPEDB_HOST", "localhost")
        self.typedb_port = typedb_port or int(os.getenv("TYPEDB_PORT", "1729"))
        self.chromadb_host = chromadb_host or os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = chromadb_port or int(os.getenv("CHROMADB_PORT", "8001"))
        self.timeout_ms = timeout_ms

        self._typedb_client: Optional[TypeDBClient] = None
        self._chromadb_client = None  # Will be chromadb.HttpClient

    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================

    def connect(self) -> Dict[str, bool]:
        """Connect to both backends."""
        status = {"typedb": False, "chromadb": False}

        # TypeDB
        try:
            self._typedb_client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port
            )
            status["typedb"] = self._typedb_client.connect()
        except Exception as e:
            print(f"[HybridRouter] TypeDB connection failed: {e}")

        # ChromaDB
        try:
            import chromadb
            self._chromadb_client = chromadb.HttpClient(
                host=self.chromadb_host,
                port=self.chromadb_port
            )
            # Test connection
            self._chromadb_client.heartbeat()
            status["chromadb"] = True
        except Exception as e:
            print(f"[HybridRouter] ChromaDB connection failed: {e}")

        return status

    def close(self):
        """Close all connections."""
        if self._typedb_client:
            self._typedb_client.close()

    def health_check(self) -> Dict[str, Any]:
        """Check health of both backends."""
        return {
            "typedb": {
                "reachable": quick_health(),
                "connected": self._typedb_client.is_connected() if self._typedb_client else False
            },
            "chromadb": {
                "reachable": self._check_chromadb_health(),
                "connected": self._chromadb_client is not None
            }
        }

    def _check_chromadb_health(self) -> bool:
        """Check ChromaDB health."""
        try:
            if self._chromadb_client:
                self._chromadb_client.heartbeat()
                return True
        except:
            pass
        return False

    # =========================================================================
    # QUERY ROUTING
    # =========================================================================

    def query(
        self,
        query_text: str,
        query_type: Literal["inference", "semantic", "combined", "auto"] = "auto",
        collection: str = "claude_memories",
        n_results: int = 10
    ) -> QueryResult:
        """
        Execute query with automatic routing.

        Args:
            query_text: Natural language query
            query_type: "inference", "semantic", "combined", or "auto"
            collection: ChromaDB collection for semantic queries
            n_results: Max results for semantic queries

        Returns:
            QueryResult with unified results from appropriate backend(s)
        """
        start_time = time.time()

        # Detect query type if auto
        if query_type == "auto":
            query_type = self._detect_query_type(query_text)

        try:
            if query_type == "inference":
                return self._query_typedb(query_text, start_time)
            elif query_type == "semantic":
                return self._query_chromadb(query_text, collection, n_results, start_time)
            elif query_type == "combined":
                return self._query_combined(query_text, collection, n_results, start_time)
            else:
                # Default to semantic
                return self._query_chromadb(query_text, collection, n_results, start_time)

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return QueryResult(
                query=query_text,
                query_type=QueryType(query_type),
                source="error",
                results=[],
                count=0,
                latency_ms=latency,
                error=str(e)
            )

    def _detect_query_type(self, query_text: str) -> str:
        """Detect query type from keywords."""
        query_lower = query_text.lower()

        # Check for inference keywords
        inference_score = sum(
            1 for kw in self.INFERENCE_KEYWORDS
            if kw in query_lower
        )

        # Check for semantic keywords
        semantic_score = sum(
            1 for kw in self.SEMANTIC_KEYWORDS
            if kw in query_lower
        )

        # Check for specific patterns
        if "RULE-" in query_text or "DECISION-" in query_text:
            inference_score += 2  # Likely wants typed entity

        if "?" in query_text and ("what" in query_lower or "how" in query_lower):
            semantic_score += 1  # Likely natural language

        # Decide
        if inference_score > semantic_score:
            return "inference"
        elif semantic_score > inference_score:
            return "semantic"
        else:
            return "semantic"  # Default to semantic

    # =========================================================================
    # BACKEND QUERIES
    # =========================================================================

    def _query_typedb(
        self,
        query_text: str,
        start_time: float
    ) -> QueryResult:
        """Execute inference query on TypeDB."""
        if not self._typedb_client or not self._typedb_client.is_connected():
            # Fallback to ChromaDB
            return self._query_chromadb_fallback(query_text, start_time)

        try:
            results = []

            # Parse query for specific patterns
            if "depends on" in query_text.lower():
                # Extract rule ID
                rule_id = self._extract_rule_id(query_text)
                if rule_id:
                    deps = self._typedb_client.get_rule_dependencies(rule_id)
                    results = [{"type": "dependency", "rule_id": d} for d in deps]

            elif "conflicts" in query_text.lower():
                conflicts = self._typedb_client.find_conflicts()
                results = [{"type": "conflict", **c} for c in conflicts]

            elif "RULE-" in query_text:
                rule_id = self._extract_rule_id(query_text)
                if rule_id:
                    rule = self._typedb_client.get_rule_by_id(rule_id)
                    if rule:
                        results = [asdict(rule)]

            else:
                # Get all rules and filter
                all_rules = self._typedb_client.get_all_rules()
                query_lower = query_text.lower()
                results = [
                    asdict(r) for r in all_rules
                    if query_lower in r.name.lower() or query_lower in r.directive.lower()
                ]

            latency = (time.time() - start_time) * 1000
            return QueryResult(
                query=query_text,
                query_type=QueryType.INFERENCE,
                source="typedb",
                results=results,
                count=len(results),
                latency_ms=latency
            )

        except Exception as e:
            # Fallback to ChromaDB on error
            return self._query_chromadb_fallback(query_text, start_time, error=str(e))

    def _query_chromadb(
        self,
        query_text: str,
        collection: str,
        n_results: int,
        start_time: float
    ) -> QueryResult:
        """Execute semantic query on ChromaDB."""
        if not self._chromadb_client:
            latency = (time.time() - start_time) * 1000
            return QueryResult(
                query=query_text,
                query_type=QueryType.SEMANTIC,
                source="chromadb",
                results=[],
                count=0,
                latency_ms=latency,
                error="ChromaDB not connected"
            )

        try:
            # Get collection
            coll = self._chromadb_client.get_collection(collection)

            # Query
            response = coll.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            results = []
            if response["documents"]:
                for i, doc in enumerate(response["documents"][0]):
                    result = {
                        "document": doc,
                        "distance": response["distances"][0][i] if response["distances"] else None
                    }
                    if response["metadatas"] and response["metadatas"][0]:
                        result["metadata"] = response["metadatas"][0][i]
                    results.append(result)

            latency = (time.time() - start_time) * 1000
            return QueryResult(
                query=query_text,
                query_type=QueryType.SEMANTIC,
                source="chromadb",
                results=results,
                count=len(results),
                latency_ms=latency
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return QueryResult(
                query=query_text,
                query_type=QueryType.SEMANTIC,
                source="chromadb",
                results=[],
                count=0,
                latency_ms=latency,
                error=str(e)
            )

    def _query_combined(
        self,
        query_text: str,
        collection: str,
        n_results: int,
        start_time: float
    ) -> QueryResult:
        """Execute query on both backends and merge results."""
        typedb_result = self._query_typedb(query_text, start_time)
        chromadb_result = self._query_chromadb(
            query_text, collection, n_results, start_time
        )

        # Merge results
        merged = {
            "typedb": typedb_result.results,
            "chromadb": chromadb_result.results
        }

        latency = (time.time() - start_time) * 1000
        return QueryResult(
            query=query_text,
            query_type=QueryType.COMBINED,
            source="both",
            results=[merged],
            count=typedb_result.count + chromadb_result.count,
            latency_ms=latency,
            error=typedb_result.error or chromadb_result.error
        )

    def _query_chromadb_fallback(
        self,
        query_text: str,
        start_time: float,
        error: str = None
    ) -> QueryResult:
        """Fallback to ChromaDB when TypeDB fails."""
        result = self._query_chromadb(
            query_text,
            collection="claude_memories",
            n_results=10,
            start_time=start_time
        )
        result.fallback_used = True
        if error:
            result.error = f"TypeDB error: {error}. Fell back to ChromaDB."
        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _extract_rule_id(self, text: str) -> Optional[str]:
        """Extract RULE-XXX from text."""
        match = re.search(r'RULE-\d{3}', text)
        return match.group(0) if match else None

    def _extract_decision_id(self, text: str) -> Optional[str]:
        """Extract DECISION-XXX from text."""
        match = re.search(r'DECISION-\d{3}', text)
        return match.group(0) if match else None


__all__ = [
    "HybridQueryRouter",
]
