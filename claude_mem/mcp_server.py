"""
Claude-Mem MCP Server
=====================
Created: 2026-01-11
Per RULE-024: AMNESIA Protocol

Provides semantic memory tools for Claude Code context recovery.

Tools:
- chroma_query_documents: Semantic search for memories
- chroma_get_documents: Get specific documents by ID
- chroma_add_documents: Add new memories
- chroma_delete_documents: Remove memories
- chroma_health: Check ChromaDB connection

Usage:
    python -m claude_mem.mcp_server

Or add to MCP config:
    {
        "claude-mem": {
            "command": "bash",
            "args": ["scripts/mcp-runner.sh", "claude_mem.mcp_server"],
            "env": {"CHROMADB_HOST": "localhost", "CHROMADB_PORT": "8001"}
        }
    }
"""

import os
from datetime import datetime
from typing import List, Optional

# Disable ChromaDB telemetry per user request
os.environ["ANONYMIZED_TELEMETRY"] = "false"

from mcp.server.fastmcp import FastMCP

from governance.mcp_output import format_output, OutputFormat

# Initialize MCP server
mcp = FastMCP("claude-mem")

# Configuration
CHROMADB_HOST = os.environ.get("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.environ.get("CHROMADB_PORT", "8001"))
COLLECTION_NAME = "claude_memories"


def _get_client():
    """Get ChromaDB client."""
    try:
        import chromadb
        return chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
    except Exception as e:
        return None


def _get_or_create_collection(client):
    """Get or create the memories collection."""
    try:
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Claude-mem memories for AMNESIA recovery"}
        )
    except Exception as e:
        return None


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
def chroma_query_documents(
    query_texts: List[str],
    n_results: int = 10,
    where: Optional[dict] = None
) -> str:
    """
    Semantic search for memories in ChromaDB.

    IMPORTANT: Always include project name in query for isolation.
    Example: ["sim-ai 2026-01 infrastructure"] not just ["infrastructure"]

    Include dates (YYYY-MM-DD) in query text for temporal search.

    Args:
        query_texts: List of search queries (include project name!)
        n_results: Number of results to return (default: 10)
        where: Optional metadata filter (simple filters only, avoid $and/$or)

    Returns:
        JSON with matching documents, IDs, and distances

    Example:
        chroma_query_documents(["sim-ai 2026-01 AMNESIA recovery"])
    """
    client = _get_client()
    if client is None:
        return format_output({"error": "ChromaDB not available", "host": CHROMADB_HOST, "port": CHROMADB_PORT})

    collection = _get_or_create_collection(client)
    if collection is None:
        return format_output({"error": "Could not access collection"})

    try:
        # Build query kwargs
        kwargs = {
            "query_texts": query_texts,
            "n_results": n_results
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        return format_output({
            "ids": results.get("ids", [[]]),
            "documents": results.get("documents", [[]]),
            "metadatas": results.get("metadatas", [[]]),
            "distances": results.get("distances", [[]]),
            "count": len(results.get("ids", [[]])[0]) if results.get("ids") else 0
        })

    except Exception as e:
        return format_output({"error": str(e)})


@mcp.tool()
def chroma_get_documents(ids: List[str]) -> str:
    """
    Get specific documents by ID from ChromaDB.

    Args:
        ids: List of document IDs to retrieve

    Returns:
        JSON with documents and metadata

    Example:
        chroma_get_documents(ids=["mem-2026-01-11-001"])
    """
    client = _get_client()
    if client is None:
        return format_output({"error": "ChromaDB not available"})

    collection = _get_or_create_collection(client)
    if collection is None:
        return format_output({"error": "Could not access collection"})

    try:
        results = collection.get(ids=ids)

        return format_output({
            "ids": results.get("ids", []),
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "count": len(results.get("ids", []))
        })

    except Exception as e:
        return format_output({"error": str(e)})


@mcp.tool()
def chroma_add_documents(
    documents: List[str],
    ids: Optional[List[str]] = None,
    metadatas: Optional[List[dict]] = None,
    project: str = "sim-ai"
) -> str:
    """
    Add new memories to ChromaDB.

    Memories are stored with project isolation and timestamps.

    Args:
        documents: List of document contents to store
        ids: Optional custom IDs (auto-generated if not provided)
        metadatas: Optional metadata dicts for each document
        project: Project name for isolation (default: sim-ai)

    Returns:
        JSON with stored document IDs

    Example:
        chroma_add_documents(
            documents=["Fixed TypeDB connection issue by..."],
            metadatas=[{"topic": "infrastructure", "session": "2026-01-11"}],
            project="sim-ai"
        )
    """
    client = _get_client()
    if client is None:
        return format_output({"error": "ChromaDB not available"})

    collection = _get_or_create_collection(client)
    if collection is None:
        return format_output({"error": "Could not access collection"})

    try:
        # Generate IDs if not provided
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if ids is None:
            ids = [f"mem-{project}-{timestamp}-{i:03d}" for i in range(len(documents))]

        # Build metadata with project and timestamp
        if metadatas is None:
            metadatas = [{} for _ in documents]

        for i, meta in enumerate(metadatas):
            meta["project"] = project
            meta["created_at"] = datetime.now().isoformat()
            meta["source"] = "claude-mem"

        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

        return format_output({
            "success": True,
            "ids": ids,
            "count": len(ids),
            "project": project
        })

    except Exception as e:
        return format_output({"error": str(e)})


@mcp.tool()
def chroma_delete_documents(ids: List[str]) -> str:
    """
    Delete memories from ChromaDB.

    Args:
        ids: List of document IDs to delete

    Returns:
        JSON with deletion status

    Example:
        chroma_delete_documents(ids=["mem-sim-ai-20260111-001"])
    """
    client = _get_client()
    if client is None:
        return format_output({"error": "ChromaDB not available"})

    collection = _get_or_create_collection(client)
    if collection is None:
        return format_output({"error": "Could not access collection"})

    try:
        collection.delete(ids=ids)

        return format_output({
            "success": True,
            "deleted": ids,
            "count": len(ids)
        })

    except Exception as e:
        return format_output({"error": str(e)})


@mcp.tool()
def chroma_health() -> str:
    """
    Check ChromaDB connection health.

    Returns:
        JSON with health status and collection info
    """
    client = _get_client()
    if client is None:
        return format_output({
            "status": "unhealthy",
            "error": "Cannot connect to ChromaDB",
            "host": CHROMADB_HOST,
            "port": CHROMADB_PORT,
            "action_required": "START_SERVICES",
            "recovery_hint": "podman compose --profile cpu up -d chromadb"
        })

    try:
        # Check heartbeat
        client.heartbeat()

        # Get collection info
        collection = _get_or_create_collection(client)
        count = collection.count() if collection else 0

        return format_output({
            "status": "healthy",
            "host": CHROMADB_HOST,
            "port": CHROMADB_PORT,
            "collection": COLLECTION_NAME,
            "document_count": count
        })

    except Exception as e:
        return format_output({
            "status": "unhealthy",
            "error": str(e),
            "host": CHROMADB_HOST,
            "port": CHROMADB_PORT
        })


@mcp.tool()
def chroma_save_session_context(
    session_id: str,
    summary: str,
    key_decisions: List[str],
    files_modified: List[str],
    gaps_discovered: List[str],
    project: str = "sim-ai"
) -> str:
    """
    Save session context for AMNESIA recovery (RULE-024).

    Call this before session ends to preserve context.

    Args:
        session_id: Session identifier (e.g., SESSION-2026-01-11-PLATFORM)
        summary: Brief summary of session accomplishments
        key_decisions: List of key decisions made
        files_modified: List of files modified
        gaps_discovered: List of gaps discovered
        project: Project name (default: sim-ai)

    Returns:
        JSON with stored context ID

    Example:
        chroma_save_session_context(
            session_id="SESSION-2026-01-11-PLATFORM",
            summary="Implemented claude-mem MCP server",
            key_decisions=["Use ChromaDB for semantic memory"],
            files_modified=["claude_mem/mcp_server.py"],
            gaps_discovered=["GAP-MEM-001"]
        )
    """
    # Build structured context document
    context = f"""# Session: {session_id}
Project: {project}
Date: {datetime.now().isoformat()}

## Summary
{summary}

## Key Decisions
{chr(10).join(f'- {d}' for d in key_decisions)}

## Files Modified
{chr(10).join(f'- {f}' for f in files_modified)}

## Gaps Discovered
{chr(10).join(f'- {g}' for g in gaps_discovered)}
"""

    metadata = {
        "type": "session_context",
        "session_id": session_id,
        "project": project,
        "file_count": len(files_modified),
        "decision_count": len(key_decisions),
        "gap_count": len(gaps_discovered)
    }

    return chroma_add_documents(
        documents=[context],
        ids=[f"ctx-{session_id}"],
        metadatas=[metadata],
        project=project
    )


@mcp.tool()
def chroma_recover_context(
    project: str = "sim-ai",
    n_results: int = 5
) -> str:
    """
    Recover recent session context for AMNESIA recovery (RULE-024).

    Call this after context compaction/AMNESIA to restore state.

    Args:
        project: Project name (default: sim-ai)
        n_results: Number of recent sessions to retrieve

    Returns:
        JSON with recent session contexts

    Example:
        chroma_recover_context(project="sim-ai", n_results=3)
    """
    # Search for recent session contexts
    return chroma_query_documents(
        query_texts=[f"{project} session context decisions files"],
        n_results=n_results,
        where={"type": "session_context"}
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    mcp.run()
