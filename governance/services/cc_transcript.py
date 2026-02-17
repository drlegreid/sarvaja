"""
Session Transcript Extraction Service (GAP-SESSION-TRANSCRIPT-001).

Streaming JSONL parser + synthetic builder for Chat/API sessions.
Created: 2026-02-15
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from governance.session_metrics.models import TranscriptEntry

logger = logging.getLogger(__name__)

# Default truncation limits
_DEFAULT_CONTENT_LIMIT = 2000
_FULL_CONTENT_LIMIT = 50000


def _extract_user_text(content: Any) -> Optional[str]:
    """Extract user prompt text from user message content.

    Content can be a plain string or a list of blocks containing text blocks.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts) if texts else None
    return None


def _extract_tool_result_content(block: dict) -> str:
    """Extract text content from a tool_result block."""
    rc = block.get("content", "")
    if isinstance(rc, str):
        return rc
    if isinstance(rc, list):
        parts = []
        for rb in rc:
            if isinstance(rb, dict) and rb.get("type") == "text":
                parts.append(rb.get("text", ""))
        return "\n".join(parts)
    return str(rc)


def _truncate(text: str, limit: int) -> tuple:
    """Truncate text to limit. Returns (text, was_truncated)."""
    # BUG-346-TRS-001: Enforce absolute hard cap even when limit=0 (disabled)
    # to prevent multi-megabyte responses from 10KB+ Bash outputs
    _ABSOLUTE_MAX = 100_000
    effective = limit if limit > 0 else _ABSOLUTE_MAX
    if len(text) <= effective:
        return text, False
    return text[:effective] + f"\n... [{len(text) - effective} chars truncated]", True


def stream_transcript(
    filepath: Path,
    include_thinking: bool = True,
    include_user_content: bool = True,
    content_limit: int = _DEFAULT_CONTENT_LIMIT,
    start_index: int = 0,
    max_entries: int = 0,
) -> Generator[TranscriptEntry, None, None]:
    """Stream-parse JSONL into TranscriptEntry objects."""
    filepath = Path(filepath)
    if not filepath.exists():
        # BUG-TRANSCRIPT-001: Guard against missing file
        logger.warning(f"Transcript file not found: {filepath}")
        return
    entry_index = 0
    yielded = 0

    try:
        # BUG-257-TRS-001: Use context manager for reliable handle cleanup on generator abandon
        f = open(filepath, "r", encoding="utf-8")
    except (PermissionError, IOError) as e:
        logger.error(f"Cannot read transcript file {filepath}: {e}")
        return

    try:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_raw = obj.get("timestamp", "")
            entry_type = obj.get("type", "unknown")
            msg = obj.get("message", {})
            content = msg.get("content", []) if isinstance(msg, dict) else []
            model = msg.get("model") if isinstance(msg, dict) else None
            mcp_meta = obj.get("mcpMeta")

            if entry_type not in ("user", "assistant", "system"):
                continue

            # --- SYSTEM / COMPACTION ---
            if entry_type == "system":
                if obj.get("compactMetadata"):
                    if entry_index >= start_index:
                        yield TranscriptEntry(
                            index=entry_index,
                            timestamp=ts_raw,
                            entry_type="compaction",
                            content="[Context compacted]",
                            content_length=0,
                        )
                        yielded += 1
                        if max_entries > 0 and yielded >= max_entries:
                            return
                    entry_index += 1
                continue

            # --- USER ---
            if entry_type == "user":
                if include_user_content:
                    user_text = _extract_user_text(content)
                    if user_text:
                        text, truncated = _truncate(user_text, content_limit)
                        if entry_index >= start_index:
                            yield TranscriptEntry(
                                index=entry_index,
                                timestamp=ts_raw,
                                entry_type="user_prompt",
                                content=text,
                                content_length=len(user_text),
                                is_truncated=truncated,
                            )
                            yielded += 1
                            if max_entries > 0 and yielded >= max_entries:
                                return
                        entry_index += 1

                # Tool results within user content blocks
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            result_text = _extract_tool_result_content(block)
                            text, truncated = _truncate(result_text, content_limit)
                            server_name = mcp_meta.get("serverName") if mcp_meta and isinstance(mcp_meta, dict) else None
                            if entry_index >= start_index:
                                yield TranscriptEntry(
                                    index=entry_index,
                                    timestamp=ts_raw,
                                    entry_type="tool_result",
                                    content=text,
                                    content_length=len(result_text),
                                    is_truncated=truncated,
                                    tool_use_id=block.get("tool_use_id"),
                                    is_error=block.get("is_error", False),
                                    server_name=server_name,
                                )
                                yielded += 1
                                if max_entries > 0 and yielded >= max_entries:
                                    return
                            entry_index += 1
                continue

            # --- ASSISTANT ---
            if entry_type == "assistant" and isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")

                    if btype == "text":
                        text_val = block.get("text", "")
                        if not text_val.strip():
                            continue
                        text, truncated = _truncate(text_val, content_limit)
                        if entry_index >= start_index:
                            yield TranscriptEntry(
                                index=entry_index,
                                timestamp=ts_raw,
                                entry_type="assistant_text",
                                content=text,
                                content_length=len(text_val),
                                is_truncated=truncated,
                                model=model,
                            )
                            yielded += 1
                            if max_entries > 0 and yielded >= max_entries:
                                return
                        entry_index += 1

                    elif btype == "tool_use":
                        # BUG-257-TRS-002: Use default=str to prevent TypeError on non-serializable inputs
                        try:
                            full_input = json.dumps(block.get("input", {}), default=str)
                        except (TypeError, ValueError):
                            full_input = str(block.get("input", {}))[:500]
                        text, truncated = _truncate(full_input, content_limit)
                        tool_name = block.get("name", "")
                        if entry_index >= start_index:
                            yield TranscriptEntry(
                                index=entry_index,
                                timestamp=ts_raw,
                                entry_type="tool_use",
                                content=text,
                                content_length=len(full_input),
                                is_truncated=truncated,
                                tool_name=tool_name,
                                tool_use_id=block.get("id"),
                                is_mcp=tool_name.startswith("mcp__"),
                                model=model,
                            )
                            yielded += 1
                            if max_entries > 0 and yielded >= max_entries:
                                return
                        entry_index += 1

                    elif btype == "thinking" and include_thinking:
                        think_text = block.get("thinking", "")
                        text, truncated = _truncate(think_text, content_limit)
                        if entry_index >= start_index:
                            yield TranscriptEntry(
                                index=entry_index,
                                timestamp=ts_raw,
                                entry_type="thinking",
                                content=text,
                                content_length=len(think_text),
                                is_truncated=truncated,
                                model=model,
                            )
                            yielded += 1
                            if max_entries > 0 and yielded >= max_entries:
                                return
                        entry_index += 1
    finally:
        f.close()


