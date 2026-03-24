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


def _str_or_none(val) -> str | None:
    """Coerce to str or None — guards against MagicMock/non-string values."""
    return val if isinstance(val, str) else None


def _dt_to_iso(val) -> str | None:
    """Convert datetime or string to ISO string. Per SRVJ-BUG-019.

    Handles: datetime objects, ISO strings, None.
    Guards against TypeDB returning raw concepts or unexpected types.
    """
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    if isinstance(val, str):
        return val
    return str(val)


# =============================================================================
# DURATION HELPER (P0-2: Single source of truth for session duration)
# =============================================================================

def compute_session_duration_from_timestamps(start, end) -> Optional[str]:
    """Compute human-readable duration from start/end timestamps.

    Accepts datetime objects or ISO strings. Returns None if unable to compute.
    Used by both session_to_response() and _session_to_dict() to ensure
    identical duration calculation across all API paths.
    """
    if not start:
        return None
    if not end:
        return "ongoing"
    try:
        # Convert to strings if datetime objects
        st_str = start.isoformat() if hasattr(start, 'isoformat') else str(start)
        et_str = end.isoformat() if hasattr(end, 'isoformat') else str(end)
        # Normalize: take first 19 chars, strip Z
        st = st_str[:19].replace("Z", "")
        et = et_str[:19].replace("Z", "")
        delta = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S") - datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
        total_seconds = delta.total_seconds()
        if total_seconds < 0:
            total_seconds = abs(total_seconds)
        total_minutes = int(total_seconds / 60)
        if total_minutes > 1440:  # >24h
            return ">24h"
        # Detect repair-generated artificial timestamps (T09:00:00 → T13:00:00)
        if "T09:00:00" in st and "T13:00:00" in et:
            return "~4h (est)"
        if total_minutes < 1:
            return "<1m"
        hours, mins = divmod(total_minutes, 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    except Exception:
        return None


# =============================================================================
# TASK HELPERS
# =============================================================================

def task_to_response(task: TypeDBTask):
    """Convert TypeDB Task to dict for TaskResponse.

    Per GAP-UI-046: Includes resolution field for task outcome tracking.
    Per WORKFLOW-SEQ-01-v1: Evidence may include [Verification: L1/L2/L3] prefix.
    """
    from governance.models import TaskResponse
    return TaskResponse(
        task_id=task.id,
        # BUG-227-HELPER-002: Align priority with _task_to_dict (body > description > name)
        description=task.body or task.description or task.name or "",
        phase=task.phase,
        status=task.status,
        resolution=task.resolution,  # NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
        priority=task.priority,  # BUG-TASK-TAXONOMY-001
        task_type=task.task_type,  # BUG-TASK-TAXONOMY-001
        summary=task.summary if isinstance(getattr(task, 'summary', None), str) else None,  # Phase 9c
        agent_id=task.agent_id,
        created_at=_dt_to_iso(task.created_at),  # SRVJ-BUG-019: defensive conversion
        claimed_at=_dt_to_iso(task.claimed_at),
        completed_at=_dt_to_iso(task.completed_at),
        body=task.body,
        linked_rules=task.linked_rules or [],  # BUG-STORE-002: null-safe
        linked_sessions=task.linked_sessions or [],
        linked_commits=task.linked_commits or [],  # Per GAP-TASK-LINK-002
        linked_documents=list(dict.fromkeys(task.linked_documents or [])),  # BUG-TASK-DOC-DUP-001: dedup
        gap_id=task.gap_id,
        evidence=task.evidence,
        document_path=task.document_path,
        workspace_id=task.workspace_id,
        resolution_notes=_str_or_none(getattr(task, 'resolution_notes', None)),  # P17
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
    # BUG-227-HELPER-003: Remove "completed" — not a valid TaskResponse status (always uppercase)
    if completed_at or status == "DONE":
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "completed",
            # BUG-213-SYNTH-TIMESTAMP-001: Use created_at as fallback before datetime.now()
            "timestamp": completed_at or created_at or datetime.now().isoformat(),
            "agent_id": agent_id,
            "message": "Task completed",
            "details": None
        })

    # Evidence event
    # BUG-HELPERS-001: Coerce to str for safe slicing
    if evidence:
        evidence_str = str(evidence)
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "event_type": "evidence",
            # BUG-213-SYNTH-TIMESTAMP-001: Use created_at as fallback before datetime.now()
            "timestamp": completed_at or created_at or datetime.now().isoformat(),
            "agent_id": agent_id,
            "message": evidence_str[:100] + ("..." if len(evidence_str) > 100 else ""),
            "details": {"full_evidence": evidence_str}
        })

    return events


# =============================================================================
# SESSION HELPERS
# =============================================================================

def session_to_response(session: TypeDBSession):
    """Convert TypeDB Session to dict for SessionResponse.

    P0-2: Duration computed server-side via compute_session_duration_from_timestamps
    to ensure identical results across all API paths (list, detail, update).
    """
    from governance.models import SessionResponse
    return SessionResponse(
        session_id=session.id,
        # BUG-226-TYPEDB-003: Use stable sentinel instead of non-deterministic datetime.now()
        start_time=session.started_at.isoformat() if session.started_at else "1970-01-01T00:00:00",
        end_time=session.completed_at.isoformat() if session.completed_at else None,
        status=session.status,
        tasks_completed=session.tasks_completed or 0,
        agent_id=session.agent_id,
        description=session.description,
        file_path=session.file_path,
        # BUG-STORE-LIST-NULL-001: Ensure list fields are [] not None (matches _session_to_dict)
        evidence_files=session.evidence_files or [],
        linked_rules_applied=session.linked_rules_applied or [],
        linked_decisions=session.linked_decisions or [],
        cc_session_uuid=getattr(session, 'cc_session_uuid', None),
        cc_project_slug=getattr(session, 'cc_project_slug', None),
        cc_git_branch=getattr(session, 'cc_git_branch', None),
        cc_tool_count=getattr(session, 'cc_tool_count', None),
        cc_thinking_chars=getattr(session, 'cc_thinking_chars', None),
        cc_compaction_count=getattr(session, 'cc_compaction_count', None),
        cc_external_name=_str_or_none(getattr(session, 'cc_external_name', None)),
        project_id=getattr(session, 'project_id', None),
        duration=compute_session_duration_from_timestamps(
            session.started_at, session.completed_at),
    )


def extract_session_id(filename: str) -> Optional[str]:
    """Extract session ID from filename pattern SESSION-YYYY-MM-DD-TOPIC.md.

    BUG-STORE-005: Updated regex to match topic-based IDs (not just numeric).
    """
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}[-\w]+)', filename)
    return match.group(1) if match else None


# =============================================================================
# CHAT HELPERS
# =============================================================================

def generate_chat_session_id() -> str:
    """Generate a chat session ID."""
    return f"CHAT-{uuid.uuid4().hex[:8].upper()}"
