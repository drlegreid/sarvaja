"""
Hybrid Query Router - TypeDB + ChromaDB Integration
Routes queries to appropriate backend based on query type.

Created: 2024-12-24 (P3.1)
Per: RULE-004 (Executable Spec), RULE-010 (Evidence-Based Wisdom)

Query Routing Logic:
- Inference queries (dependencies, conflicts) → TypeDB
- Semantic queries (natural language search) → ChromaDB
- Combined queries (typed + semantic) → Both, merged results
- Fallback: TypeDB timeout → ChromaDB semantic search

Usage:
    router = HybridQueryRouter()

    # Inference query (TypeDB)
    deps = router.query("What depends on RULE-001?", query_type="inference")

    # Semantic query (ChromaDB)
    results = router.query("authentication rules", query_type="semantic")

    # Auto-detect query type
    results = router.query("Find all governance rules about sessions")
"""

import os
import time
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum

# Import TypeDB client
try:
    from governance.client import TypeDBClient, Rule, quick_health
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from governance.client import TypeDBClient, Rule, quick_health


class QueryType(Enum):
    """Query type for routing."""
    INFERENCE = "inference"   # TypeDB: dependencies, conflicts, relations
    SEMANTIC = "semantic"     # ChromaDB: natural language search
    COMBINED = "combined"     # Both: typed entities + semantic context
    AUTO = "auto"             # Auto-detect based on query content


@dataclass
class QueryResult:
    """Unified result from hybrid query."""
    query: str
    query_type: QueryType
    source: str  # "typedb", "chromadb", "both"
    results: List[Dict[str, Any]]
    count: int
    latency_ms: float
    fallback_used: bool = False
    error: Optional[str] = None


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
        import re
        match = re.search(r'RULE-\d{3}', text)
        return match.group(0) if match else None

    def _extract_decision_id(self, text: str) -> Optional[str]:
        """Extract DECISION-XXX from text."""
        import re
        match = re.search(r'DECISION-\d{3}', text)
        return match.group(0) if match else None


# =============================================================================
# SYNC BRIDGE
# =============================================================================

