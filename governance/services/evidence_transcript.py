"""
Evidence file transcript parser (GAP-SESSION-TRANSCRIPT-001).

Parses evidence .md files into TranscriptEntry objects as a fallback
when no JSONL or _sessions_store data is available.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.session_metrics.models import TranscriptEntry

logger = logging.getLogger(__name__)

# Evidence directory relative to project root
_EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence"

# Regex for Event Timeline lines
_TOOL_CALL_RE = re.compile(
    r"- 🔧 \*\*TOOL_CALL\*\* \(([^)]+)\): (.+)"
)
_THOUGHT_RE = re.compile(
    r"- 💭 \*\*THOUGHT\*\* \(([^)]+)\): (.+)"
)

# Regex for Tool Calls table rows
_TABLE_ROW_RE = re.compile(
    r"\|\s*(.+?)\s*\|\s*(✅|❌)\s*\|\s*(.+?)\s*\|"
)


def find_evidence_file(session_id: str) -> Optional[Path]:
    """Find evidence markdown file matching session_id."""
    if not _EVIDENCE_DIR.is_dir():
        return None
    candidate = _EVIDENCE_DIR / f"{session_id}.md"
    if candidate.is_file():
        return candidate
    # Fuzzy: scan for files containing session_id
    for f in _EVIDENCE_DIR.iterdir():
        if f.suffix == ".md" and session_id in f.stem:
            return f
    return None


def _parse_tool_success_map(text: str) -> Dict[str, bool]:
    """Parse the Tool Calls table into a tool_name → success map."""
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        match = _TABLE_ROW_RE.match(line)
        if not match:
            continue
        tool_name = match.group(1).strip()
        success = match.group(2) == "✅"
        if tool_name and tool_name not in ("Tool", ""):
            result[tool_name] = success
    return result


def parse_evidence_transcript(
    filepath: Path,
    page: int = 1,
    per_page: int = 50,
    include_thinking: bool = True,
    content_limit: int = 2000,
) -> Dict[str, Any]:
    """Parse evidence .md file into transcript format.

    Extracts tool calls and thoughts from the Event Timeline section.
    Falls back to Tool Calls table if no timeline found.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    entries: List[TranscriptEntry] = []

    # Build success map from table
    success_map = _parse_tool_success_map(text)

    # Parse Event Timeline (preferred — has timestamps)
    timeline_entries = _parse_event_timeline(text, success_map, include_thinking)
    if timeline_entries:
        entries = timeline_entries
    else:
        # Fallback: parse Tool Calls table + Key Thoughts sections
        entries = _parse_table_and_thoughts(text, success_map, include_thinking)

    # Apply truncation
    for entry in entries:
        if content_limit and entry.content_length > content_limit:
            entry.content = (
                entry.content[:content_limit]
                + f"\n... [{entry.content_length - content_limit} chars truncated]"
            )
            entry.is_truncated = True

    # Re-index and paginate
    for i, entry in enumerate(entries):
        entry.index = i
    total = len(entries)
    start = (page - 1) * per_page
    page_entries = entries[start:start + per_page]

    return {
        "entries": [e.to_dict() for e in page_entries],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": (start + per_page) < total,
        "source": "evidence",
    }


def _parse_event_timeline(
    text: str, success_map: Dict[str, bool], include_thinking: bool,
) -> List[TranscriptEntry]:
    """Parse the ## Event Timeline section."""
    entries: List[TranscriptEntry] = []

    for match in _TOOL_CALL_RE.finditer(text):
        timestamp = match.group(1).strip()
        detail = match.group(2).strip().rstrip(".")
        # Extract tool name: "/status()" or "heuristic/H-TASK-001(domain=TASK)"
        tool_name = detail.split("(")[0] if "(" in detail else detail
        is_error = not success_map.get(tool_name, True)
        entries.append(TranscriptEntry(
            index=0, timestamp=timestamp, entry_type="tool_use",
            content=detail, content_length=len(detail),
            tool_name=tool_name, is_error=is_error,
            is_mcp=tool_name.startswith("mcp__"),
        ))

    if include_thinking:
        for match in _THOUGHT_RE.finditer(text):
            timestamp = match.group(1).strip()
            thought = match.group(2).strip().rstrip(".")
            entries.append(TranscriptEntry(
                index=0, timestamp=timestamp, entry_type="thinking",
                content=thought, content_length=len(thought),
            ))

    entries.sort(key=lambda e: e.timestamp)
    return entries


def _parse_table_and_thoughts(
    text: str, success_map: Dict[str, bool], include_thinking: bool,
) -> List[TranscriptEntry]:
    """Parse Tool Calls table + Key Thoughts when no timeline found."""
    entries: List[TranscriptEntry] = []

    for tool_name, success in success_map.items():
        entries.append(TranscriptEntry(
            index=0, timestamp="", entry_type="tool_use",
            content=tool_name, content_length=len(tool_name),
            tool_name=tool_name, is_error=not success,
            is_mcp=tool_name.startswith("mcp__"),
        ))

    if include_thinking:
        # Parse Key Thoughts: lines starting with > after ### headers
        in_thoughts = False
        for line in text.split("\n"):
            if line.startswith("## Key Thoughts"):
                in_thoughts = True
                continue
            if in_thoughts and line.startswith("## "):
                break
            if in_thoughts and line.startswith("> "):
                thought = line[2:].strip()
                if thought:
                    entries.append(TranscriptEntry(
                        index=0, timestamp="", entry_type="thinking",
                        content=thought, content_length=len(thought),
                    ))

    return entries
