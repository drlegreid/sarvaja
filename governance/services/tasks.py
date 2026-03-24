"""Task Service Layer - Hub module for all task operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.
Per DOC-SIZE-01-v1: Queries in tasks_queries.py, mutations in tasks_mutations.py.

Created: 2026-02-01
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    get_all_tasks_from_typedb,  # noqa: F401 — re-export for test patch compat
    _tasks_store,
    _sessions_store,
    task_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event

# Re-export query functions for backward compatibility (DOC-SIZE-01-v1)
from governance.services.tasks_queries import (  # noqa: F401
    list_tasks,
    get_task,
    get_task_details,
    get_sessions_for_task,
    _apply_post_filters,
    _apply_search,
    _parse_structured_search,
    _extract_priority_tag,
    _detect_doc_type,
)

# Re-export mutation functions for backward compatibility
from governance.services.tasks_mutations import (  # noqa: F401
    update_task,
    delete_task,
    link_task_to_rule,
    link_task_to_session,
    link_task_to_document,
    unlink_task_from_document,
)

logger = logging.getLogger(__name__)

__all__ = [
    "list_tasks",
    "create_task",
    "get_task",
    "get_task_details",
    "update_task_details",
    "get_sessions_for_task",
    # Re-exports from tasks_mutations
    "update_task",
    "delete_task",
    "link_task_to_rule",
    "link_task_to_session",
    "link_task_to_document",
    "unlink_task_from_document",
    # Re-exports from tasks_queries (private helpers used by tests)
    "_apply_post_filters",
    "_apply_search",
    "_parse_structured_search",
    "_extract_priority_tag",
    "_detect_doc_type",
    "_generate_summary",
]


def _get_active_session_id() -> Optional[str]:
    """Find the most recent active session for auto-linking (DATA-LINK-01-v1)."""
    active = [
        # BUG-214-008: Snapshot to prevent RuntimeError on concurrent dict mutation
        (sid, s) for sid, s in list(_sessions_store.items())
        if s.get("status") == "ACTIVE"
    ]
    if not active:
        return None
    # Return most recent by start_time
    active.sort(key=lambda x: x[1].get("start_time", ""), reverse=True)
    return active[0][0]


def _monitor(action: str, task_id: str, source: str = "service", **extra):
    """Log task monitoring event for MCP compliance."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="task_event",
            source=source,
            details={"task_id": task_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        # BUG-420-MON-005: Add exc_info for stack trace preservation
        # BUG-464-TSK-001: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Monitor event failed for task {task_id}: {type(e).__name__}", exc_info=True)


# P16: Duplicate detection helpers (extracted per DOC-SIZE-01-v1)
from governance.services.tasks_duplicate import (  # noqa: F401
    _jaccard_word_similarity,
    _find_duplicate_tasks,
    _attach_duplicate_warnings,
    DUPLICATE_SIMILARITY_THRESHOLD,
)


def _generate_summary(description: str) -> str:
    """Auto-generate a structured summary from description.

    Phase 9c: Produces a short (<= 80 char) one-line intent.
    Strips [Priority: X] tags before summarizing.
    """
    if not description:
        return ""
    # Strip priority tags
    import re
    cleaned = re.sub(r'\s*\[(?:P|p)riority:\s*\w+\]\s*', ' ', description).strip()
    # Truncate to 80 chars
    if len(cleaned) <= 80:
        return cleaned
    return cleaned[:77] + "..."


def create_task(
    task_id: Optional[str] = None,
    description: str = "",
    status: str = "OPEN",
    phase: str = "P10",
    agent_id: Optional[str] = None,
    body: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    gap_id: Optional[str] = None,
    linked_rules: Optional[List[str]] = None,
    linked_sessions: Optional[List[str]] = None,
    linked_documents: Optional[List[str]] = None,
    workspace_id: Optional[str] = None,
    summary: Optional[str] = None,
    source: str = "rest",
) -> Dict[str, Any]:
    """Create a task in TypeDB with fallback to in-memory store.

    Per META-TAXON-01-v1: If task_id is None/empty and task_type is provided,
    auto-generates a sequential ID like BUG-001, FEAT-042, etc.

    Returns:
        Task dict on success.

    Raises:
        ValueError: If task already exists, or no task_id and no task_type.
    """
    # BUG-STATUS-CASE-001: Normalize status to uppercase at service boundary
    status = (status or "OPEN").upper()

    # SRVJ-BUG-023: Validate agent_id against registered agents at write boundary
    if agent_id:
        from governance.services.task_rules import validate_agent_id
        agent_errors = validate_agent_id(agent_id)
        if agent_errors:
            raise ValueError(f"Invalid agent_id '{agent_id}': {agent_errors[0].message}")

    # Phase 9c: Extract [Priority: X] tag from description if no explicit priority
    if description and not priority:
        description, extracted_priority = _extract_priority_tag(description)
        if extracted_priority:
            priority = extracted_priority
            logger.info(f"[Phase9c] Extracted priority {priority} from description")
    elif description and priority:
        # Still clean the tag from description even if explicit priority given
        description, _ = _extract_priority_tag(description)

    # Phase 9c: Auto-generate summary if not provided
    if not summary and description:
        summary = _generate_summary(description)

    # Auto-generate task_id from task_type if not provided (META-TAXON-01-v1 + FIX-NOM-002)
    client = get_typedb_client()
    if not task_id:
        if task_type:
            from governance.services.task_id_gen import (
                generate_task_id, resolve_project_prefix,
            )
            # FIX-NOM-002: Auto-prefix with project name when workspace is set
            project_prefix = ""
            if workspace_id:
                try:
                    from governance.services.workspaces import _workspaces_store
                    project_prefix = resolve_project_prefix(
                        workspace_id, _workspaces_store,
                    )
                except Exception:
                    pass
            task_id = generate_task_id(task_type, client, project_prefix=project_prefix)
            logger.info(f"[META-TAXON-01] Auto-generated task ID: {task_id}")
        else:
            raise ValueError("Either task_id or task_type must be provided for ID generation")

    # SRVJ-FEAT-013: Auto-assign default workspace when not provided
    if not workspace_id:
        try:
            from agent.governance_ui.state.constants import DEFAULT_WORKSPACE_ID
            workspace_id = DEFAULT_WORKSPACE_ID
            logger.info(f"[SRVJ-FEAT-013] Auto-assigned workspace {workspace_id} to task {task_id or 'TBD'}")
        except ImportError:
            pass

    # SRVJ-BUG-022 / H-TASK-002: Auto-assign agent_id on create with IN_PROGRESS
    if status == "IN_PROGRESS" and not agent_id:
        from governance.stores.agents import DEFAULT_AGENT_ID
        agent_id = DEFAULT_AGENT_ID
        logger.info(f"[H-TASK-002] Auto-assigned agent_id={DEFAULT_AGENT_ID} on create IN_PROGRESS for {task_id}")

    # Auto-trim: if description > 200 chars and no body, split
    if description and len(description) > 200 and not body:
        body = description
        description = description[:197] + "..."

    # Per DATA-LINK-01-v1: Auto-link to active session if none provided
    if not linked_sessions:
        active_sid = _get_active_session_id()
        if active_sid:
            linked_sessions = [active_sid]
            logger.info(f"[DATA-LINK-01] Auto-linking task {task_id} to session {active_sid}")

    # SRVJ-FEAT-001: Static rules engine — validate on create
    from governance.services.task_rules import validate_on_create, format_validation_result
    create_errors = validate_on_create(
        task_id=task_id, summary=summary, task_type=task_type,
        description=description,
    )
    if create_errors:
        # Log warnings but only block on hard errors (RequiredField, TypePrefixMismatch)
        hard_errors = [e for e in create_errors if e.rule in ("RequiredField", "TypePrefixMismatch")]
        for err in create_errors:
            level = "WARNING" if err.rule == "FormatRule" else "ERROR"
            logger.log(
                logging.WARNING if level == "WARNING" else logging.ERROR,
                f"[TASK-RULES] {err.rule}: {err.message}"
            )
        if hard_errors:
            result = format_validation_result(hard_errors)
            raise ValueError(f"Validation failed: {result}")

    if client:
        try:
            if client.get_task(task_id):
                raise ValueError(f"Task {task_id} already exists")
            created = client.insert_task(
                task_id=task_id, name=description, status=status,
                phase=phase, body=body, gap_id=gap_id,
                linked_rules=linked_rules, linked_sessions=linked_sessions,
                agent_id=agent_id, priority=priority, task_type=task_type,
                workspace_id=workspace_id, summary=summary,
            )
            if created:
                # Link documents after creation
                if linked_documents:
                    for doc_path in linked_documents:
                        try:
                            client.link_task_to_document(task_id, doc_path)
                        except Exception as le:
                            # BUG-275-TASKS-001: Promote to WARNING (debug hides link failures)
                            # BUG-450-TSK-001: Add exc_info for stack trace preservation
                            # BUG-464-TSK-002: Sanitize logger message — exc_info=True already captures full stack
                            logger.warning(f"TypeDB document link {task_id}->{doc_path}: {type(le).__name__}", exc_info=True)
                record_audit("CREATE", "task", task_id,
                             actor_id=agent_id or "system",
                             metadata={"phase": phase, "status": status, "source": source})
                _monitor("create", task_id, source=source, status=status, phase=phase)
                log_event("task", "create", task_id=task_id, status=status, agent_id=agent_id, source=source)
                # BUG-TASK-UI-001: Cache in _tasks_store so task is visible
                # even during transient TypeDB read failures
                response = task_to_response(created)
                # SRVJ-BUG-007: response is TaskResponse (Pydantic), not dict
                _tasks_store[task_id] = {
                    "task_id": task_id, "description": description,
                    "phase": phase, "status": status, "priority": priority,
                    "task_type": task_type, "agent_id": agent_id,
                    "body": body, "gap_id": gap_id,
                    "linked_rules": linked_rules or [],
                    "linked_sessions": linked_sessions or [],
                    "linked_documents": linked_documents or [],
                    "workspace_id": workspace_id,
                    "summary": summary,
                    "created_at": getattr(response, "created_at", None)
                    or datetime.now().isoformat(),
                }
                return _attach_duplicate_warnings(
                    response, summary, description, task_id,
                )
        except ValueError:
            raise
        except Exception as e:
            # BUG-408-TSK-001: Add exc_info for stack trace preservation
            # BUG-464-TSK-003: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task insert failed, using fallback: {type(e).__name__}", exc_info=True)

    # Fallback to in-memory store
    if task_id in _tasks_store:
        raise ValueError(f"Task {task_id} already exists")

    task_data = {
        "task_id": task_id, "description": description, "phase": phase,
        "status": status, "priority": priority, "task_type": task_type,
        "agent_id": agent_id, "body": body, "summary": summary,
        # BUG-214-003: Normalize list fields to [] to prevent NoneType iteration errors
        "linked_rules": linked_rules or [], "linked_sessions": linked_sessions or [],
        "linked_documents": linked_documents or [], "gap_id": gap_id,
        "workspace_id": workspace_id,
        "created_at": datetime.now().isoformat(),
    }
    _tasks_store[task_id] = task_data
    record_audit("CREATE", "task", task_id,
                 actor_id=agent_id or "system",
                 metadata={"phase": phase, "status": status, "source": source})
    _monitor("create", task_id, source=source, status=status, phase=phase)
    log_event("task", "create", task_id=task_id, status=status, agent_id=agent_id, source=source)
    return _attach_duplicate_warnings(task_data, summary, description, task_id)


def update_task_details(
    task_id: str,
    business: Optional[str] = None,
    design: Optional[str] = None,
    architecture: Optional[str] = None,
    test_section: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update task detail sections via TypeDB or fallback.

    Per TASK-TECH-01-v1: Technology Solution Documentation.

    Returns:
        Updated detail sections or None if task not found.
    """
    client = get_typedb_client()
    if client:
        try:
            success = client.update_task_details(
                task_id, business=business, design=design,
                architecture=architecture, test_section=test_section,
            )
            if success:
                _monitor("update_details", task_id, source="service")
                return get_task_details(task_id)
        except Exception as e:
            # BUG-408-TSK-004: Add exc_info for stack trace preservation
            # BUG-464-TSK-006: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task details update failed, using fallback: {type(e).__name__}", exc_info=True)
    # Fallback to in-memory store
    if task_id in _tasks_store:
        t = _tasks_store[task_id]
        if business is not None:
            t["business"] = business
        if design is not None:
            t["design"] = design
        if architecture is not None:
            t["architecture"] = architecture
        if test_section is not None:
            t["test_section"] = test_section
        _monitor("update_details", task_id, source="service_fallback")
        return get_task_details(task_id)
    return None
