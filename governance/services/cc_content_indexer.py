"""Streaming content indexer: JSONL -> semantic chunks -> ChromaDB.

Processes Claude Code session JSONL files incrementally, accumulating
assistant text into semantic chunks and upserting to ChromaDB.
Memory-safe: generator-based, O(1) per line, ~55MB peak for 641MB files.

Per SESSION-METRICS-01-v1.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Generator

from governance.embedding_pipeline.chunking import chunk_content
from governance.services.ingestion_checkpoint import (
    IngestionCheckpoint,
    get_resume_offset,
    load_checkpoint,
    save_checkpoint,
)

logger = logging.getLogger(__name__)

# ChromaDB collection for session content (separate from sim_ai_sessions)
CONTENT_COLLECTION = "sim_ai_session_content"


def _get_chromadb_collection(collection_name: str = CONTENT_COLLECTION) -> Any:
    """Lazy-import ChromaDB and get/create collection.

    Returns a chromadb.Collection instance (typed as Any to avoid import dependency).
    """
    import chromadb

    host = os.getenv("CHROMADB_HOST", "localhost")
    # BUG-334-INDEX-001: Guard against non-numeric CHROMADB_PORT at call time
    try:
        port = int(os.getenv("CHROMADB_PORT", "8001"))
    except (ValueError, TypeError):
        port = 8001
    client = chromadb.HttpClient(host=host, port=port)
    return client.get_or_create_collection(collection_name)


def _accumulate_semantic_chunks(
    entries: Generator, chunk_size: int = 2000
) -> Generator[tuple[str, dict], None, None]:
    """Accumulate ParsedEntry text into semantic chunks.

    Yields (text, metadata) tuples when accumulated text reaches chunk_size.
    Only includes assistant text_content (not user content for privacy).
    """
    buffer = ""
    chunk_index = 0
    line_start = 0
    line_end = 0
    last_timestamp = ""
    last_branch = ""
    entry_types: set[str] = set()

    for i, entry in enumerate(entries):
        if not entry.text_content:
            continue

        if not buffer:
            line_start = i

        buffer += entry.text_content + "\n"
        line_end = i
        entry_types.add(entry.entry_type)

        if entry.timestamp:
            last_timestamp = entry.timestamp.isoformat()
        if entry.git_branch:
            last_branch = entry.git_branch

        if len(buffer) >= chunk_size:
            meta = {
                "chunk_index": chunk_index,
                "line_start": line_start,
                "line_end": line_end,
                "entry_types": ",".join(sorted(entry_types)),
                "timestamp": last_timestamp,
                "git_branch": last_branch or "",
            }
            yield buffer.rstrip(), meta
            buffer = ""
            chunk_index += 1
            entry_types = set()

    # Flush remainder
    if buffer.strip():
        meta = {
            "chunk_index": chunk_index,
            "line_start": line_start,
            "line_end": line_end,
            "entry_types": ",".join(sorted(entry_types)),
            "timestamp": last_timestamp,
            "git_branch": last_branch or "",
        }
        yield buffer.rstrip(), meta


def index_session_content(
    jsonl_path: Path,
    session_id: str,
    *,
    batch_size: int = 100,
    chunk_size: int = 2000,
    include_thinking: bool = False,
    resume: bool = True,
    dry_run: bool = False,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Stream-index session JSONL content into ChromaDB.

    Args:
        jsonl_path: Path to the .jsonl file.
        session_id: Session identifier for metadata.
        batch_size: ChromaDB upsert batch size.
        chunk_size: Max chars per semantic chunk.
        include_thinking: Include thinking blocks in index.
        resume: Resume from checkpoint if available.
        dry_run: Report what would be done without writing.
        checkpoint_dir: Override checkpoint storage location.

    Returns:
        Dict with chunks_indexed, lines_processed, resumed_from, status, errors.
    """
    from governance.session_metrics.parser import parse_log_file_extended

    start_line = 0
    if resume:
        start_line = get_resume_offset(session_id, checkpoint_dir)

    ckpt = load_checkpoint(session_id, checkpoint_dir)
    if ckpt is None:
        ckpt = IngestionCheckpoint(
            session_id=session_id,
            jsonl_path=str(jsonl_path),
            phase="content",
        )
    else:
        ckpt.phase = "content"

    result = {
        "chunks_indexed": 0,
        "lines_processed": start_line,
        "resumed_from": start_line,
        "status": "success",
        "errors": [],
    }

    collection = None
    if not dry_run:
        try:
            collection = _get_chromadb_collection()
        except Exception as e:
            msg = f"ChromaDB connection failed: {e}"
            logger.error(msg)
            return {**result, "status": "error", "errors": [msg]}

    # BUG-194-002: Guard against missing JSONL file before streaming
    if not Path(jsonl_path).exists():
        msg = f"JSONL file not found: {jsonl_path}"
        logger.error(msg)
        return {**result, "status": "error", "errors": [msg]}

    # Stream entries from JSONL
    entries = parse_log_file_extended(
        jsonl_path, include_thinking=include_thinking, start_line=start_line
    )

    # Accumulate into semantic chunks
    batch_ids: list[str] = []
    batch_docs: list[str] = []
    batch_metas: list[dict] = []
    lines_seen = start_line

    for text, meta in _accumulate_semantic_chunks(entries, chunk_size):
        # Apply chunk_content for oversized chunks
        sub_chunks = chunk_content(text, chunk_size)

        for sub_idx, sub_text in enumerate(sub_chunks):
            chunk_id = f"{session_id}::chunk-{meta['chunk_index']}-{sub_idx}"
            chunk_meta = {
                **meta,
                "session_id": session_id,
                "source_type": "cc_session_content",
                "sub_index": sub_idx,
            }

            batch_ids.append(chunk_id)
            batch_docs.append(sub_text)
            batch_metas.append(chunk_meta)

            if len(batch_ids) >= batch_size:
                # BUG-236-IDX-002: Only count chunks on successful upsert
                upsert_ok = True
                if not dry_run and collection is not None:
                    try:
                        collection.upsert(
                            ids=batch_ids,
                            documents=batch_docs,
                            metadatas=batch_metas,
                        )
                    except Exception as e:
                        msg = f"ChromaDB upsert failed at chunk {meta['chunk_index']}: {e}"
                        logger.error(msg)
                        result["errors"].append(msg)
                        ckpt.add_error(msg)
                        upsert_ok = False

                if upsert_ok:
                    result["chunks_indexed"] += len(batch_ids)
                # BUG-257-IDX-001: line_end is relative to current run; add start_line for absolute offset
                lines_seen = start_line + meta.get("line_end", lines_seen - start_line) + 1
                result["lines_processed"] = lines_seen

                # Checkpoint after each batch
                ckpt.chunks_indexed = result["chunks_indexed"]
                ckpt.lines_processed = lines_seen
                if not dry_run:
                    save_checkpoint(ckpt, checkpoint_dir)

                batch_ids, batch_docs, batch_metas = [], [], []

    # Flush final batch
    if batch_ids:
        # BUG-236-IDX-002: Only count chunks on successful upsert
        final_ok = True
        if not dry_run and collection is not None:
            try:
                collection.upsert(
                    ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                )
            except Exception as e:
                msg = f"ChromaDB final upsert failed: {e}"
                logger.error(msg)
                result["errors"].append(msg)
                ckpt.add_error(msg)
                final_ok = False

        if final_ok:
            result["chunks_indexed"] += len(batch_ids)
        # Update lines_processed for the final partial batch
        if batch_metas:
            # BUG-257-IDX-001: line_end is relative to current run; add start_line for absolute offset
            lines_seen = start_line + batch_metas[-1].get("line_end", lines_seen - start_line) + 1
            result["lines_processed"] = lines_seen

    # Final checkpoint
    ckpt.chunks_indexed = result["chunks_indexed"]
    ckpt.lines_processed = result["lines_processed"]
    ckpt.phase = "content_complete"
    if not dry_run:
        save_checkpoint(ckpt, checkpoint_dir)

    if result["errors"]:
        result["status"] = "partial"

    return result


def delete_session_content(session_id: str) -> dict[str, Any]:
    """Remove all indexed content for a session from ChromaDB.

    Returns dict with deleted_count and status.
    """
    try:
        collection = _get_chromadb_collection()
        # ChromaDB where filter on metadata
        collection.delete(where={"session_id": session_id})
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}
