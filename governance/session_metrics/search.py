"""Content search engine for session logs (GAP-SESSION-METRICS-CONTENT).

Provides text search, session ID filtering, and git branch filtering
over ParsedEntry objects with extended fields.
"""

from __future__ import annotations

from governance.session_metrics.models import ParsedEntry


def _entry_matches_query(entry: ParsedEntry, query_lower: str) -> bool:
    """Check if any searchable content in the entry matches the query."""
    # Search in text_content (assistant text blocks)
    if entry.text_content and query_lower in entry.text_content.lower():
        return True
    # Search in thinking content
    if entry.thinking_content and query_lower in entry.thinking_content.lower():
        return True
    # Search in tool names
    for tu in entry.tool_uses:
        if query_lower in tu.name.lower():
            return True
        if query_lower in tu.input_summary.lower():
            return True
    return False


def search_entries(
    entries: list[ParsedEntry],
    query: str = "",
    session_id: str | None = None,
    git_branch: str | None = None,
    max_results: int = 0,
) -> list[ParsedEntry]:
    """Search and filter parsed entries.

    Args:
        entries: List of ParsedEntry objects (preferably from parse_log_file_extended).
        query: Text to search for (case-insensitive). Empty = match all.
        session_id: Filter to specific session ID.
        git_branch: Filter to specific git branch.
        max_results: Maximum results to return (0 = unlimited).

    Returns:
        List of matching ParsedEntry objects.
    """
    results = []
    query_lower = query.lower().strip()

    for entry in entries:
        # Session ID filter
        if session_id and entry.session_id != session_id:
            continue

        # Git branch filter
        if git_branch and entry.git_branch != git_branch:
            continue

        # Text search (empty query matches everything)
        if query_lower and not _entry_matches_query(entry, query_lower):
            continue

        results.append(entry)

        if max_results > 0 and len(results) >= max_results:
            break

    return results


def results_to_dicts(entries: list[ParsedEntry]) -> list[dict]:
    """Convert search results to JSON-serializable dicts."""
    output = []
    for e in entries:
        d = {
            "timestamp": e.timestamp.isoformat(),
            "entry_type": e.entry_type,
            "session_id": e.session_id,
            "git_branch": e.git_branch,
            "text_content": e.text_content,
            "model": e.model,
            "tool_uses": [tu.name for tu in e.tool_uses],
            "thinking_chars": e.thinking_chars,
        }
        output.append(d)
    return output
