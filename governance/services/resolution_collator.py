"""Resolution Collator — Auto-generate resolution summary from linked data.

Per EPIC-TASK-QUALITY-V3 Phase 17: Issue Resolution Evidence Trail.
Builds a markdown summary from linked sessions, documents, and commits.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def build_resolution_summary(
    task_data: Dict[str, Any],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Build markdown resolution summary from task's linked data.

    Args:
        task_data: Task dict from _tasks_store (has linked_sessions, etc.)
        session_metadata: Optional pre-fetched session metadata dicts.
            Each dict should have: session_id, description, duration.

    Returns:
        Markdown string summarizing the resolution context.
    """
    parts = ["## Resolution Summary\n"]

    # Sessions section
    linked_sessions = task_data.get("linked_sessions") or []
    if linked_sessions:
        parts.append("### Sessions")
        if session_metadata:
            meta_map = {s.get("session_id"): s for s in session_metadata}
        else:
            meta_map = {}
        for sid in linked_sessions:
            meta = meta_map.get(sid)
            if meta:
                desc = meta.get("description") or meta.get("topic") or "N/A"
                duration = meta.get("duration") or ""
                suffix = f" ({duration})" if duration else ""
                parts.append(f"- {sid}: {desc}{suffix}")
            else:
                parts.append(f"- {sid}")
        parts.append("")

    # Documents section
    linked_documents = task_data.get("linked_documents") or []
    if linked_documents:
        parts.append("### Linked Documents")
        for doc in linked_documents:
            parts.append(f"- {doc}")
        parts.append("")

    # Commits section
    linked_commits = task_data.get("linked_commits") or []
    if linked_commits:
        parts.append("### Commits")
        for sha in linked_commits:
            parts.append(f"- {sha}")
        parts.append("")

    # Evidence section
    evidence = task_data.get("evidence")
    if evidence:
        parts.append("### Evidence")
        parts.append(str(evidence))
        parts.append("")

    # If nothing to summarize, return minimal note
    if len(parts) == 1:
        return "Task completed."

    return "\n".join(parts).strip()


def fetch_session_metadata(
    session_ids: List[str],
) -> List[Dict[str, Any]]:
    """Fetch lightweight metadata for sessions from the store.

    Uses in-memory store first, falls back gracefully.
    Does NOT make HTTP calls — uses store data only.
    """
    from governance.stores import _sessions_store

    results = []
    for sid in session_ids:
        session_data = _sessions_store.get(sid)
        if session_data:
            results.append({
                "session_id": sid,
                "description": session_data.get("description") or session_data.get("topic"),
                "duration": session_data.get("duration"),
                "agent_id": session_data.get("agent_id"),
            })
        else:
            results.append({"session_id": sid})
    return results
