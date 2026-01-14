"""
Session Visibility Routes.

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/routes/agents.py

Created: 2026-01-14
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Session Visibility"])

# Import session visibility module
try:
    from session_visibility import (
        start_session as vis_start_session,
        start_task as vis_start_task,
        record_rule_application,
        record_tool_call as vis_record_tool_call,
        complete_task as vis_complete_task,
        get_session_visibility,
        get_task_rules_summary,
        get_token_usage_report
    )
    SESSION_VISIBILITY_AVAILABLE = True
except ImportError:
    SESSION_VISIBILITY_AVAILABLE = False


@router.get("/sessions/visibility")
async def get_visibility():
    """
    Get session visibility report.

    Shows: Active tasks, rules applied, tool calls, token usage.
    """
    if not SESSION_VISIBILITY_AVAILABLE:
        return {"error": "Session visibility not available", "status": "UNAVAILABLE"}

    return get_session_visibility()


@router.get("/sessions/visibility/tokens")
async def get_tokens():
    """
    Get token usage report.

    Shows: Total tokens, by session, API key status.
    """
    if not SESSION_VISIBILITY_AVAILABLE:
        return {"error": "Session visibility not available"}

    return get_token_usage_report()


@router.get("/tasks/{task_id}/rules")
async def get_task_rules(task_id: str):
    """
    Get rules applied for a specific task.

    Shows: Task details, rules applied, tool calls, tokens.
    """
    if not SESSION_VISIBILITY_AVAILABLE:
        return {"error": "Session visibility not available"}

    return get_task_rules_summary(task_id)


@router.post("/sessions/visibility/start")
async def start_visibility_session(session_id: str):
    """Start tracking a new session for visibility."""
    if not SESSION_VISIBILITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session visibility not available")

    return vis_start_session(session_id)


@router.post("/tasks/{task_id}/start")
async def start_task_tracking(task_id: str, task_name: str, session_id: Optional[str] = None):
    """Start tracking a task within the current session."""
    if not SESSION_VISIBILITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session visibility not available")

    from dataclasses import asdict
    task = vis_start_task(task_id, task_name, session_id)
    return asdict(task)


@router.post("/tasks/{task_id}/rule")
async def record_task_rule(task_id: str, rule_id: str, context: str = ""):
    """Record that a rule was applied while working on a task."""
    if not SESSION_VISIBILITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session visibility not available")

    record_rule_application(task_id, rule_id, context)
    return {"task_id": task_id, "rule_id": rule_id, "recorded": True}


@router.post("/tasks/{task_id}/tool-call")
async def record_task_tool_call(
    task_id: str,
    tool_name: str,
    duration_ms: int = 0,
    rules_applied: str = "",
    tokens: int = 0
):
    """Record a tool call within a task."""
    if not SESSION_VISIBILITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session visibility not available")

    rules_list = [r.strip() for r in rules_applied.split(",")] if rules_applied else []
    vis_record_tool_call(task_id, tool_name, duration_ms, rules_list, tokens)
    return {"task_id": task_id, "tool_name": tool_name, "recorded": True}


@router.post("/tasks/{task_id}/complete")
async def complete_task_tracking(task_id: str, status: str = "completed"):
    """Mark a task as complete."""
    if not SESSION_VISIBILITY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session visibility not available")

    result = vis_complete_task(task_id, status)
    if result:
        return result
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