@dataclass
class SyncStatus:
    """Status of sync operation."""
    source: str
    target: str
    synced_count: int
    skipped_count: int
    error_count: int
    last_sync: Optional[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MemorySyncBridge:
    """
    Bidirectional sync between ChromaDB and TypeDB.

    Sync Directions:
    - TypeDB → ChromaDB: Push typed entities for semantic search
    - ChromaDB → TypeDB: Pull memories to create typed entities

    Collections:
    - sim_ai_rules: Governance rules from TypeDB
    - sim_ai_decisions: Decisions from TypeDB
    - sim_ai_agents: Agent definitions from TypeDB
    - claude_memories: User memories (primary semantic store)
    """

    def __init__(self, router: HybridQueryRouter):
        self.router = router
        self._last_sync: Dict[str, str] = {}

    def sync_rules_to_chromadb(self, collection: str = "sim_ai_rules") -> SyncStatus:
        """Push all TypeDB rules to ChromaDB for semantic search."""
        status = SyncStatus(
            source="typedb",
            target="chromadb",
            synced_count=0,
            skipped_count=0,
            error_count=0
        )

        if not self.router._typedb_client:
            status.errors.append("TypeDB client not connected")
            return status

        try:
            rules = self.router._typedb_client.get_all_rules()
        except Exception as e:
            status.errors.append(f"Failed to get rules: {e}")
            status.error_count = 1
            return status

        if not self.router._chromadb_client:
            status.errors.append("ChromaDB client not connected")
            return status

        try:
            # Get or create collection
            coll = self.router._chromadb_client.get_or_create_collection(collection)

            # Upsert rules
            documents = []
            metadatas = []
            ids = []

            for rule in rules:
                documents.append(f"{rule.name}: {rule.directive}")
                metadatas.append({
                    "rule_id": rule.id,
                    "category": rule.category,
                    "priority": rule.priority,
                    "status": rule.status,
                    "sync_source": "typedb"
                })
                ids.append(f"rule_{rule.id}")

            if documents:
                coll.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            status.synced_count = len(documents)
            status.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
            self._last_sync["rules"] = status.last_sync

            return status

        except Exception as e:
            status.errors.append(f"Sync error: {e}")
            status.error_count = 1
            return status

    def sync_decisions_to_chromadb(self, collection: str = "sim_ai_decisions") -> SyncStatus:
        """Push all TypeDB decisions to ChromaDB for semantic search."""
        status = SyncStatus(
            source="typedb",
            target="chromadb",
            synced_count=0,
            skipped_count=0,
            error_count=0
        )

        if not self.router._typedb_client:
            status.errors.append("TypeDB client not connected")
            return status

        if not self.router._chromadb_client:
            status.errors.append("ChromaDB client not connected")
            return status

        try:
            # Get or create collection
            coll = self.router._chromadb_client.get_or_create_collection(collection)

            # Query decisions from TypeDB
            decisions = self.router._typedb_client.execute_query(
                "match $d isa decision; fetch $d: id, title, rationale, status;"
            )

            documents = []
            metadatas = []
            ids = []

            for d in decisions if decisions else []:
                if isinstance(d, dict):
                    doc = f"{d.get('title', '')}: {d.get('rationale', '')}"
                    documents.append(doc)
                    metadatas.append({
                        "decision_id": d.get("id", ""),
                        "status": d.get("status", ""),
                        "sync_source": "typedb"
                    })
                    ids.append(f"decision_{d.get('id', 'unknown')}")

            if documents:
                coll.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            status.synced_count = len(documents)
            status.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
            self._last_sync["decisions"] = status.last_sync

            return status

        except Exception as e:
            status.errors.append(f"Sync error: {e}")
            status.error_count = 1
            return status

    def sync_agents_to_chromadb(self, collection: str = "sim_ai_agents") -> SyncStatus:
        """Push all TypeDB agents to ChromaDB for semantic search."""
        status = SyncStatus(
            source="typedb",
            target="chromadb",
            synced_count=0,
            skipped_count=0,
            error_count=0
        )

        if not self.router._typedb_client:
            status.errors.append("TypeDB client not connected")
            return status

        if not self.router._chromadb_client:
            status.errors.append("ChromaDB client not connected")
            return status

        try:
            # Get or create collection
            coll = self.router._chromadb_client.get_or_create_collection(collection)

            # Query agents from TypeDB
            agents = self.router._typedb_client.execute_query(
                "match $a isa agent; fetch $a: id, name, agent_type, trust_score;"
            )

            documents = []
            metadatas = []
            ids = []

            for a in agents if agents else []:
                if isinstance(a, dict):
                    doc = f"Agent {a.get('name', '')}: {a.get('agent_type', '')} agent"
                    documents.append(doc)
                    metadatas.append({
                        "agent_id": a.get("id", ""),
                        "agent_type": a.get("agent_type", ""),
                        "trust_score": str(a.get("trust_score", 0)),
                        "sync_source": "typedb"
                    })
                    ids.append(f"agent_{a.get('id', 'unknown')}")

            if documents:
                coll.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            status.synced_count = len(documents)
            status.last_sync = time.strftime("%Y-%m-%d %H:%M:%S")
            self._last_sync["agents"] = status.last_sync

            return status

        except Exception as e:
            status.errors.append(f"Sync error: {e}")
            status.error_count = 1
            return status

    def sync_all(self) -> Dict[str, SyncStatus]:
        """Sync all entity types to ChromaDB."""
        return {
            "rules": self.sync_rules_to_chromadb(),
            "decisions": self.sync_decisions_to_chromadb(),
            "agents": self.sync_agents_to_chromadb()
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status across all collections."""
        status = {
            "last_sync": self._last_sync,
            "chromadb_connected": self.router._chromadb_client is not None,
            "typedb_connected": (
                self.router._typedb_client is not None and
                self.router._typedb_client.is_connected()
            ),
            "collections": {}
        }

        if self.router._chromadb_client:
            try:
                for coll_name in ["sim_ai_rules", "sim_ai_decisions", "sim_ai_agents"]:
                    try:
                        coll = self.router._chromadb_client.get_collection(coll_name)
                        status["collections"][coll_name] = {
                            "exists": True,
                            "count": coll.count()
                        }
                    except:
                        status["collections"][coll_name] = {
                            "exists": False,
                            "count": 0
                        }
            except Exception as e:
                status["error"] = str(e)

        return status


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid Query Router Test")
    print("=" * 60)

    router = HybridQueryRouter()
    status = router.connect()
    print(f"\nConnection status: {status}")

    health = router.health_check()
    print(f"Health: {health}")

    # Test queries
    test_queries = [
        ("What depends on RULE-001?", "inference"),
        ("Find governance rules", "semantic"),
        ("RULE-012 DSP protocol", "auto"),
        ("conflicts between rules", "inference"),
    ]

    print("\n--- Query Tests ---")
    for query, qtype in test_queries:
        result = router.query(query, query_type=qtype)
        print(f"\n[{result.query_type.value}] '{query}'")
        print(f"  Source: {result.source}")
        print(f"  Results: {result.count}")
        print(f"  Latency: {result.latency_ms:.1f}ms")
        if result.fallback_used:
            print(f"  Fallback: Yes")
        if result.error:
            print(f"  Error: {result.error}")

    router.close()
    print("\n[OK] Router test complete!")