def build_synthetic_transcript(
    session_data: Dict[str, Any], page: int = 1, per_page: int = 50,
    include_thinking: bool = True, content_limit: int = _DEFAULT_CONTENT_LIMIT,
) -> Dict[str, Any]:
    """Build transcript from in-memory _sessions_store data (Chat/API sessions)."""
    entries: list[TranscriptEntry] = []
    for call in session_data.get("tool_calls", []):
        ts, name = call.get("timestamp", ""), call.get("tool_name", "unknown")
        inp = json.dumps(call.get("arguments", {}))
        text, trunc = _truncate(inp, content_limit)
        entries.append(TranscriptEntry(
            index=0, timestamp=ts, entry_type="tool_use",
            content=text, content_length=len(inp), is_truncated=trunc,
            tool_name=name, is_mcp=name.startswith("mcp__"),
        ))
        res = call.get("result", "") or ""
        text, trunc = _truncate(res, content_limit)
        entries.append(TranscriptEntry(
            index=0, timestamp=ts, entry_type="tool_result",
            content=text, content_length=len(res), is_truncated=trunc,
            tool_name=name, is_error=not call.get("success", True),
        ))
    if include_thinking:
        for th in session_data.get("thoughts", []):
            txt = th.get("thought", "")
            text, trunc = _truncate(txt, content_limit)
            entries.append(TranscriptEntry(
                index=0, timestamp=th.get("timestamp", ""), entry_type="thinking",
                content=text, content_length=len(txt), is_truncated=trunc,
            ))
    entries.sort(key=lambda e: e.timestamp)
    for i, entry in enumerate(entries):
        entry.index = i
    total = len(entries)
    # BUG-257-TRS-003: Validate page to prevent negative start index
    page = max(1, page)
    start = (page - 1) * per_page
    return {
        "entries": [e.to_dict() for e in entries[start:start + per_page]],
        "total": total, "page": page, "per_page": per_page,
        "has_more": (start + per_page) < total, "source": "synthetic",
    }


def get_transcript_page(
    filepath: Path,
    page: int = 1,
    per_page: int = 50,
    include_thinking: bool = True,
    include_user_content: bool = True,
    content_limit: int = _DEFAULT_CONTENT_LIMIT,
) -> Dict[str, Any]:
    """Get a paginated page of transcript entries.

    Returns dict with entries, total, page, per_page, has_more.
    """
    # BUG-257-TRS-003: Validate page to prevent negative start index
    page = max(1, page)
    start_index = (page - 1) * per_page
    entries = []
    total_count = 0

    for entry in stream_transcript(
        filepath,
        include_thinking=include_thinking,
        include_user_content=include_user_content,
        content_limit=content_limit,
    ):
        total_count += 1
        if total_count > start_index and len(entries) < per_page:
            entries.append(entry.to_dict())

    return {
        "entries": entries,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "has_more": (start_index + per_page) < total_count,
    }
