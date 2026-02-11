"""Task CRUD MCP Tools. Per RULE-012/032, DECISION-003.
Per DOC-SIZE-01-v1: Verification + sync tools in tasks_crud_verify.py.
"""
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import typedb_client, format_mcp_result, log_monitor_event

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
    def task_create(task_id: str, name: str, description: str = "", status: str = "OPEN",
                    priority: str = "MEDIUM", phase: str = "P10",
                    session_id: Optional[str] = None) -> str:
        """
        Create a new task in TypeDB.

        Per DATA-LINK-01-v1: Tasks can be linked to a session at creation time.

        Args:
            task_id: Unique task identifier (e.g., "P12.1", "RD-001")
            name: Human-readable task name
            description: Task description/details
            status: Task status per TASK-LIFE-01-v1 (OPEN, IN_PROGRESS, CLOSED)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            phase: Phase identifier (e.g., "P10", "P11", "RD")
            session_id: Optional session ID to link this task to (per DATA-LINK-01-v1)

        Returns:
            JSON with created task details or error
        """
        try:
            with typedb_client() as client:
                body = f"[Priority: {priority}] {description}" if description else f"[Priority: {priority}]"
                # Per DATA-LINK-01-v1: Pass session_id for auto-linking
                linked_sessions = [session_id] if session_id else None
                success = client.insert_task(
                    task_id=task_id, name=name, status=status, phase=phase, body=body,
                    linked_sessions=linked_sessions
                )
                if success:
                    _monitor_task("mcp-task-create", task_id, "create", status=status,
                                  priority=priority, session_id=session_id)
                    result = {
                        "task_id": task_id, "name": name, "status": status,
                        "phase": phase, "priority": priority,
                        "message": f"Task {task_id} created successfully"
                    }
                    if session_id:
                        result["linked_sessions"] = [session_id]
                    return format_mcp_result(result)
                return format_mcp_result({"error": f"Failed to create task {task_id}"})
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

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
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def task_update(task_id: str, status: Optional[str] = None, name: Optional[str] = None,
                    phase: Optional[str] = None) -> str:
        """
        Update an existing task in TypeDB.

        Args:
            task_id: Task identifier to update
            status: New status (pending, in_progress, completed)
            name: New task name
            phase: New phase identifier

        Returns:
            JSON with updated task details or error
        """
        if not any([status, name, phase]):
            return format_mcp_result({"error": "No update fields provided"})

        try:
            with typedb_client() as client:
                success = client.update_task(task_id=task_id, status=status, name=name, phase=phase)
                if success:
                    _monitor_task("mcp-task-update", task_id, "update", status=status, phase=phase)
                    task = client.get_task(task_id)
                    if task:
                        result = asdict(task)
                        result["message"] = f"Task {task_id} updated successfully"
                        return format_mcp_result(result)
                    return format_mcp_result({
                        "task_id": task_id, "message": f"Task {task_id} updated successfully"
                    })
                return format_mcp_result({"error": f"Failed to update task {task_id}"})
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def task_delete(task_id: str) -> str:
        """
        Delete a task from TypeDB.

        Args:
            task_id: Task identifier to delete

        Returns:
            JSON with deletion confirmation or error
        """
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
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

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
                total = len(filtered)
                paginated = filtered[offset:offset + limit]

                return format_mcp_result({
                    "tasks": [asdict(t) for t in paginated],
                    "count": len(paginated),
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + len(paginated)) < total,
                    "source": "typedb"
                })
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})
