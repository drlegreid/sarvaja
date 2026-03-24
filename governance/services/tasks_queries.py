"""Task Service Queries — read-only query, filter, and search operations.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
All read-only functions: list, get, search, filter helpers.
"""
import logging
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    get_all_tasks_from_typedb,
    _tasks_store,
    task_to_response,
)

logger = logging.getLogger(__name__)

__all__ = [
    "list_tasks",
    "get_task",
    "get_task_details",
    "get_sessions_for_task",
    "_apply_post_filters",
    "_date_gte",
    "_date_lte",
    "_detect_doc_type",
    "_parse_structured_search",
    "_apply_search",
    "_extract_priority_tag",
]


def list_tasks(
    status: Optional[str] = None,
    phase: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    completed_after: Optional[str] = None,
    completed_before: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    workspace_id: Optional[str] = None,
    sort_by: str = "task_id",
    order: str = "asc",
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """List tasks with pagination, sorting, filtering, and search.

    Filters: status, phase, agent_id (TypeDB-level), task_type, priority,
    created_after/before, completed_after/before, session_id (post-filter).
    Search: free text across task_id/description/summary/body/gap_id,
    with optional attribute-prefix syntax (type:bug priority:HIGH).

    Returns:
        Dict with 'items' (list of task dicts) and 'pagination' metadata.

    Raises:
        ConnectionError: If TypeDB unavailable and no fallback data.
    """
    # BUG-323-TASK-001: Clamp offset/limit to prevent negative indexing or unbounded fetch
    offset = max(0, offset)
    limit = max(1, min(limit, 500))
    tasks = get_all_tasks_from_typedb(
        status=status, phase=phase, agent_id=agent_id, allow_fallback=True
    )
    # Phase 9 post-filters: task_type, priority, date ranges
    tasks = _apply_post_filters(
        tasks, task_type=task_type, priority=priority,
        created_after=created_after, created_before=created_before,
        completed_after=completed_after, completed_before=completed_before,
        session_id=session_id, workspace_id=workspace_id,
    )
    # Phase 9d: Server-side search
    if search:
        tasks = _apply_search(tasks, search)
    total = len(tasks)
    sort_field = sort_by if sort_by in ("task_id", "status", "phase", "name", "priority", "created_at") else "task_id"
    tasks.sort(key=lambda t: t.get(sort_field) or "", reverse=order.lower() == "desc")
    paginated = tasks[offset: offset + limit]
    return {
        "items": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(paginated)) < total,
    }


