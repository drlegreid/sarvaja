"""Task Verification & Session Sync MCP Tools.

Per DOC-SIZE-01-v1: Extracted from tasks_crud.py.
task_verify and session_sync_todos tools.
"""
from governance.mcp_tools.common import typedb_client, format_mcp_result, log_monitor_event


def _monitor_task(source: str, task_id: str, action: str, severity: str = "INFO", **extra):
    """Log a task monitoring event."""
    log_monitor_event(event_type="task_event", source=source,
                      details={"task_id": task_id, "action": action, **extra}, severity=severity)


def register_task_verify_tools(mcp) -> None:
    """Register task verification and session sync MCP tools."""

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

        Per MCP-002-A / GOV-MCP-FIRST-01-v1: Enable TodoWrite persistence to TypeDB.

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
