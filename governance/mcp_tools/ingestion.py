"""Session Content Ingestion MCP Tools.

Provides MCP tools for streaming JSONL content into ChromaDB and
mining cross-entity links into TypeDB.

Per SESSION-METRICS-01-v1.
"""

import json
from pathlib import Path
from typing import Optional

from governance.mcp_tools.common import format_mcp_result


def register_ingestion_tools(mcp) -> None:
    """Register ingestion MCP tools on the gov-sessions server."""

    @mcp.tool()
    def ingest_session_content(
        session_id: str,
        jsonl_path: Optional[str] = None,
        dry_run: bool = True,
        resume: bool = True,
    ) -> str:
        """Index session JSONL content into ChromaDB for semantic search.

        Streams a Claude Code JSONL log, accumulates assistant text into
        semantic chunks, and upserts to ChromaDB. Safe for mega-sessions
        (641MB+) — generator-based, ~55MB peak memory.

        Args:
            session_id: Session ID to index content for.
            jsonl_path: Path to JSONL file (auto-discovers if omitted).
            dry_run: If True (default), report without writing.
            resume: If True (default), resume from last checkpoint.
        """
        from governance.services.cc_content_indexer import index_session_content

        path = _resolve_jsonl_path(session_id, jsonl_path)
        if path is None:
            return format_mcp_result(
                "error", {"error": "JSONL file not found", "session_id": session_id}
            )

        result = index_session_content(
            path, session_id, dry_run=dry_run, resume=resume
        )
        return format_mcp_result("ok", result)

    @mcp.tool()
    def mine_session_links(
        session_id: str,
        jsonl_path: Optional[str] = None,
        dry_run: bool = True,
    ) -> str:
        """Mine JSONL for entity references and create TypeDB linkage relations.

        Scans assistant text for task, rule, gap, and decision references,
        then creates TypeDB relations (completed-in, session-applied-rule, etc.).

        Args:
            session_id: Session ID to link entities for.
            jsonl_path: Path to JSONL file (auto-discovers if omitted).
            dry_run: If True (default), report refs without creating links.
        """
        from governance.services.cc_link_miner import mine_session_links as _mine

        path = _resolve_jsonl_path(session_id, jsonl_path)
        if path is None:
            return format_mcp_result(
                "error", {"error": "JSONL file not found", "session_id": session_id}
            )

        result = _mine(path, session_id, dry_run=dry_run)
        return format_mcp_result("ok", result)

    @mcp.tool()
    def ingest_session_full(
        session_id: str,
        jsonl_path: Optional[str] = None,
        dry_run: bool = True,
    ) -> str:
        """Run full ingestion pipeline: content indexing + link mining.

        Combines ingest_session_content and mine_session_links in a single
        coordinated run with memory monitoring and checkpointing.

        Args:
            session_id: Session ID to process.
            jsonl_path: Path to JSONL file (auto-discovers if omitted).
            dry_run: If True (default), report without writing.
        """
        from governance.services.ingestion_orchestrator import run_ingestion_pipeline

        path = _resolve_jsonl_path(session_id, jsonl_path)
        if path is None:
            return format_mcp_result(
                "error", {"error": "JSONL file not found", "session_id": session_id}
            )

        result = run_ingestion_pipeline(path, session_id, dry_run=dry_run)
        return format_mcp_result("ok", result)

    @mcp.tool()
    def ingestion_status(session_id: str = "") -> str:
        """Get ingestion pipeline status for a session.

        Args:
            session_id: Session ID to check. If empty, lists all checkpoints.
        """
        from governance.services.ingestion_orchestrator import get_ingestion_status

        if not session_id:
            return _list_all_checkpoints()

        result = get_ingestion_status(session_id)
        return format_mcp_result("ok", result)

    @mcp.tool()
    def ingestion_estimate(jsonl_path: str) -> str:
        """Estimate ingestion work for a JSONL file without processing.

        Returns file size, line count, estimated chunks, and memory requirements.

        Args:
            jsonl_path: Path to the JSONL file to analyze.
        """
        from governance.services.ingestion_orchestrator import estimate_ingestion

        result = estimate_ingestion(Path(jsonl_path))
        return format_mcp_result("ok", result)


def _resolve_jsonl_path(
    session_id: str, explicit_path: Optional[str]
) -> Optional[Path]:
    """Resolve JSONL path from explicit path or auto-discovery."""
    if explicit_path:
        p = Path(explicit_path)
        return p if p.exists() else None

    try:
        from governance.services.cc_session_scanner import find_jsonl_for_session
        return find_jsonl_for_session(session_id)
    except (ImportError, Exception):
        return None


def _list_all_checkpoints() -> str:
    """List all ingestion checkpoints."""
    from governance.services.ingestion_checkpoint import _DEFAULT_CHECKPOINT_DIR

    cdir = _DEFAULT_CHECKPOINT_DIR
    if not cdir.exists():
        return format_mcp_result("ok", {"checkpoints": [], "count": 0})

    checkpoints = []
    for f in sorted(cdir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            checkpoints.append({
                "session_id": data.get("session_id", f.stem),
                "phase": data.get("phase", "unknown"),
                "lines_processed": data.get("lines_processed", 0),
                "chunks_indexed": data.get("chunks_indexed", 0),
                "updated_at": data.get("updated_at", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue

    return format_mcp_result("ok", {"checkpoints": checkpoints, "count": len(checkpoints)})
