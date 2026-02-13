"""JSONL log file discovery and streaming parser (SESSION-METRICS-01-v1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from governance.session_metrics.models import ParsedEntry, ToolResultInfo, ToolUseInfo


def discover_log_files(
    directory: Path, include_agents: bool = True
) -> list[Path]:
    """Discover JSONL log files in a Claude Code project directory.

    Args:
        directory: Path to search for .jsonl files.
        include_agents: If False, exclude agent-*.jsonl files.

    Returns:
        List of Path objects sorted by modification time (newest first).
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    files = list(directory.glob("*.jsonl"))

    if not include_agents:
        files = [f for f in files if not f.name.startswith("agent-")]

    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def _parse_timestamp(raw: str) -> datetime:
    """Parse ISO 8601 timestamp, handling Z suffix."""
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    return datetime.fromisoformat(raw)


def _extract_text_content(content: list) -> str | None:
    """Extract concatenated text blocks from message content."""
    texts = []
    if not isinstance(content, list):
        return None
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            texts.append(block.get("text", ""))
    return "\n".join(texts) if texts else None


def _extract_tool_uses(content: list) -> list[ToolUseInfo]:
    """Extract tool_use blocks from message content."""
    tools = []
    if not isinstance(content, list):
        return tools
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            tools.append(ToolUseInfo.from_content_block(block))
    return tools


def _extract_tool_results(content: list, mcp_meta: dict | None) -> list[ToolResultInfo]:
    """Extract tool_result blocks from message content."""
    results = []
    if not isinstance(content, list):
        return results
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            tool_use_id = block.get("tool_use_id", "")
            server_name = None
            if mcp_meta and isinstance(mcp_meta, dict):
                server_name = mcp_meta.get("serverName")
            results.append(ToolResultInfo(
                tool_use_id=tool_use_id,
                server_name=server_name,
            ))
    return results


def _extract_thinking(content: list, include: bool) -> tuple[int, str | None]:
    """Extract thinking block stats from message content.

    Returns:
        (char_count, content_or_none)
    """
    total_chars = 0
    full_text = []
    if not isinstance(content, list):
        return 0, None
    for block in content:
        if isinstance(block, dict) and block.get("type") == "thinking":
            text = block.get("thinking", "")
            total_chars += len(text)
            if include:
                full_text.append(text)
    content_str = "\n".join(full_text) if include and full_text else None
    return total_chars, content_str


def parse_log_file(
    filepath: Path, include_thinking: bool = False
) -> Generator[ParsedEntry, None, None]:
    """Stream-parse a JSONL log file into ParsedEntry objects.

    Args:
        filepath: Path to the .jsonl file.
        include_thinking: If True, include thinking block content.

    Yields:
        ParsedEntry for each valid line.
    """
    filepath = Path(filepath)
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_raw = obj.get("timestamp")
            if not ts_raw:
                continue

            try:
                timestamp = _parse_timestamp(ts_raw)
            except (ValueError, TypeError):
                continue

            entry_type = obj.get("type", "unknown")
            msg = obj.get("message", {})
            content = msg.get("content", []) if isinstance(msg, dict) else []

            # Tool uses (from assistant content blocks)
            tool_uses = _extract_tool_uses(content)

            # Tool results (from user content blocks, with mcpMeta)
            mcp_meta = obj.get("mcpMeta")
            tool_results = _extract_tool_results(content, mcp_meta)

            # Thinking
            thinking_chars, thinking_content = _extract_thinking(
                content, include_thinking
            )

            # Compaction detection
            is_compaction = (
                entry_type == "system"
                and obj.get("compactMetadata") is not None
            )

            # API error detection
            is_api_error = obj.get("isApiErrorMessage", False) is True

            # Model
            model = msg.get("model") if isinstance(msg, dict) else None

            # Text content (assistant text blocks, not privacy-sensitive)
            text_content = _extract_text_content(content)

            yield ParsedEntry(
                timestamp=timestamp,
                entry_type=entry_type,
                tool_uses=tool_uses,
                tool_results=tool_results,
                thinking_chars=thinking_chars,
                thinking_content=thinking_content,
                user_content=None,  # Privacy: never store
                is_compaction=is_compaction,
                is_api_error=is_api_error,
                model=model,
                text_content=text_content,
            )


def parse_log_file_extended(
    filepath: Path, include_thinking: bool = True, start_line: int = 0
) -> Generator[ParsedEntry, None, None]:
    """Extended parser that also extracts session_id, git_branch, text_content.

    This variant populates the extended fields on ParsedEntry for use
    with the search module. Includes thinking by default for searchability.

    Args:
        filepath: Path to the .jsonl file.
        include_thinking: If True, include thinking block content.
        start_line: Skip lines before this offset (for resume support).

    Yields:
        ParsedEntry with extended fields populated.
    """
    filepath = Path(filepath)
    with open(filepath, "r") as f:
        for line_num, line in enumerate(f):
            if line_num < start_line:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_raw = obj.get("timestamp")
            if not ts_raw:
                continue

            try:
                timestamp = _parse_timestamp(ts_raw)
            except (ValueError, TypeError):
                continue

            entry_type = obj.get("type", "unknown")
            msg = obj.get("message", {})
            content = msg.get("content", []) if isinstance(msg, dict) else []

            tool_uses = _extract_tool_uses(content)
            mcp_meta = obj.get("mcpMeta")
            tool_results = _extract_tool_results(content, mcp_meta)
            thinking_chars, thinking_content = _extract_thinking(
                content, include_thinking
            )
            is_compaction = (
                entry_type == "system"
                and obj.get("compactMetadata") is not None
            )
            is_api_error = obj.get("isApiErrorMessage", False) is True
            model = msg.get("model") if isinstance(msg, dict) else None

            # Extended fields
            session_id = obj.get("sessionId")
            git_branch = obj.get("gitBranch")
            text_content = _extract_text_content(content)

            yield ParsedEntry(
                timestamp=timestamp,
                entry_type=entry_type,
                tool_uses=tool_uses,
                tool_results=tool_results,
                thinking_chars=thinking_chars,
                thinking_content=thinking_content,
                user_content=None,
                is_compaction=is_compaction,
                is_api_error=is_api_error,
                model=model,
                session_id=session_id,
                git_branch=git_branch,
                text_content=text_content,
            )
