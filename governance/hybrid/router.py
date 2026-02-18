"""Hybrid Query Router: TypeDB (inference) + ChromaDB (semantic). Per RULE-004, RULE-010."""

import logging
import os
import re
import time
from typing import Dict, Any, Optional, Literal
from dataclasses import asdict

logger = logging.getLogger(__name__)

from .models import QueryType, QueryResult

# Import TypeDB client
try:
    from governance.client import TypeDBClient, quick_health
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from governance.client import TypeDBClient, quick_health

class HybridQueryRouter:
    """Routes queries to TypeDB (inference) or ChromaDB (semantic) with auto-detection and fallback."""

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

    def __init__(self, typedb_host: str = None, typedb_port: int = None,
                 chromadb_host: str = None, chromadb_port: int = None, timeout_ms: int = 5000):
        self.typedb_host = typedb_host or os.getenv("TYPEDB_HOST", "localhost")
        self.typedb_port = typedb_port or int(os.getenv("TYPEDB_PORT", "1729"))
        self.chromadb_host = chromadb_host or os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = chromadb_port or int(os.getenv("CHROMADB_PORT", "8001"))
        self.timeout_ms = timeout_ms

        self._typedb_client: Optional[TypeDBClient] = None
        self._chromadb_client = None

    def connect(self) -> Dict[str, bool]:
        """Connect to both backends."""
        status = {"typedb": False, "chromadb": False}
        try:
            self._typedb_client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port
            )
            status["typedb"] = self._typedb_client.connect()
        except Exception as e:
            # BUG-474-HYB-1: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"TypeDB connection failed: {type(e).__name__}", exc_info=True)

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
            # BUG-474-HYB-2: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"ChromaDB connection failed: {type(e).__name__}", exc_info=True)

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
        except Exception as e:
            # BUG-474-HYB-3: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"ChromaDB health check failed: {type(e).__name__}", exc_info=True)
        return False

    def query(self, query_text: str, query_type: Literal["inference", "semantic", "combined", "auto"] = "auto",
              collection: str = "claude_memories", n_results: int = 10) -> QueryResult:
        """Execute query with automatic routing to TypeDB or ChromaDB."""
        start_time = time.time()
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
        inference_score = sum(1 for kw in self.INFERENCE_KEYWORDS if kw in query_lower)
        semantic_score = sum(1 for kw in self.SEMANTIC_KEYWORDS if kw in query_lower)
        if "RULE-" in query_text or "DECISION-" in query_text:
            inference_score += 2
        if "?" in query_text and ("what" in query_lower or "how" in query_lower):
            semantic_score += 1
        if inference_score > semantic_score:
            return "inference"
        elif semantic_score > inference_score:
            return "semantic"
        else:
            return "semantic"  # Default to semantic

    def _query_typedb(self, query_text: str, start_time: float) -> QueryResult:
        """Execute inference query on TypeDB."""
        if not self._typedb_client or not self._typedb_client.is_connected():
            return self._query_chromadb_fallback(query_text, start_time)
        try:
            results = []
            if "depends on" in query_text.lower():
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
            return self._query_chromadb_fallback(query_text, start_time, error=str(e))

    def _query_chromadb(self, query_text: str, collection: str, n_results: int,
                        start_time: float) -> QueryResult:
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
            coll = self._chromadb_client.get_collection(collection)
            response = coll.query(query_texts=[query_text], n_results=n_results,
                                  include=["documents", "metadatas", "distances"])
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

    def _query_combined(self, query_text: str, collection: str, n_results: int,
                        start_time: float) -> QueryResult:
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

    def _query_chromadb_fallback(self, query_text: str, start_time: float,
                                 error: str = None) -> QueryResult:
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
