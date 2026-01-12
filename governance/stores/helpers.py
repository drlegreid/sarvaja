"""
Governance Stores - Task, Session, Chat Helpers.

Per RULE-032: Modularized from stores.py (503 lines).
Contains: Conversion helpers for tasks, sessions, and chat.
"""

import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from governance.client import Task as TypeDBTask, Session as TypeDBSession


# =============================================================================
# TASK HELPERS
# =============================================================================

def task_to_response(task: TypeDBTask):
    """Convert TypeDB Task to dict for TaskResponse."""
    from governance.models import TaskResponse
    return TaskResponse(
        task_id=task.id,
        description=task.name or task.description or "",
        phase=task.phase,
        status=task.status,
        agent_id=task.agent_id,
        created_at=task.created_at.isoformat() if task.created_at else None,
        claimed_at=task.claimed_at.isoformat() if task.claimed_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        body=task.body,
        linked_rules=task.linked_rules,
        linked_sessions=task.linked_sessions,
        gap_id=task.gap_id,
        evidence=task.evidence
    )


def synthesize_execution_events(task_id: str, task_data: Any) -> List[Dict[str, Any]]:
    """
    Synthesize execution events from task timestamps (ORCH-007).

    Creates events from claimed_at, completed_at, etc. for tasks without explicit events.
    """
    events = []

    # Handle both TypeDB Task objects and dict data
    if hasattr(task_data, 'created_at'):
        created_at = task_data.created_at.isoformat() if task_data.created_at else None
        claimed_at = task_data.claimed_at.isoformat() if task_data.claimed_at else None
        completed_at = task_data.completed_at.isoformat() if task_data.completed_at else None
        agent_id = task_data.agent_id
        status = task_data.status
        evidence = task_data.evidence
    else:
        created_at = task_data.get("created_at")
        claimed_at = task_data.get("claimed_at")
        completed_at = task_data.get("completed_at")
        agent_id = task_data.get("agent_id")
        status = task_data.get("status", "pending")
        evidence = task_data.get("evidence")

    # Created event
    if created_at:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "started",
            "timestamp": created_at,
            "agent_id": None,
            "message": "Task created",
            "details": None
        })

    # Claimed event
    if claimed_at and agent_id:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "claimed",
            "timestamp": claimed_at,
            "agent_id": agent_id,
            "message": f"Claimed by {agent_id}",
            "details": None
        })

    # Completed event
    if completed_at or status in ["DONE", "completed"]:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "completed",
            "timestamp": completed_at or datetime.now().isoformat(),
            "agent_id": agent_id,
            "message": "Task completed",
            "details": None
        })

    # Evidence event
    if evidence:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "evidence",
            "timestamp": completed_at or datetime.now().isoformat(),
            "agent_id": agent_id,
            "message": evidence[:100] + ("..." if len(evidence) > 100 else ""),
            "details": {"full_evidence": evidence}
        })

    return events


# =============================================================================
# SESSION HELPERS
# =============================================================================

def session_to_response(session: TypeDBSession):
    """Convert TypeDB Session to dict for SessionResponse."""
    from governance.models import SessionResponse
    return SessionResponse(
        session_id=session.id,
        start_time=session.started_at.isoformat() if session.started_at else datetime.now().isoformat(),
        end_time=session.completed_at.isoformat() if session.completed_at else None,
        status=session.status,
        tasks_completed=session.tasks_completed or 0,
        agent_id=session.agent_id,
        description=session.description,
        file_path=session.file_path,
        evidence_files=session.evidence_files,
        linked_rules_applied=session.linked_rules_applied,
        linked_decisions=session.linked_decisions
    )


def extract_session_id(filename: str) -> Optional[str]:
    """Extract session ID from filename pattern SESSION-YYYY-MM-DD-NNN.md."""
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}-\d+)', filename)
    return match.group(1) if match else None


# =============================================================================
# CHAT HELPERS
# =============================================================================

def generate_chat_session_id() -> str:
    """Generate a chat session ID."""
    return f"CHAT-{uuid.uuid4().hex[:8].upper()}"
