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
import os
import threading
from datetime import datetime
from typing import Optional, List

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)

# BUG-218-MEM-001: Use env vars for ChromaDB host/port (not hardcoded localhost)
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
# BUG-288-MEM-001: Guard against non-numeric CHROMADB_PORT at import time
try:
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
except (ValueError, TypeError):
    logger.warning("Invalid CHROMADB_PORT env var, defaulting to 8001")
    CHROMADB_PORT = 8001

# L1 short memory: in-process dict, lost on restart
# BUG-271-MEMORY-001: Cap at 500 entries to prevent unbounded growth
_short_memory: dict = {}
_SHORT_MEMORY_MAX = 500
# BUG-331-MEM-001: Lock for thread-safe access to _short_memory
_short_memory_lock = threading.Lock()


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
        # BUG-361-MEM-002: Cap content size to prevent unbounded ChromaDB storage
        _MAX_CONTENT_SIZE = 100_000  # 100KB
        if len(content) > _MAX_CONTENT_SIZE:
            content = content[:_MAX_CONTENT_SIZE]
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        ts = datetime.now().isoformat()
        # BUG-343-MEM-001: Include microseconds + random suffix to prevent ID collision
        # when two concurrent calls occur within the same second
        import uuid as _uuid_mod
        memory_id = f"MEM-{tier}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{_uuid_mod.uuid4().hex[:6]}"

        if tier == "L1":
            # BUG-331-MEM-001: Thread-safe access to _short_memory
            with _short_memory_lock:
                # BUG-271-MEMORY-001: Evict oldest entries when cap exceeded
                if len(_short_memory) >= _SHORT_MEMORY_MAX:
                    oldest_key = next(iter(_short_memory))
                    del _short_memory[oldest_key]
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
                chroma = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
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
                # BUG-416-MEM-001: Upgrade debug→warning + exc_info for ChromaDB failure
                logger.warning(f"ChromaDB save failed, falling back to L1: {type(e).__name__}", exc_info=True)

            # Fallback: save to L1 with L2 marker
            # BUG-331-MEM-001: Thread-safe access to _short_memory
            with _short_memory_lock:
                # BUG-288-MEM-002: Enforce _SHORT_MEMORY_MAX cap on L2 fallback path
                if len(_short_memory) >= _SHORT_MEMORY_MAX:
                    oldest_key = next(iter(_short_memory))
                    del _short_memory[oldest_key]
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
                # BUG-361-MEM-001: Log full error but return only type name to prevent info disclosure
                # BUG-454-MEM-001: Sanitize logger message — exc_info=True already captures full stack
                logger.error(f"TypeDB audit save failed for {memory_id}: {type(e).__name__}", exc_info=True)
                return format_mcp_result({
                    "memory_id": memory_id,
                    "tier": "L3",
                    "status": "error",
                    "error": f"L3 save failed: {type(e).__name__}",
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
            # BUG-331-MEM-001: Snapshot dict to prevent RuntimeError during concurrent mutation
            with _short_memory_lock:
                _snapshot = list(_short_memory.items())
            for mid, mem in _snapshot:
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
                chroma = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
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
                # BUG-416-MEM-002: Upgrade debug→warning + exc_info for ChromaDB failure
                logger.warning(f"ChromaDB recall failed: {type(e).__name__}", exc_info=True)

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
                # BUG-416-MEM-003: Upgrade debug→warning + exc_info for audit failure
                logger.warning(f"Audit recall failed: {type(e).__name__}", exc_info=True)

        results["total"] = len(results["results"])
        return format_mcp_result(results)
