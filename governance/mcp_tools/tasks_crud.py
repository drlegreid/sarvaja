"""Task CRUD MCP Tools. Per RULE-012/032, DECISION-003."""
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import typedb_client, format_mcp_result, log_monitor_event


def _monitor_task(source: str, task_id: str, action: str, severity: str = "INFO", **extra):
    """Log a task monitoring event."""
    log_monitor_event(event_type="task_event", source=source,
                      details={"task_id": task_id, "action": action, **extra}, severity=severity)


def register_task_crud_tools(mcp) -> None:
    """Register task CRUD MCP tools."""

    @mcp.tool()
    def task_create(task_id: str, name: str, description: str = "", status: str = "OPEN",
                    priority: str = "MEDIUM", phase: str = "P10") -> str:
        """
        Create a new task in TypeDB.

        Args:
            task_id: Unique task identifier (e.g., "P12.1", "RD-001")
            name: Human-readable task name
            description: Task description/details
            status: Task status per TASK-LIFE-01-v1 (OPEN, IN_PROGRESS, CLOSED)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            phase: Phase identifier (e.g., "P10", "P11", "RD")

        Returns:
            JSON with created task details or error
        """
        try:
            with typedb_client() as client:
                body = f"[Priority: {priority}] {description}" if description else f"[Priority: {priority}]"
                success = client.insert_task(
                    task_id=task_id, name=name, status=status, phase=phase, body=body
                )
                if success:
                    _monitor_task("mcp-task-create", task_id, "create", status=status, priority=priority)
                    return format_mcp_result({
                        "task_id": task_id, "name": name, "status": status,
                        "phase": phase, "priority": priority,
                        "message": f"Task {task_id} created successfully"
                    })
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
    def tasks_list() -> str:
        """
        List all tasks from TypeDB.

        Returns:
            JSON with array of all tasks and count
        """
        try:
            with typedb_client() as client:
                tasks = client.get_all_tasks()
                return format_mcp_result({
                    "tasks": [asdict(t) for t in tasks],
                    "count": len(tasks), "source": "typedb"
                })
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def task_verify(task_id: str, verification_method: str, evidence: str,
                    test_passed: bool = True) -> str:
        """
        Verify task completion with evidence. Per TEST-FIX-01-v1.

        Args:
            task_id: Task identifier to verify
            verification_method: How verification was done (pytest, curl, podman ps, etc.)
            evidence: Proof of completion (test output, log excerpt, screenshot path)
            test_passed: Whether verification tests passed

        Returns:
            JSON with verification result and task status update
        """
        if not verification_method:
            return format_mcp_result({
                "error": "verification_method required",
                "rule": "TEST-FIX-01-v1",
                "hint": "Specify how you verified: pytest, curl, podman ps, etc."
            })

        if not evidence:
            return format_mcp_result({
                "error": "evidence required",
                "rule": "TEST-FIX-01-v1",
                "hint": "Include evidence: test output, log excerpt, or screenshot path"
            })

        if not test_passed:
            return format_mcp_result({
                "error": "Cannot mark completed - verification failed",
                "task_id": task_id,
                "verification_method": verification_method,
                "evidence": evidence,
                "status": "VERIFICATION_FAILED",
                "action": "Fix the issue and re-verify"
            })

        # Verification passed - update task status
        evidence_short = evidence[:500] if len(evidence) > 500 else evidence
        try:
            with typedb_client() as client:
                success = client.update_task(task_id=task_id, status="completed")
                if success:
                    _monitor_task("mcp-task-verify", task_id, "verify", method=verification_method)
                    return format_mcp_result({
                        "task_id": task_id, "status": "completed", "verified": True,
                        "verification_method": verification_method,
                        "evidence": evidence_short, "rule": "TEST-FIX-01-v1",
                        "message": f"Task {task_id} verified and marked completed"
                    })
                return format_mcp_result({
                    "task_id": task_id, "verified": True,
                    "verification_method": verification_method,
                    "evidence": evidence_short,
                    "note": "Task not in TypeDB but verification recorded",
                    "message": f"Verification complete for {task_id}"
                })
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def session_sync_todos(session_id: str, todos_json: str) -> str:
        """
        Sync Claude Code todos to TypeDB as session tasks.

        Per MCP-002-A: Enable TodoWrite persistence to TypeDB.

        Args:
            session_id: Session identifier (e.g., "SESSION-2026-01-19-TOPIC")
            todos_json: JSON array of todos: [{"content": "...", "status": "pending|in_progress|completed"}]

        Returns:
            JSON with sync summary (created, updated, skipped)

        Example:
            session_sync_todos("SESSION-2026-01-19-AUDIT", '[{"content":"Fix bug","status":"completed"}]')
        """
        import json as json_lib
        from datetime import datetime

        try:
            todos = json_lib.loads(todos_json)
        except json_lib.JSONDecodeError as e:
            return format_mcp_result({"error": f"Invalid JSON: {e}"})

        if not isinstance(todos, list):
            return format_mcp_result({"error": "todos_json must be a JSON array"})

        try:
            with typedb_client() as client:
                date_str = datetime.now().strftime("%Y%m%d")
                created, updated, skipped = 0, 0, 0
                synced_tasks = []

                for i, todo in enumerate(todos, 1):
                    content = todo.get("content", "")
                    status = todo.get("status", "pending")
                    if not content:
                        skipped += 1
                        continue

                    task_id = f"TODO-{date_str}-{i:03d}"
                    existing = client.get_task(task_id)
                    if existing:
                        if existing.status != status:
                            client.update_task(task_id, status=status)
                            updated += 1
                            synced_tasks.append({"task_id": task_id, "action": "updated"})
                        else:
                            skipped += 1
                    else:
                        body = f"[Session: {session_id}] {content}"
                        client.insert_task(
                            task_id=task_id, name=content[:100],
                            status=status, phase="SESSION", body=body
                        )
                        created += 1
                        synced_tasks.append({"task_id": task_id, "action": "created"})

                return format_mcp_result({
                    "session_id": session_id,
                    "summary": {"created": created, "updated": updated, "skipped": skipped},
                    "tasks": synced_tasks,
                    "message": f"Synced {created + updated} tasks to TypeDB"
                })
        except ConnectionError as e:
            return format_mcp_result({"error": str(e)})
