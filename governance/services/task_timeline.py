"""Task Timeline Service — Multi-session chronological event merge.

Per EPIC-ISSUE-EVIDENCE P18: Merge tool calls, thoughts, and decisions
from all linked sessions into a single chronological timeline.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Icon / color mapping for timeline entry types
# ---------------------------------------------------------------------------

_ENTRY_STYLE: Dict[str, Dict[str, str]] = {
    "tool_call": {"icon": "mdi-wrench", "color": "primary"},
    "thought": {"icon": "mdi-head-cog", "color": "info"},
    "decision": {"icon": "mdi-scale-balance", "color": "warning"},
    "status_change": {"icon": "mdi-swap-horizontal", "color": "success"},
}

_DEFAULT_STYLE = {"icon": "mdi-circle", "color": "grey"}

# Max detail text length to avoid oversized payloads
_DETAIL_TRUNCATE = 200


def build_task_timeline(
    task_id: str,
    page: int = 1,
    per_page: int = 50,
    entry_types: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Build chronological timeline from all sessions linked to a task.

    Args:
        task_id: Task to build timeline for.
        page: Page number (1-based).
        per_page: Items per page (max 100).
        entry_types: Filter to specific types (tool_call, thought, etc.).

    Returns:
        Dict with entries, total, page, per_page, has_more, session_ids.
        None if task not found.
    """
    from governance.services.tasks_queries import get_task

    task = get_task(task_id)
    if not task:
        return None

    # Get linked session IDs
    if hasattr(task, "linked_sessions"):
        session_ids = task.linked_sessions or []
    else:
        session_ids = task.get("linked_sessions") or []

    # Collect entries from all sessions
    all_entries: List[Dict[str, Any]] = []
    for sid in session_ids:
        all_entries.extend(_collect_session_entries(sid))

    # Sort chronologically
    all_entries.sort(key=lambda e: e.get("timestamp") or "")

    # Apply entry_types filter
    if entry_types:
        allowed = set(entry_types)
        all_entries = [e for e in all_entries if e["entry_type"] in allowed]

    # Paginate
    per_page = max(1, min(per_page, 100))
    total = len(all_entries)
    start = max(0, (page - 1) * per_page)
    paginated = all_entries[start:start + per_page]

    return {
        "task_id": task_id,
        "entries": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": (start + len(paginated)) < total,
        "session_ids": list(session_ids),
    }


def _collect_session_entries(session_id: str) -> List[Dict[str, Any]]:
    """Collect timeline entries from a single session.

    Uses get_session_detail at zoom=2 for tool_calls and zoom=3
    for thinking_blocks. Falls back gracefully if session has no JSONL.
    """
    entries: List[Dict[str, Any]] = []
    try:
        from governance.services.cc_session_ingestion import get_session_detail

        # zoom=2: tool calls
        detail = get_session_detail(session_id, zoom=2, page=1, per_page=500)
        if detail:
            for tc in detail.get("tool_calls") or []:
                entries.append(_normalize_entry(tc, "tool_call", session_id))

        # zoom=3: thinking blocks
        detail3 = get_session_detail(session_id, zoom=3, page=1, per_page=500)
        if detail3:
            for tb in detail3.get("thinking_blocks") or []:
                entries.append(_normalize_entry(tb, "thought", session_id))

    except Exception as e:
        logger.debug("Failed to collect entries for %s: %s", session_id, e)

    return entries


def _normalize_entry(
    raw: Dict[str, Any],
    entry_type: str,
    session_id: str,
) -> Dict[str, Any]:
    """Normalize a raw tool_call or thinking_block to timeline schema."""
    style = _ENTRY_STYLE.get(entry_type, _DEFAULT_STYLE)

    if entry_type == "tool_call":
        title = raw.get("name") or raw.get("tool_name") or "Unknown Tool"
        detail = raw.get("input_summary") or raw.get("output_summary") or ""
        duration_ms = raw.get("latency_ms") or raw.get("duration_ms")
    elif entry_type == "thought":
        content = raw.get("content") or raw.get("thought") or ""
        title = f"Thinking ({raw.get('chars', len(content))} chars)"
        detail = content
        duration_ms = None
    else:
        title = raw.get("title") or entry_type
        detail = raw.get("detail") or ""
        duration_ms = raw.get("duration_ms")

    # Truncate detail
    if len(detail) > _DETAIL_TRUNCATE:
        detail = detail[:_DETAIL_TRUNCATE] + "..."

    return {
        "timestamp": raw.get("timestamp") or "",
        "entry_type": entry_type,
        "session_id": session_id,
        "title": title,
        "detail": detail,
        "duration_ms": duration_ms,
        "icon": style["icon"],
        "color": style["color"],
    }
