"""
Memory Sync Bridge
==================
Bidirectional sync between ChromaDB and TypeDB.

Per RULE-004: Executable Spec
Per RULE-010: Evidence-Based Wisdom
Per GAP-FILE-012: Extracted from hybrid_router.py

Created: 2024-12-28
"""

import logging
import time
from typing import Dict, Any, TYPE_CHECKING

logger = logging.getLogger(__name__)

from .models import SyncStatus

if TYPE_CHECKING:
    from .router import HybridQueryRouter


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

    def __init__(self, router: "HybridQueryRouter"):
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
                    except Exception as e:
                        logger.debug(f"Failed to get collection {coll_name}: {e}")
                        status["collections"][coll_name] = {
                            "exists": False,
                            "count": 0
                        }
            except Exception as e:
                status["error"] = str(e)

        return status


__all__ = [
    "MemorySyncBridge",
]
