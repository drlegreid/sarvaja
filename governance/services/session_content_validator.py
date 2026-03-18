"""Session content validator — deep JSONL integrity checks.

Validates real Claude Code session JSONL data for:
- Tool call / tool result pairing (orphaned calls, missing results)
- MCP tool calls with server metadata
- Thinking blocks with actual content
- Timestamp consistency and ordering
- Session completeness metrics

Per TEST-E2E-01-v1: Content-level validation of CC session data.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A single validation finding."""

    check: str  # e.g. "tool_call_result_pairing", "mcp_server_metadata"
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"check": self.check, "severity": self.severity, "message": self.message}
        if self.line_number is not None:
            d["line_number"] = self.line_number
        return d


@dataclass
class ContentValidationResult:
    """Aggregated result from validating a JSONL session file."""

    valid: bool = True
    entry_count: int = 0
    parse_errors: int = 0

    # Message counts
    user_messages: int = 0
    assistant_messages: int = 0

    # Tool call metrics
    tool_calls_total: int = 0
    tool_results_total: int = 0
    orphaned_tool_calls: int = 0
    orphaned_tool_results: int = 0
    tool_errors: int = 0

    # MCP metrics
    mcp_calls_total: int = 0
    mcp_calls_with_server: int = 0
    mcp_calls_without_server: int = 0
    mcp_server_distribution: dict[str, int] = field(default_factory=dict)

    # Thinking metrics
    thinking_blocks_total: int = 0
    thinking_blocks_empty: int = 0
    thinking_chars_total: int = 0

    # Issues
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_user_messages(self) -> bool:
        return self.user_messages > 0

    @property
    def has_assistant_messages(self) -> bool:
        return self.assistant_messages > 0

    @property
    def has_tool_calls(self) -> bool:
        return self.tool_calls_total > 0

    @property
    def has_thinking(self) -> bool:
        return self.thinking_blocks_total > 0

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "entry_count": self.entry_count,
            "parse_errors": self.parse_errors,
            "user_messages": self.user_messages,
            "assistant_messages": self.assistant_messages,
            "tool_calls_total": self.tool_calls_total,
            "tool_results_total": self.tool_results_total,
            "orphaned_tool_calls": self.orphaned_tool_calls,
            "orphaned_tool_results": self.orphaned_tool_results,
            "tool_errors": self.tool_errors,
            "mcp_calls_total": self.mcp_calls_total,
            "mcp_calls_with_server": self.mcp_calls_with_server,
            "mcp_calls_without_server": self.mcp_calls_without_server,
            "mcp_server_distribution": dict(self.mcp_server_distribution),
            "thinking_blocks_total": self.thinking_blocks_total,
            "thinking_blocks_empty": self.thinking_blocks_empty,
            "thinking_chars_total": self.thinking_chars_total,
            "has_user_messages": self.has_user_messages,
            "has_assistant_messages": self.has_assistant_messages,
            "has_tool_calls": self.has_tool_calls,
            "has_thinking": self.has_thinking,
            "issues": [i.to_dict() for i in self.issues],
        }


def validate_session_content(jsonl_path: str) -> ContentValidationResult:
    """Validate a Claude Code session JSONL file for content integrity.

    Parses the JSONL file and checks:
    1. Tool call / result pairing (every tool_use has a tool_result and vice versa)
    2. MCP tool calls have server metadata (mcpMeta.serverName)
    3. Thinking blocks have actual content (not empty strings)
    4. Timestamps are present and monotonically ordered
    5. Tool results are not empty

    Args:
        jsonl_path: Path to the JSONL session file.

    Returns:
        ContentValidationResult with metrics and issues.
    """
    result = ContentValidationResult()
    path = Path(jsonl_path)

    if not path.exists():
        result.valid = False
        result.issues.append(ValidationIssue(
            check="file_exists", severity="error",
            message=f"Session file not found: {jsonl_path}",
        ))
        return result

    # Parse all entries
    entries = _parse_jsonl(path, result)

    if not entries:
        result.issues.append(ValidationIssue(
            check="empty_session", severity="warning",
            message="Empty session file — no JSONL entries found",
        ))
        return result

    # Track tool_use IDs and their names for pairing
    tool_use_ids: dict[str, str] = {}  # id -> tool_name
    tool_result_ids: set[str] = set()
    # Track MCP tool_use IDs for server metadata correlation
    mcp_tool_use_ids: dict[str, str] = {}  # id -> tool_name
    mcp_result_servers: dict[str, str | None] = {}  # tool_use_id -> server_name

    prev_timestamp: str | None = None

    for line_num, entry in entries:
        entry_type = entry.get("type", "")
        timestamp = entry.get("timestamp")

        # Timestamp validation
        if not timestamp:
            result.issues.append(ValidationIssue(
                check="missing_timestamp", severity="warning",
                message=f"Entry at line {line_num} has no timestamp",
                line_number=line_num,
            ))
        elif prev_timestamp and timestamp < prev_timestamp:
            result.issues.append(ValidationIssue(
                check="timestamp_order", severity="info",
                message=f"Timestamp at line {line_num} goes backwards: {timestamp} < {prev_timestamp}",
                line_number=line_num,
            ))
        if timestamp:
            prev_timestamp = timestamp

        if entry_type == "assistant":
            result.assistant_messages += 1
            _process_assistant_entry(entry, line_num, result, tool_use_ids, mcp_tool_use_ids)

        elif entry_type == "user":
            result.user_messages += 1
            _process_user_entry(entry, line_num, result, tool_result_ids, mcp_result_servers)

    # Pairing analysis
    _analyze_pairing(result, tool_use_ids, tool_result_ids)
    _analyze_mcp_metadata(result, mcp_tool_use_ids, mcp_result_servers)

    return result


