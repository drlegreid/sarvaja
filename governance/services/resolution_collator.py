"""Resolution Collator — Auto-generate resolution summary from linked data.

Per EPIC-TASK-QUALITY-V3 Phase 17: Issue Resolution Evidence Trail.
Per EPIC-TASK-TAXONOMY-V2 Session 3: Type-specific resolution templates.
Builds a markdown summary from linked sessions, documents, and commits.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# TYPE-SPECIFIC RESOLUTION TEMPLATES (EPIC-TASK-TAXONOMY-V2 Session 3)
# =============================================================================
# Each template is a list of (section_title, data_key, fallback_text) tuples.
# data_key maps to task_data fields or special keys handled in the builder.

TYPE_RESOLUTION_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "bug": [
        {"title": "Root Cause", "key": "evidence", "fallback": "Not documented"},
        {"title": "Fix Applied", "key": "linked_commits", "fallback": "No commits linked"},
        {"title": "Regression Test", "key": "_evidence_test", "fallback": "No test evidence"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
    "feature": [
        {"title": "Requirements Met", "key": "linked_documents", "fallback": "No documents linked"},
        {"title": "Files Changed", "key": "linked_commits", "fallback": "No commits linked"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
    "chore": [
        {"title": "What Changed", "key": "linked_commits", "fallback": "No commits linked"},
        {"title": "Why", "key": "evidence", "fallback": "Not documented"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
    "research": [
        {"title": "Findings", "key": "evidence", "fallback": "No findings documented"},
        {"title": "Recommendation", "key": "_recommendation", "fallback": "No recommendation provided"},
        {"title": "Documents", "key": "linked_documents", "fallback": "No documents linked"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
    "spec": [
        {"title": "Spec Document", "key": "linked_documents", "fallback": "No documents linked"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
    "test": [
        {"title": "Test Results", "key": "evidence", "fallback": "No test results documented"},
        {"title": "Coverage", "key": "_coverage", "fallback": "Coverage data not available"},
        {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions linked"},
    ],
}


def _render_session_list(
    session_ids: List[str],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Render linked sessions as markdown bullet list."""
    if not session_ids:
        return []
    lines = []
    meta_map = {s.get("session_id"): s for s in (session_metadata or [])}
    for sid in session_ids:
        meta = meta_map.get(sid)
        if meta:
            desc = meta.get("description") or meta.get("topic") or "N/A"
            duration = meta.get("duration") or ""
            suffix = f" ({duration})" if duration else ""
            lines.append(f"- {sid}: {desc}{suffix}")
        else:
            lines.append(f"- {sid}")
    return lines


def _render_template_section(
    section: Dict[str, str],
    task_data: Dict[str, Any],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Render a single template section to markdown lines."""
    key = section["key"]
    title = section["title"]
    fallback = section["fallback"]

    # Special keys with custom rendering
    if key == "linked_sessions":
        items = task_data.get("linked_sessions") or []
        if items:
            return [f"### {title}"] + _render_session_list(items, session_metadata) + [""]
        return [f"### {title}", fallback, ""]

    if key == "linked_commits":
        items = task_data.get("linked_commits") or []
        if items:
            return [f"### {title}"] + [f"- {sha}" for sha in items] + [""]
        return [f"### {title}", fallback, ""]

    if key == "linked_documents":
        items = task_data.get("linked_documents") or []
        if items:
            return [f"### {title}"] + [f"- {doc}" for doc in items] + [""]
        return [f"### {title}", fallback, ""]

    if key == "evidence":
        val = task_data.get("evidence")
        if val:
            return [f"### {title}", str(val), ""]
        return [f"### {title}", fallback, ""]

    # Special computed keys — fallback only (data not yet available)
    if key.startswith("_"):
        return [f"### {title}", fallback, ""]

    # Generic string field
    val = task_data.get(key)
    if val:
        return [f"### {title}", str(val), ""]
    return [f"### {title}", fallback, ""]


def build_resolution_summary(
    task_data: Dict[str, Any],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Build markdown resolution summary from task's linked data.

    Per EPIC-TASK-TAXONOMY-V2 Session 3: Uses type-specific templates when
    task_type is set and has a template. Falls back to generic summary.

    Args:
        task_data: Task dict from _tasks_store (has linked_sessions, etc.)
        session_metadata: Optional pre-fetched session metadata dicts.
            Each dict should have: session_id, description, duration.

    Returns:
        Markdown string summarizing the resolution context.
    """
    task_type = task_data.get("task_type")
    template = TYPE_RESOLUTION_TEMPLATES.get(task_type) if task_type else None

    if template:
        return _build_typed_summary(task_data, template, session_metadata)
    return _build_generic_summary(task_data, session_metadata)


def _build_typed_summary(
    task_data: Dict[str, Any],
    template: List[Dict[str, str]],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Build resolution summary using a type-specific template."""
    task_type = task_data.get("task_type", "unknown")
    parts = [f"## Resolution Summary ({task_type})\n"]

    for section in template:
        parts.extend(_render_template_section(section, task_data, session_metadata))

    if len(parts) == 1:
        return "Task completed."
    return "\n".join(parts).strip()


def _build_generic_summary(
    task_data: Dict[str, Any],
    session_metadata: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Build generic resolution summary (original behavior)."""
    parts = ["## Resolution Summary\n"]

    # Sessions section
    linked_sessions = task_data.get("linked_sessions") or []
    if linked_sessions:
        parts.append("### Sessions")
        parts.extend(_render_session_list(linked_sessions, session_metadata))
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
