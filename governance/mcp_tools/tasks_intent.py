"""
Task Intent/Outcome Capture MCP Tools (H.1)
============================================
Captures why tasks are started and what was achieved.

Per EPIC-H: Gov-Tasks MCP Parity with Gov-Sessions.
Mirrors session_capture_intent/session_capture_outcome pattern.

Created: 2026-02-09
"""

import logging
from datetime import datetime
from typing import Optional, List

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def _store_task_section(task_id: str, section: str, data: dict) -> None:
    """Store a detail section in task via TypeDB or fallback to memory."""
    try:
        from governance.stores import get_typedb_client
        client = get_typedb_client()
        if client and hasattr(client, "update_task_details"):
            client.update_task_details(task_id, **{section: str(data)})
            return
    except Exception as e:
        # BUG-477-TIN-1: Sanitize debug/info logger
        logger.debug(f"TypeDB task detail update failed for {task_id}: {type(e).__name__}")
    # Fallback: in-memory store
    from governance.stores import _tasks_store
    if task_id in _tasks_store:
        details = _tasks_store[task_id].get("details", {})
        details[section] = data
        _tasks_store[task_id]["details"] = details


def register_tasks_intent_tools(mcp) -> None:
    """Register task intent/outcome MCP tools."""

    @mcp.tool()
    def task_capture_intent(
        task_id: str,
        goal: str,
        planned_steps: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """Capture the intent behind starting a task.

        Records why this task was started, what the goal is, and the
        planned approach. Used for reconciling planned vs achieved.

        Args:
            task_id: The task to annotate
            goal: What this task aims to achieve
            planned_steps: Comma-separated planned steps
            context: Additional context (e.g., triggering gap, rule)

        Returns:
            Confirmation of intent capture.
        """
        from governance.services.tasks import get_task

        task = get_task(task_id)
        if not task:
            return format_mcp_result({"error": f"Task {task_id} not found"})

        intent_data = {
            "goal": goal,
            "planned_steps": [s.strip() for s in (planned_steps or "").split(",") if s.strip()],
            "context": context,
            "captured_at": datetime.now().isoformat(),
        }

        _store_task_section(task_id, "intent", intent_data)

        return format_mcp_result({
            "task_id": task_id,
            "action": "intent_captured",
            "goal": goal,
            "steps_count": len(intent_data["planned_steps"]),
        })

    @mcp.tool()
    def task_capture_outcome(
        task_id: str,
        status: str,
        achieved: str,
        deferred: Optional[str] = None,
        discoveries: Optional[str] = None,
        files_modified: Optional[str] = None,
    ) -> str:
        """Capture the outcome of a completed task.

        Records what was actually achieved, what was deferred, and
        any discoveries made during execution.

        Args:
            task_id: The task to annotate
            status: Final status (DONE, PARTIAL, BLOCKED, DEFERRED)
            achieved: What was actually accomplished
            deferred: What was deferred (comma-separated)
            discoveries: New insights or gaps found (comma-separated)
            files_modified: Files changed (comma-separated)

        Returns:
            Confirmation of outcome capture.
        """
        from governance.services.tasks import get_task

        task = get_task(task_id)
        if not task:
            return format_mcp_result({"error": f"Task {task_id} not found"})

        outcome_data = {
            "status": status,
            "achieved": achieved,
            "deferred": [s.strip() for s in (deferred or "").split(",") if s.strip()],
            "discoveries": [s.strip() for s in (discoveries or "").split(",") if s.strip()],
            "files_modified": [s.strip() for s in (files_modified or "").split(",") if s.strip()],
            "captured_at": datetime.now().isoformat(),
        }

        _store_task_section(task_id, "outcome", outcome_data)

        return format_mcp_result({
            "task_id": task_id,
            "action": "outcome_captured",
            "status": status,
            "deferred_count": len(outcome_data["deferred"]),
            "discoveries_count": len(outcome_data["discoveries"]),
        })
