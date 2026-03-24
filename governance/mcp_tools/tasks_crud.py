"""Task CRUD MCP Tools. Per RULE-012/032, DECISION-003.
Per DOC-SIZE-01-v1: Verification + sync tools in tasks_crud_verify.py.
"""
import logging
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import typedb_client, format_mcp_result, log_monitor_event
from governance.services.tasks_mutations import update_task as svc_update_task

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
from governance.mcp_tools.tasks_crud_verify import register_task_verify_tools  # noqa: F401


def _monitor_task(source: str, task_id: str, action: str, severity: str = "INFO", **extra):
    """Log a task monitoring event."""
    log_monitor_event(event_type="task_event", source=source,
                      details={"task_id": task_id, "action": action, **extra}, severity=severity)


def register_task_crud_tools(mcp) -> None:
    """Register task CRUD MCP tools."""

    # Register verification + sync tools from extracted module
    register_task_verify_tools(mcp)

    @mcp.tool()
    def task_create(name: str, task_id: str = "", description: str = "", status: str = "OPEN",
                    priority: str = "MEDIUM", task_type: str = "feature",
                    phase: str = "P10",
                    session_id: Optional[str] = None,
                    workspace_id: Optional[str] = None) -> str:
        """
        Create a new task in TypeDB.

        Per META-TAXON-01-v1: task_id is auto-generated from task_type if omitted.
        Per DATA-LINK-01-v1: Tasks can be linked to a session at creation time.
        Per EPIC-GOV-TASKS-V2 Phase 4: Tasks can be assigned to a workspace.

        Args:
            name: Human-readable task name
            task_id: Task ID (leave empty to auto-generate from task_type, e.g. BUG-001)
            description: Task description/details
            status: Task status per TASK-LIFE-01-v1 (OPEN, IN_PROGRESS, CLOSED)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            task_type: Task type (bug, feature, chore, research, gap, epic, test, specification, spec)
            phase: Phase identifier (e.g., "P10", "P11", "RD")
            session_id: Optional session ID to link this task to (per DATA-LINK-01-v1)
            workspace_id: Optional workspace ID to assign this task to

        Returns:
            JSON with created task details or error
        """
        try:
            from governance.services.tasks import create_task as svc_create
            linked_sessions = [session_id] if session_id else None
            result = svc_create(
                task_id=task_id or None,
                description=name,
                status=status,
                phase=phase,
                body=description or None,
                priority=priority or "MEDIUM",
                task_type=task_type or None,
                linked_sessions=linked_sessions,
                workspace_id=workspace_id,
                source="mcp",
            )
            # BUG-INTTEST-001: result is Pydantic TaskResponse, not dict
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = {"task_id": task_id}
            actual_id = result_dict.get("task_id") or task_id
            _monitor_task("mcp-task-create", actual_id, "create", status=status,
                          priority=priority, session_id=session_id)
            result_dict["message"] = f"Task {actual_id} created successfully"
            return format_mcp_result(result_dict)
        except ValueError as ve:
            # SRVJ-FEAT-001: Return structured validation errors
            error_msg = str(ve)
            logger.warning(f"task_create validation: {error_msg}")
            return format_mcp_result({"error": error_msg, "type": "validation"})
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-001: Sanitize logger message to match response pattern
            logger.error(f"task_create failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"task_create failed: {type(e).__name__}"})

    @mcp.tool()
    def task_get(task_id: str) -> str:
        """
        Get a task by ID from TypeDB.

        Args:
            task_id: Task identifier to retrieve

        Returns:
            JSON with task details or error if not found
        """
        try:
            with typedb_client() as client:
                task = client.get_task(task_id)
                if task:
                    _monitor_task("mcp-task-get", task_id, "query", found=True)
                    return format_mcp_result(asdict(task))
                return format_mcp_result({"error": f"Task {task_id} not found"})
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-002: Sanitize logger message to match response pattern
            logger.error(f"task_get failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"task_get failed: {type(e).__name__}"})

    @mcp.tool()
    def task_update(task_id: str, status: Optional[str] = None, name: Optional[str] = None,
                    phase: Optional[str] = None, priority: Optional[str] = None,
                    task_type: Optional[str] = None,
                    workspace_id: Optional[str] = None,
                    summary: Optional[str] = None,
                    agent_id: Optional[str] = None,
                    resolution_notes: Optional[str] = None) -> str:
        """
        Update an existing task in TypeDB.

        Per BUG-TASK-TAXONOMY-001: priority and task_type are first-class fields.
        Per EPIC-GOV-TASKS-V2 Phase 2: Routes through service layer for
        auto-linking, audit, and monitoring parity.
        Per EPIC-GOV-TASKS-V2 Phase 4: workspace_id assignment.
        Per FIX-DATA-002: summary is a first-class updatable field.
        Per SRVJ-BUG-021: agent_id exposed for DONE gate compliance.

        Args:
            task_id: Task identifier to update
            status: New status (OPEN, IN_PROGRESS, CLOSED)
            name: New task name
            phase: New phase identifier
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            task_type: Task type (bug, feature, chore, research, gap, epic, test, specification, spec)
            workspace_id: Workspace ID to assign this task to
            summary: One-line task summary (optional)
            agent_id: Agent performing the work (must be registered agent)

        Returns:
            JSON with updated task details or error
        """
        if not any([status, name, phase, priority, task_type, workspace_id, summary, agent_id, resolution_notes]):
            return format_mcp_result({"error": "No update fields provided"})

        try:
            result = svc_update_task(
                task_id=task_id,
                status=status,
                description=name,
                phase=phase,
                priority=priority,
                task_type=task_type,
                workspace_id=workspace_id,
                summary=summary,
                agent_id=agent_id,
                resolution_notes=resolution_notes,
                source="mcp",
            )
            if result:
                _monitor_task("mcp-task-update", task_id, "update", status=status, phase=phase)
                result["message"] = f"Task {task_id} updated successfully"
                return format_mcp_result(result)
            return format_mcp_result({"error": f"Task {task_id} not found"})
        except ValueError as ve:
            # SRVJ-FEAT-002: Return structured DONE gate validation errors
            error_msg = str(ve)
            logger.warning(f"task_update validation: {error_msg}")
            return format_mcp_result({"error": error_msg, "type": "validation"})
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-003: Sanitize logger message to match response pattern
            logger.error(f"task_update failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"task_update failed: {type(e).__name__}"})

    @mcp.tool()
    def task_delete(task_id: str, confirm: bool = False) -> str:
        """
        Delete a task from TypeDB.

        Requires explicit confirmation to prevent accidental deletion.

        Args:
            task_id: Task identifier to delete
            confirm: Must be True to proceed with deletion

        Returns:
            JSON with deletion confirmation or error
        """
        # BUG-357-TDL-001: Require explicit confirmation (matching rule_delete pattern)
        if confirm is not True:
            return format_mcp_result({
                "error": "Deletion requires explicit confirmation. Set confirm=True to proceed.",
                "task_id": task_id,
                "hint": "Consider updating status to CLOSED instead of deleting."
            })
        try:
            with typedb_client() as client:
                success = client.delete_task(task_id)
                if success:
                    _monitor_task("mcp-task-delete", task_id, "delete", severity="WARNING")
                    return format_mcp_result({
                        "task_id": task_id, "deleted": True,
                        "message": f"Task {task_id} deleted successfully"
                    })
                return format_mcp_result({"error": f"Failed to delete task {task_id}"})
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-004: Sanitize logger message to match response pattern
            logger.error(f"task_delete failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"task_delete failed: {type(e).__name__}"})

    @mcp.tool()
    def taxonomy_get() -> str:
        """
        Get task/rule taxonomy (types, priorities, statuses, prefixes).

        Per META-TAXON-01-v1: Returns all enum values for validation and auto-ID.

        Returns:
            JSON with task_types, task_priorities, task_type_prefixes,
            task_statuses, task_phases, rule_categories, rule_priorities, rule_statuses.
        """
        # BUG-276-TCRUD-001: Wrap in try/except to prevent raw ImportError to MCP caller
        try:
            from agent.governance_ui.state.constants import (
                TASK_TYPES, TASK_PRIORITIES, TASK_TYPE_PREFIX,
                TASK_STATUSES, TASK_PHASES,
                RULE_CATEGORIES, RULE_PRIORITIES, RULE_STATUSES,
            )
            return format_mcp_result({
                "task_types": TASK_TYPES,
                "task_priorities": TASK_PRIORITIES,
                "task_type_prefixes": TASK_TYPE_PREFIX,
                "task_statuses": TASK_STATUSES,
                "task_phases": TASK_PHASES,
                "rule_categories": RULE_CATEGORIES,
                "rule_priorities": RULE_PRIORITIES,
                "rule_statuses": RULE_STATUSES,
            })
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-005: Sanitize logger message to match response pattern
            logger.error(f"taxonomy_get failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"taxonomy_get failed: {type(e).__name__}"})

    @mcp.tool()
    def tasks_list(
        status: Optional[str] = None,
        phase: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> str:
        """
        List tasks from TypeDB with optional filtering and pagination.

        Per ARCH-MCP-PARITY-01-v1: Provides REST API-equivalent filtering.

        Args:
            status: Filter by status (TODO, IN_PROGRESS, DONE, BLOCKED)
            phase: Filter by phase (P10, P11, RD, etc.)
            limit: Maximum number of results (default: 50, max: 200)
            offset: Skip first N results for pagination (default: 0)

        Returns:
            JSON with tasks array, count, and pagination info
        """
        try:
            # Cap limit at 200 per API parity
            limit = min(limit, 200)

            with typedb_client() as client:
                all_tasks = client.get_all_tasks()

                # Apply filters
                filtered = all_tasks
                if status:
                    filtered = [t for t in filtered if t.status == status.upper()]
                if phase:
                    filtered = [t for t in filtered if t.phase == phase.upper()]

                # Apply pagination
                # BUG-204-OFFSET-001: Guard against negative offset/limit
                total = len(filtered)
                safe_offset = max(0, offset)
                safe_limit = max(1, min(limit, 200))
                paginated = filtered[safe_offset:safe_offset + safe_limit]

                return format_mcp_result({
                    "tasks": [asdict(t) for t in paginated],
                    "count": len(paginated),
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + len(paginated)) < total,
                    "source": "typedb"
                })
        except Exception as e:
            # BUG-357-MCP-001: Log full error for debugging
            # BUG-451-TC-006: Sanitize logger message to match response pattern
            logger.error(f"tasks_list failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"tasks_list failed: {type(e).__name__}"})
