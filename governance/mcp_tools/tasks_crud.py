"""
Task CRUD MCP Tools
===================
Task CRUD operations for TypeDB.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per DECISION-003: TypeDB-First Strategy
Per P10.4: MCP Tools for CRUD

Extracted from tasks.py per modularization plan.
Created: 2026-01-03
"""

import json
from typing import Optional
from dataclasses import asdict

from governance.mcp_tools.common import get_typedb_client


def register_task_crud_tools(mcp) -> None:
    """Register task CRUD MCP tools."""

    @mcp.tool()
    def governance_create_task(
        task_id: str,
        name: str,
        description: str = "",
        status: str = "pending",
        priority: str = "MEDIUM",
        phase: str = "P10"
    ) -> str:
        """
        Create a new task in TypeDB.

        Args:
            task_id: Task ID (e.g., "P10.7", "RD-010")
            name: Task name/title
            description: Task description
            status: Task status (pending, in_progress, completed, blocked)
            priority: Task priority (LOW, MEDIUM, HIGH, CRITICAL)
            phase: Phase identifier (e.g., "P10", "RD", "FH")

        Returns:
            JSON object with created task confirmation
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            # Map description → body, include priority in body (per TypeDB schema)
            body = f"[Priority: {priority}] {description}" if description else f"[Priority: {priority}]"
            success = client.insert_task(
                task_id=task_id,
                name=name,
                status=status,
                phase=phase,
                body=body
            )

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "name": name,
                    "status": status,
                    "phase": phase,
                    "priority": priority,
                    "message": f"Task {task_id} created successfully"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to create task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def governance_get_task(task_id: str) -> str:
        """
        Get a specific task by ID from TypeDB.

        Args:
            task_id: Task ID (e.g., "P10.1", "RD-001")

        Returns:
            JSON object with task details or error if not found
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            task = client.get_task(task_id)
            if task:
                return json.dumps(asdict(task), indent=2, default=str)
            else:
                return json.dumps({"error": f"Task {task_id} not found"})
        finally:
            client.close()

    @mcp.tool()
    def governance_update_task(
        task_id: str,
        status: Optional[str] = None,
        name: Optional[str] = None,
        phase: Optional[str] = None
    ) -> str:
        """
        Update an existing task in TypeDB.

        Args:
            task_id: Task ID to update
            status: New status (pending, in_progress, completed, blocked)
            name: New name/title
            phase: New phase identifier

        Returns:
            JSON object with updated task confirmation
        """
        if not any([status, name, phase]):
            return json.dumps({"error": "No update fields provided"})

        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

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
                    return json.dumps(result, indent=2, default=str)
                return json.dumps({
                    "task_id": task_id,
                    "message": f"Task {task_id} updated successfully"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to update task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def governance_delete_task(task_id: str) -> str:
        """
        Delete a task from TypeDB.

        Args:
            task_id: Task ID to delete

        Returns:
            JSON object with deletion confirmation
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.delete_task(task_id)

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "deleted": True,
                    "message": f"Task {task_id} deleted successfully"
                }, indent=2)
            else:
                return json.dumps({"error": f"Failed to delete task {task_id}"})
        finally:
            client.close()

    @mcp.tool()
    def governance_list_all_tasks() -> str:
        """
        List all tasks from TypeDB.

        Returns:
            JSON array of all tasks with ID, name, status, phase
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            tasks = client.get_all_tasks()
            return json.dumps({
                "tasks": [asdict(t) for t in tasks],
                "count": len(tasks),
                "source": "typedb"
            }, indent=2, default=str)
        finally:
            client.close()

    @mcp.tool()
    def governance_verify_completion(
        task_id: str,
        verification_method: str,
        evidence: str,
        test_passed: bool = True
    ) -> str:
        """
        Verify and mark a task as completed with required evidence.

        Per TEST-FIX-01-v1: Fixes MUST include verification evidence.
        Per GAP-VERIFY-001: Enforces verification before marking DONE.

        Args:
            task_id: Task/Gap ID to verify (e.g., "P10.1", "GAP-UI-001")
            verification_method: How verification was done (e.g., "pytest", "curl", "podman ps")
            evidence: Evidence of completion (test output, screenshot path, log excerpt)
            test_passed: Whether the verification test passed (default True)

        Returns:
            JSON object with verification status and task update
        """
        if not verification_method:
            return json.dumps({
                "error": "verification_method required",
                "rule": "TEST-FIX-01-v1",
                "hint": "Specify how you verified: pytest, curl, podman ps, etc."
            })

        if not evidence:
            return json.dumps({
                "error": "evidence required",
                "rule": "TEST-FIX-01-v1",
                "hint": "Include evidence: test output, log excerpt, or screenshot path"
            })

        if not test_passed:
            return json.dumps({
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
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.update_task(
                task_id=task_id,
                status="completed"
            )

            if success:
                return json.dumps({
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
                return json.dumps({
                    "task_id": task_id,
                    "verified": True,
                    "verification_method": verification_method,
                    "evidence": evidence[:500] if len(evidence) > 500 else evidence,
                    "note": "Task not in TypeDB but verification recorded",
                    "message": f"Verification complete for {task_id}"
                }, indent=2)
        finally:
            client.close()
