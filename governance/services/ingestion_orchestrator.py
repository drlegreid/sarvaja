"""Ingestion orchestrator: coordinates content indexing + link mining.

Runs D2 (content indexer) and D3 (link miner) in sequence with memory
monitoring, error budgets, and checkpoint coordination.

Per SESSION-METRICS-01-v1.
"""

from __future__ import annotations

import logging
import resource
from pathlib import Path
from typing import Any

from governance.services.cc_content_indexer import (
    delete_session_content,
    index_session_content,
)
from governance.services.cc_link_miner import mine_session_links
from governance.services.ingestion_checkpoint import (
    IngestionCheckpoint,
    delete_checkpoint,
    load_checkpoint,
    save_checkpoint,
)

logger = logging.getLogger(__name__)


def _get_rss_mb() -> float:
    """Get current process RSS in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux
    return usage.ru_maxrss / 1024.0


def _validate_jsonl_path(path: Path) -> bool:
    """BUG-301-ORCH-001: Validate jsonl_path is under allowed base directories."""
    _allowed_bases = [
        Path.home() / ".claude" / "projects",
        Path(__file__).resolve().parent.parent,  # governance root → project root parent
    ]
    resolved = path.resolve()
    # BUG-322-ORCH-001: Use relative_to() instead of startswith() to prevent
    # path traversal bypass (e.g. "/allowed_base_extra/../evil" matches startswith)
    for b in _allowed_bases:
        try:
            resolved.relative_to(b.resolve())
            return True
        except ValueError:
            continue
    return False


def estimate_ingestion(jsonl_path: Path) -> dict[str, Any]:
    """Estimate ingestion work without processing.

    Returns file stats and estimated chunk/link counts.
    """
    path = Path(jsonl_path)
    if not path.exists():
        # BUG-381-ORCH-001: Redact absolute path from error response
        return {"error": f"File not found: {path.name}", "status": "error"}
    # BUG-301-ORCH-001: Path containment check
    if not _validate_jsonl_path(path):
        return {"error": "Path outside allowed directories", "status": "error"}

    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    # Count lines without loading entire file
    line_count = 0
    # BUG-199-ORCH-001: Specify encoding for locale-independent file reading
    with open(path, "r", encoding="utf-8") as f:
        for _ in f:
            line_count += 1

    # Rough estimates based on typical JSONL structure:
    # ~30% of lines have assistant text content
    # ~2000 chars per chunk => ~4KB avg line => chunks ≈ lines * 0.3 * avg_len / 2000
    est_content_lines = int(line_count * 0.3)
    est_chunks = max(1, est_content_lines * 2)  # ~2 chunks per content line

    return {
        "file": str(path),
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 1),
        "line_count": line_count,
        "est_content_lines": est_content_lines,
        "est_chunks": est_chunks,
        "est_memory_mb": 55,  # Generator-based, constant memory
        "status": "ok",
    }


def get_ingestion_status(
    session_id: str, checkpoint_dir: Path | None = None
) -> dict[str, Any]:
    """Get current ingestion status for a session."""
    ckpt = load_checkpoint(session_id, checkpoint_dir)
    if ckpt is None:
        return {"session_id": session_id, "status": "not_started"}

    return {
        "session_id": session_id,
        "status": ckpt.phase,
        "lines_processed": ckpt.lines_processed,
        "chunks_indexed": ckpt.chunks_indexed,
        "links_created": ckpt.links_created,
        "started_at": ckpt.started_at,
        "updated_at": ckpt.updated_at,
        "error_count": len(ckpt.errors),
        "recent_errors": ckpt.errors[-5:] if ckpt.errors else [],
    }


def rollback_content_index(session_id: str) -> dict[str, Any]:
    """Remove all indexed content for a session (ChromaDB + checkpoint)."""
    results: dict[str, Any] = {"session_id": session_id}

    # Delete from ChromaDB
    chroma_result = delete_session_content(session_id)
    results["chromadb"] = chroma_result

    # Delete checkpoint
    deleted = delete_checkpoint(session_id)
    results["checkpoint_deleted"] = deleted
    results["status"] = "rolled_back"

    return results


def run_ingestion_pipeline(
    jsonl_path: Path,
    session_id: str,
    *,
    phases: list[str] | None = None,
    dry_run: bool = False,
    resume: bool = True,
    memory_limit_mb: int = 500,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the full ingestion pipeline: content indexing + link mining.

    Args:
        jsonl_path: Path to the .jsonl file.
        session_id: Session identifier.
        phases: Which phases to run ("content", "linking"). Default: both.
        dry_run: Report without writing.
        resume: Resume from checkpoint.
        memory_limit_mb: Pause if RSS exceeds this.
        checkpoint_dir: Override checkpoint storage.

    Returns:
        Combined results from content indexing and link mining.
    """
    if phases is None:
        phases = ["content", "linking"]

    path = Path(jsonl_path)
    if not path.exists():
        # BUG-381-ORCH-001: Redact absolute path from error response
        return {"error": f"File not found: {path.name}", "status": "error"}
    # BUG-301-ORCH-001: Path containment check
    if not _validate_jsonl_path(path):
        return {"error": "Path outside allowed directories", "status": "error"}

    result: dict[str, Any] = {
        "session_id": session_id,
        # BUG-381-ORCH-002: Use filename only, not absolute path, in response
        "file": path.name,
        "phases_requested": phases,
        "content": None,
        "linking": None,
        "status": "success",
        "memory_mb": round(_get_rss_mb(), 1),
    }

    # Phase 1: Content indexing
    if "content" in phases:
        logger.info(f"Starting content indexing for {session_id}")

        # Memory check before starting
        rss = _get_rss_mb()
        if rss > memory_limit_mb:
            msg = f"Memory limit exceeded before content phase: {rss:.0f}MB > {memory_limit_mb}MB"
            logger.warning(msg)
            result["status"] = "memory_limit"
            result["content"] = {"status": "skipped", "reason": msg}
        else:
            content_result = index_session_content(
                path,
                session_id,
                resume=resume,
                dry_run=dry_run,
                checkpoint_dir=checkpoint_dir,
            )
            result["content"] = content_result

            if content_result.get("status") == "error":
                result["status"] = "partial"

    # Phase 2: Link mining
    if "linking" in phases:
        logger.info(f"Starting link mining for {session_id}")

        rss = _get_rss_mb()
        if rss > memory_limit_mb:
            msg = f"Memory limit exceeded before linking phase: {rss:.0f}MB > {memory_limit_mb}MB"
            logger.warning(msg)
            result["linking"] = {"status": "skipped", "reason": msg}
            if result["status"] == "success":
                result["status"] = "partial"
        else:
            linking_result = mine_session_links(
                path,
                session_id,
                dry_run=dry_run,
                checkpoint_dir=checkpoint_dir,
            )
            result["linking"] = linking_result

            if linking_result.get("status") == "error":
                result["status"] = "partial"

    # Final checkpoint
    ckpt = load_checkpoint(session_id, checkpoint_dir)
    if ckpt is None:
        ckpt = IngestionCheckpoint(
            session_id=session_id, jsonl_path=str(path)
        )

    if result["status"] == "success" and not dry_run:
        ckpt.phase = "complete"
    save_checkpoint(ckpt, checkpoint_dir)

    result["memory_mb"] = round(_get_rss_mb(), 1)
    return result