def _apply_post_filters(
    tasks: List[Dict[str, Any]],
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    completed_after: Optional[str] = None,
    completed_before: Optional[str] = None,
    session_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Apply post-query filters for task_type, priority, date ranges, session_id, workspace_id."""
    if task_type:
        tasks = [t for t in tasks if t.get("task_type") == task_type]
    if priority:
        tasks = [t for t in tasks if t.get("priority") == priority]
    if created_after:
        tasks = [t for t in tasks if _date_gte(t.get("created_at"), created_after)]
    if created_before:
        tasks = [t for t in tasks if _date_lte(t.get("created_at"), created_before)]
    if completed_after:
        tasks = [t for t in tasks
                 if t.get("completed_at") and _date_gte(t["completed_at"], completed_after)]
    if completed_before:
        tasks = [t for t in tasks
                 if t.get("completed_at") and _date_lte(t["completed_at"], completed_before)]
    # Phase 9d: Filter by linked session
    if session_id:
        tasks = [t for t in tasks if session_id in (t.get("linked_sessions") or [])]
    # FIX-COL-006: Filter by workspace_id
    if workspace_id:
        tasks = [t for t in tasks if t.get("workspace_id") == workspace_id]
    return tasks


def _date_gte(date_val: Optional[str], threshold: str) -> bool:
    """Check if date_val >= threshold (ISO date string comparison)."""
    if not date_val:
        return False
    return str(date_val)[:10] >= threshold[:10]


def _date_lte(date_val: Optional[str], threshold: str) -> bool:
    """Check if date_val <= threshold (ISO date string comparison)."""
    if not date_val:
        return False
    return str(date_val)[:10] <= threshold[:10]


def _detect_doc_type(path: str) -> str:
    """Detect document type from file path. Phase 9d: Concern 2.

    Returns: 'evidence', 'plan', 'spec', 'log', or 'document'.
    """
    p = path.lower()
    if "evidence" in p:
        return "evidence"
    if "backlog/phases" in p or "plans/" in p or p.endswith("-plan.md"):
        return "plan"
    if "specs/" in p or "spec" in p and ".gherkin" in p:
        return "spec"
    if "log" in p and (p.endswith(".log") or "/logs/" in p):
        return "log"
    return "document"


def _parse_structured_search(query: str) -> tuple:
    """Parse attribute-prefix syntax from search query. Phase 9d: Concern 4.

    Extracts 'key:value' pairs and returns remaining free text.
    Supported prefixes: type, priority, status, phase, agent.

    Returns:
        (attrs_dict, remaining_text)
    """
    import re
    attrs = {}
    _VALID_PREFIXES = {"type", "priority", "status", "phase", "agent"}
    parts = []
    for token in query.split():
        match = re.match(r'^(\w+):(\S+)$', token)
        if match and match.group(1).lower() in _VALID_PREFIXES:
            attrs[match.group(1).lower()] = match.group(2)
        else:
            parts.append(token)
    return attrs, " ".join(parts)


def _apply_search(
    tasks: List[Dict[str, Any]],
    search: str,
) -> List[Dict[str, Any]]:
    """Server-side search across task fields. Phase 9d: Concern 4.

    Searches task_id, description, summary, body, gap_id (case-insensitive).
    Supports attribute-prefix syntax: 'type:bug priority:HIGH auth'.
    """
    if not search or not search.strip():
        return tasks
    attrs, free_text = _parse_structured_search(search.strip())
    # Apply structured attribute filters
    _ATTR_MAP = {
        "type": "task_type", "priority": "priority",
        "status": "status", "phase": "phase", "agent": "agent_id",
    }
    for prefix, value in attrs.items():
        field = _ATTR_MAP.get(prefix, prefix)
        tasks = [t for t in tasks if (t.get(field) or "").upper() == value.upper()]
    # Apply free text search across searchable fields
    if free_text:
        needle = free_text.lower()
        _SEARCH_FIELDS = ("task_id", "description", "summary", "body", "gap_id")

        def matches(t):
            return any(needle in str(t.get(f) or "").lower() for f in _SEARCH_FIELDS)
        tasks = [t for t in tasks if matches(t)]
    return tasks


def _extract_priority_tag(description: str) -> tuple:
    """Extract [Priority: X] tag from description, return (cleaned_desc, priority_or_None).

    Phase 9c: Parse legacy "[Priority: HIGH]" tags from description text.
    Only extracts valid priorities: LOW, MEDIUM, HIGH, CRITICAL.
    """
    import re
    valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    match = re.search(r'\[(?:P|p)riority:\s*(\w+)\]', description)
    if match:
        value = match.group(1).upper()
        if value in valid:
            cleaned = re.sub(r'\s*\[(?:P|p)riority:\s*\w+\]\s*', ' ', description).strip()
            return cleaned, value
    return description, None


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a task by ID from TypeDB or fallback store.

    Returns:
        Task dict or None if not found.
    """
    client = get_typedb_client()
    if client:
        try:
            task = client.get_task(task_id)
            if task:
                return task_to_response(task)
        except Exception as e:
            # BUG-408-TSK-002: Add exc_info for stack trace preservation
            # BUG-464-TSK-004: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task get failed, using fallback: {type(e).__name__}", exc_info=True)
    if task_id in _tasks_store:
        return dict(_tasks_store[task_id])
    return None


def get_task_details(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task detail sections from TypeDB or fallback store.

    Per TASK-TECH-01-v1: business, design, architecture, test_section.

    Returns:
        Dict with detail sections or None if task not found.
    """
    client = get_typedb_client()
    if client:
        try:
            details = client.get_task_details(task_id)
            if details is not None:
                return {"task_id": task_id, **details}
        except Exception as e:
            # BUG-408-TSK-003: Add exc_info for stack trace preservation
            # BUG-464-TSK-005: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task details get failed, using fallback: {type(e).__name__}", exc_info=True)
    # Fallback to in-memory store
    if task_id in _tasks_store:
        t = _tasks_store[task_id]
        return {
            "task_id": task_id,
            "business": t.get("business"),
            "design": t.get("design"),
            "architecture": t.get("architecture"),
            "test_section": t.get("test_section"),
        }
    return None


def get_sessions_for_task(task_id: str) -> List[Dict[str, Any]]:
    """Get all sessions linked to a task via completed-in relation.

    Returns full session details (not just IDs) by resolving each
    linked session through the session service.

    Returns:
        List of session dicts. Empty list if task not found or no sessions.
    """
    from governance.services import sessions as session_service

    # Get linked session IDs from task
    task = get_task(task_id)
    if not task:
        return []

    # Handle both dict and TaskResponse (Pydantic model)
    if hasattr(task, "linked_sessions"):
        session_ids = task.linked_sessions or []
    else:
        session_ids = task.get("linked_sessions") or []
    if not session_ids:
        return []

    # Resolve each session ID to full details
    sessions = []
    for sid in session_ids:
        session = session_service.get_session(sid)
        if session:
            # Normalize to dict for JSON serialization
            if hasattr(session, "model_dump"):
                sessions.append(session.model_dump())
            elif hasattr(session, "dict"):
                sessions.append(session.dict())
            else:
                sessions.append(session)
        else:
            # BUG-TASKS-002: Log unresolved session for debugging
            logger.debug(f"Session {sid} not found for task {task_id}")
            sessions.append({"session_id": sid, "status": "UNKNOWN"})

    return sessions
