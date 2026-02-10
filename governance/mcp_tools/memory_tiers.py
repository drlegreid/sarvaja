"""
Three-Tier Memory Model MCP Tools (G.2)
========================================
Holographic memory model with short/long/persistent memory tiers.

Per EPIC-G: Context Rot Protection.

Memory Tiers:
  L1 (Short): Current task context — what's in the context window.
              Tracked by entropy monitor. Lost on compaction.
  L2 (Long):  Session-level summaries — compiled views in ChromaDB.
              Survives compaction, lost on container restart.
  L3 (Persistent): Rules, decisions, audit trail in TypeDB.
              Survives everything.

Created: 2026-02-09
"""

import json
import logging
from datetime import datetime
from typing import Optional, List

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)

# L1 short memory: in-process dict, lost on restart
_short_memory: dict = {}


def register_memory_tier_tools(mcp) -> None:
    """Register three-tier memory MCP tools."""

    @mcp.tool()
    def memory_save(
        tier: str,
        content: str,
        tags: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Save content to the appropriate memory tier.

        Tiers:
          L1 (short): In-process memory, fast, lost on compaction/restart.
          L2 (long): ChromaDB, survives compaction, queryable.
          L3 (persistent): TypeDB rules/audit, survives everything.

        Args:
            tier: Memory tier — "L1", "L2", or "L3"
            content: Content to save
            tags: Comma-separated tags for retrieval
            session_id: Associated session ID

        Returns:
            Confirmation with memory ID.
        """
        tier = tier.upper()
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        ts = datetime.now().isoformat()
        memory_id = f"MEM-{tier}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if tier == "L1":
            _short_memory[memory_id] = {
                "content": content,
                "tags": tag_list,
                "session_id": session_id,
                "created": ts,
            }
            return format_mcp_result({
                "memory_id": memory_id,
                "tier": "L1",
                "status": "saved",
                "note": "Short memory — lost on compaction/restart",
            })

        elif tier == "L2":
            # Save to ChromaDB via claude-mem
            try:
                # Use governance stores ChromaDB integration if available
                import chromadb
                chroma = chromadb.HttpClient(host="localhost", port=8001)
                if chroma:
                    collection = chroma.get_or_create_collection("memory_tiers")
                    collection.add(
                        ids=[memory_id],
                        documents=[content],
                        metadatas=[{
                            "tier": "L2",
                            "tags": ",".join(tag_list),
                            "session_id": session_id or "",
                            "created": ts,
                        }],
                    )
                    return format_mcp_result({
                        "memory_id": memory_id,
                        "tier": "L2",
                        "status": "saved_chromadb",
                    })
            except Exception as e:
                logger.debug(f"ChromaDB save failed, falling back to L1: {e}")

            # Fallback: save to L1 with L2 marker
            _short_memory[memory_id] = {
                "content": content,
                "tags": tag_list,
                "session_id": session_id,
                "created": ts,
                "intended_tier": "L2",
            }
            return format_mcp_result({
                "memory_id": memory_id,
                "tier": "L2",
                "status": "saved_fallback_L1",
                "warning": "ChromaDB unavailable, saved to L1",
            })

        elif tier == "L3":
            # TypeDB persistent storage via audit trail
            try:
                from governance.stores.audit import record_audit
                record_audit(
                    "CREATE", "memory", memory_id,
                    actor_id="memory-tier-system",
                    metadata={
                        "content": content[:500],
                        "tags": tag_list,
                        "session_id": session_id,
                    },
                )
                return format_mcp_result({
                    "memory_id": memory_id,
                    "tier": "L3",
                    "status": "saved_typedb_audit",
                })
            except Exception as e:
                logger.debug(f"TypeDB audit save failed: {e}")
                return format_mcp_result({
                    "memory_id": memory_id,
                    "tier": "L3",
                    "status": "error",
                    "error": str(e),
                })

        return format_mcp_result({"error": f"Unknown tier: {tier}. Use L1, L2, or L3."})

    @mcp.tool()
    def memory_recall(
        query: str,
        tier: Optional[str] = None,
        limit: int = 5,
    ) -> str:
        """Search across memory tiers for relevant content.

        Searches L1 (in-process), L2 (ChromaDB), and L3 (TypeDB audit)
        for content matching the query. Returns results ranked by relevance.

        Args:
            query: Search query
            tier: Specific tier to search (L1/L2/L3) or None for all
            limit: Max results per tier

        Returns:
            Matching memories across tiers.
        """
        results = {"query": query, "results": []}
        query_lower = query.lower()

        # L1: Search short memory (keyword match)
        if not tier or tier.upper() == "L1":
            for mid, mem in _short_memory.items():
                if (query_lower in mem["content"].lower()
                        or any(query_lower in t.lower() for t in mem.get("tags", []))):
                    results["results"].append({
                        "memory_id": mid,
                        "tier": "L1",
                        "content": mem["content"][:300],
                        "tags": mem.get("tags", []),
                        "created": mem.get("created", ""),
                    })
                    if len(results["results"]) >= limit:
                        break

        # L2: Search ChromaDB (semantic search)
        if not tier or tier.upper() == "L2":
            try:
                import chromadb
                chroma = chromadb.HttpClient(host="localhost", port=8001)
                if chroma:
                    collection = chroma.get_or_create_collection("memory_tiers")
                    hits = collection.query(
                        query_texts=[query],
                        n_results=limit,
                    )
                    for i, doc in enumerate(hits.get("documents", [[]])[0]):
                        meta = (hits.get("metadatas", [[]])[0][i]
                                if hits.get("metadatas") else {})
                        results["results"].append({
                            "memory_id": hits["ids"][0][i] if hits.get("ids") else f"L2-{i}",
                            "tier": "L2",
                            "content": doc[:300],
                            "tags": meta.get("tags", "").split(","),
                            "created": meta.get("created", ""),
                        })
            except Exception as e:
                logger.debug(f"ChromaDB recall failed: {e}")

        # L3: Search audit trail (keyword match)
        if not tier or tier.upper() == "L3":
            try:
                from governance.stores.audit import query_audit_trail
                entries = query_audit_trail(entity_type="memory", limit=50)
                for entry in entries:
                    meta = entry.get("metadata", {})
                    content = meta.get("content", "")
                    if query_lower in content.lower():
                        results["results"].append({
                            "memory_id": entry.get("entity_id", "?"),
                            "tier": "L3",
                            "content": content[:300],
                            "tags": meta.get("tags", []),
                            "created": entry.get("timestamp", ""),
                        })
                        if len([r for r in results["results"] if r["tier"] == "L3"]) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Audit recall failed: {e}")

        results["total"] = len(results["results"])
        return format_mcp_result(results)
