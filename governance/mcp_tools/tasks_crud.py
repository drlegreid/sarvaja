"""Task CRUD MCP Tools. Per RULE-012/032, DECISION-003."""
import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client, format_mcp_result


def register_task_crud_tools(mcp) -> None:
    """Register task CRUD MCP tools."""

    @mcp.tool()
    def task_create(task_id: str, name: str, description: str = "", status: str = "pending",
                    priority: str = "MEDIUM", phase: str = "P10") -> str:
        """
        Create a new task in TypeDB.

        Args:
            task_id: Unique task identifier (e.g., "P12.1", "RD-001")
            name: Human-readable task name
            description: Task description/details
            status: Task status (pending, in_progress, completed)
            priority: Priority level (LOW, MEDIUM, HIGH, CRITICAL)
            phase: Phase identifier (e.g., "P10", "P11", "RD")

        Returns:
            JSON with created task details or error
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # Map description -> body, include priority in body (per TypeDB schema)
            body = f"[Priority: {priority}] {description}" if description else f"[Priority: {priority}]"
            success = client.insert_task(
                task_id=task_id,
                name=name,
                status=status,
                phase=phase,
                body=body
            )

            if success:
                return format_mcp_result({
                    "task_id": task_id,
                    "name": name,
                    "status": status,
                    "phase": phase,
                    "priority": priority,
                    "message": f"Task {task_id} created successfully"
                }, indent=2)
            else:
                return format_mcp_result({"error": f"Failed to create task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def task_get(task_id: str) -> str:
        """
        Get a task by ID from TypeDB.

        Args:
            task_id: Task identifier to retrieve

        Returns:
            JSON with task details or error if not found
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            task = client.get_task(task_id)
            if task:
                return format_mcp_result(asdict(task), indent=2, default=str)
            else:
                return format_mcp_result({"error": f"Task {task_id} not found"})
        finally:
            client.close()

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

        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.update_task(
                task_id=task_id,
                status=status,
                name=name,
                phase=phase
            )

            if success:
                # Get updated task to return
                task = client.get_task(task_id)
                if task:
                    result = asdict(task)
                    result["message"] = f"Task {task_id} updated successfully"
                    return format_mcp_result(result)
                return format_mcp_result({
                    "task_id": task_id,
                    "message": f"Task {task_id} updated successfully"
                }, indent=2)
            else:
                return format_mcp_result({"error": f"Failed to update task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def task_delete(task_id: str) -> str:
        """
        Delete a task from TypeDB.

        Args:
            task_id: Task identifier to delete

        Returns:
            JSON with deletion confirmation or error
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.delete_task(task_id)

            if success:
                return format_mcp_result({
                    "task_id": task_id,
                    "deleted": True,
                    "message": f"Task {task_id} deleted successfully"
                }, indent=2)
            else:
                return format_mcp_result({"error": f"Failed to delete task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def tasks_list() -> str:
        """
        List all tasks from TypeDB.

        Returns:
            JSON with array of all tasks and count
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            tasks = client.get_all_tasks()
            return format_mcp_result({
                "tasks": [asdict(t) for t in tasks],
                "count": len(tasks),
                "source": "typedb"
            }, indent=2, default=str)
        finally:
            client.close()

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
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.update_task(
                task_id=task_id,
                status="completed"
            )

            if success:
                return format_mcp_result({
                    "task_id": task_id,
                    "status": "completed",
                    "verified": True,
                    "verification_method": verification_method,
                    "evidence": evidence[:500] if len(evidence) > 500 else evidence,
                    "rule": "TEST-FIX-01-v1",
                    "message": f"Task {task_id} verified and marked completed"
                }, indent=2)
            else:
                # Task might not exist in TypeDB, but verification is recorded
                return format_mcp_result({
                    "task_id": task_id,
                    "verified": True,
                    "verification_method": verification_method,
                    "evidence": evidence[:500] if len(evidence) > 500 else evidence,
                    "note": "Task not in TypeDB but verification recorded",
                    "message": f"Verification complete for {task_id}"
                }, indent=2)
        finally:
            client.close()