def _parse_jsonl(
    path: Path, result: ContentValidationResult,
) -> list[tuple[int, dict]]:
    """Parse JSONL file, collecting entries and tracking parse errors."""
    entries = []
    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                entries.append((line_num, obj))
                result.entry_count += 1
            except json.JSONDecodeError:
                result.parse_errors += 1
                result.issues.append(ValidationIssue(
                    check="json_parse", severity="warning",
                    message=f"Malformed JSON at line {line_num}",
                    line_number=line_num,
                ))
    return entries


def _process_assistant_entry(
    entry: dict,
    line_num: int,
    result: ContentValidationResult,
    tool_use_ids: dict[str, str],
    mcp_tool_use_ids: dict[str, str],
) -> None:
    """Extract tool_use and thinking blocks from assistant entry."""
    message = entry.get("message", {})
    content = message.get("content", [])
    if not isinstance(content, list):
        return

    for block in content:
        block_type = block.get("type", "")

        if block_type == "tool_use":
            tool_id = block.get("id", "")
            tool_name = block.get("name", "")
            result.tool_calls_total += 1
            if tool_id:
                tool_use_ids[tool_id] = tool_name
            if tool_name.startswith("mcp__"):
                result.mcp_calls_total += 1
                if tool_id:
                    mcp_tool_use_ids[tool_id] = tool_name

        elif block_type == "thinking":
            thinking_text = block.get("thinking", "")
            result.thinking_blocks_total += 1
            result.thinking_chars_total += len(thinking_text)
            if not thinking_text:
                result.thinking_blocks_empty += 1
                result.issues.append(ValidationIssue(
                    check="empty_thinking", severity="info",
                    message=f"Empty thinking block at line {line_num}",
                    line_number=line_num,
                ))


def _process_user_entry(
    entry: dict,
    line_num: int,
    result: ContentValidationResult,
    tool_result_ids: set[str],
    mcp_result_servers: dict[str, str | None],
) -> None:
    """Extract tool_result blocks from user entry."""
    message = entry.get("message", {})
    content = message.get("content", [])
    if not isinstance(content, list):
        return

    mcp_meta = entry.get("mcpMeta", {}) or {}
    server_name = mcp_meta.get("serverName")

    for block in content:
        if block.get("type") != "tool_result":
            continue
        tool_use_id = block.get("tool_use_id", "")
        result.tool_results_total += 1
        if tool_use_id:
            tool_result_ids.add(tool_use_id)
            mcp_result_servers[tool_use_id] = server_name

        # Check for empty content
        result_content = block.get("content", "")
        if isinstance(result_content, list):
            text_parts = [p.get("text", "") for p in result_content if isinstance(p, dict)]
            result_content = "".join(text_parts)
        if not result_content:
            result.issues.append(ValidationIssue(
                check="empty_tool_result", severity="info",
                message=f"Tool result for {tool_use_id} has empty content at line {line_num}",
                line_number=line_num,
            ))

        # Check for errors
        if block.get("is_error"):
            result.tool_errors += 1


def _analyze_pairing(
    result: ContentValidationResult,
    tool_use_ids: dict[str, str],
    tool_result_ids: set[str],
) -> None:
    """Identify orphaned tool calls and tool results."""
    for tool_id, tool_name in tool_use_ids.items():
        if tool_id not in tool_result_ids:
            result.orphaned_tool_calls += 1
            result.issues.append(ValidationIssue(
                check="tool_call_result_pairing", severity="warning",
                message=f"Tool call {tool_id} ({tool_name}) has no matching result",
            ))

    for tool_id in tool_result_ids:
        if tool_id not in tool_use_ids:
            result.orphaned_tool_results += 1
            result.issues.append(ValidationIssue(
                check="tool_call_result_pairing", severity="warning",
                message=f"Tool result {tool_id} has no matching tool call",
            ))


def _derive_server_from_tool_name(tool_name: str) -> str | None:
    """Extract MCP server name from tool name convention.

    Example: "mcp__gov-core__rules_query" → "gov-core"
    """
    if not tool_name.startswith("mcp__"):
        return None
    parts = tool_name.split("__", 2)
    return parts[1] if len(parts) >= 3 else None


def _analyze_mcp_metadata(
    result: ContentValidationResult,
    mcp_tool_use_ids: dict[str, str],
    mcp_result_servers: dict[str, str | None],
) -> None:
    """Check MCP tool calls have server metadata and build distribution.

    Resolves server name from: (1) mcpMeta.serverName in tool_result,
    or (2) tool name convention (mcp__{server}__{method}).
    """
    for tool_id, tool_name in mcp_tool_use_ids.items():
        server = mcp_result_servers.get(tool_id)
        # Fallback: derive from tool name convention
        if not server:
            server = _derive_server_from_tool_name(tool_name)
        if server:
            result.mcp_calls_with_server += 1
            result.mcp_server_distribution[server] = (
                result.mcp_server_distribution.get(server, 0) + 1
            )
        else:
            result.mcp_calls_without_server += 1
            result.issues.append(ValidationIssue(
                check="mcp_server_metadata", severity="info",
                message=f"MCP call {tool_name} ({tool_id}) has no server metadata",
            ))
