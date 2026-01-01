"""
Governance API Shared Stores and Helpers.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Shared state for route modules.

Created: 2024-12-28
"""

import os
import json
import math
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from governance.client import get_client, Task as TypeDBTask, Session as TypeDBSession

logger = logging.getLogger(__name__)

# =============================================================================
# TYPEDB CONFIGURATION
# =============================================================================

USE_TYPEDB = os.getenv("USE_TYPEDB", "true").lower() == "true"


def get_typedb_client():
    """Get TypeDB client with connection check."""
    if not USE_TYPEDB:
        return None
    try:
        client = get_client()
        if client and client.is_connected():
            return client
    except Exception as e:
        logger.warning(f"TypeDB connection failed: {e}")
    return None


# =============================================================================
# DATA STORES (Hybrid: TypeDB primary, in-memory cache/fallback)
# =============================================================================

# Task store - serves as cache when TypeDB is primary, fallback when unavailable
# Per GAP-STUB-001/002: Prefer TypeDB wrappers for reads, but keep fallback active
# WARNING: Direct writes to this dict without syncing to TypeDB will cause inconsistency
_tasks_store: Dict[str, Dict[str, Any]] = {}

# Task execution events store (ORCH-007)
_execution_events_store: Dict[str, List[Dict[str, Any]]] = {}

# Session store - serves as cache when TypeDB is primary, fallback when unavailable
# Per GAP-STUB-003/004: Prefer TypeDB wrappers for reads, but keep fallback active
# WARNING: Direct writes to this dict without syncing to TypeDB will cause inconsistency
_sessions_store: Dict[str, Dict[str, Any]] = {}

# Chat sessions store (ORCH-006)
_chat_sessions: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# TYPEDB-FIRST DATA ACCESS (Per GAP-STUB-001/002/003/004)
# =============================================================================

class TypeDBUnavailable(Exception):
    """Raised when TypeDB is required but unavailable."""
    pass


def get_all_tasks_from_typedb(
    status: str = None,
    phase: str = None,
    agent_id: str = None,
    allow_fallback: bool = False
) -> List[Dict[str, Any]]:
    """
    Get all tasks from TypeDB (source of truth).

    Per GAP-STUB-001/002: TypeDB is the primary data source for tasks.

    Args:
        status: Optional filter by status
        phase: Optional filter by phase
        agent_id: Optional filter by agent
        allow_fallback: If True, fallback to in-memory when TypeDB unavailable

    Returns:
        List of task dicts

    Raises:
        TypeDBUnavailable: If TypeDB is down and allow_fallback=False
    """
    client = get_typedb_client()

    if client:
        try:
            tasks = client.get_all_tasks(status=status, phase=phase, agent_id=agent_id)
            # Convert to dict format for API compatibility
            return [_task_to_dict(t) for t in tasks]
        except Exception as e:
            logger.warning(f"TypeDB task query failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        # Fallback to in-memory (deprecated path)
        logger.warning("Using deprecated in-memory fallback for tasks")
        tasks = list(_tasks_store.values())
        if phase:
            tasks = [t for t in tasks if t.get("phase") == phase]
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if agent_id:
            tasks = [t for t in tasks if t.get("agent_id") == agent_id]
        return tasks

    raise TypeDBUnavailable("TypeDB client not available")


def get_task_from_typedb(task_id: str, allow_fallback: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a specific task from TypeDB.

    Per GAP-STUB-001/002: TypeDB is the primary data source for tasks.
    """
    client = get_typedb_client()

    if client:
        try:
            task = client.get_task(task_id)
            if task:
                return _task_to_dict(task)
            return None
        except Exception as e:
            logger.warning(f"TypeDB task get failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for task get")
        return _tasks_store.get(task_id)

    raise TypeDBUnavailable("TypeDB client not available")


def get_all_sessions_from_typedb(allow_fallback: bool = False) -> List[Dict[str, Any]]:
    """
    Get all sessions from TypeDB (source of truth).

    Per GAP-STUB-003/004: TypeDB is the primary data source for sessions.
    """
    client = get_typedb_client()

    if client:
        try:
            sessions = client.get_all_sessions()
            return [_session_to_dict(s) for s in sessions]
        except Exception as e:
            logger.warning(f"TypeDB session query failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for sessions")
        return list(_sessions_store.values())

    raise TypeDBUnavailable("TypeDB client not available")


def get_session_from_typedb(session_id: str, allow_fallback: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a specific session from TypeDB.

    Per GAP-STUB-003/004: TypeDB is the primary data source for sessions.
    """
    client = get_typedb_client()

    if client:
        try:
            session = client.get_session(session_id)
            if session:
                return _session_to_dict(session)
            return None
        except Exception as e:
            logger.warning(f"TypeDB session get failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for session get")
        return _sessions_store.get(session_id)

    raise TypeDBUnavailable("TypeDB client not available")


def get_task_count(allow_fallback: bool = True) -> int:
    """Get total task count from TypeDB or fallback."""
    try:
        tasks = get_all_tasks_from_typedb(allow_fallback=allow_fallback)
        return len(tasks)
    except TypeDBUnavailable:
        return 0


def get_session_count(allow_fallback: bool = True) -> int:
    """Get total session count from TypeDB or fallback."""
    try:
        sessions = get_all_sessions_from_typedb(allow_fallback=allow_fallback)
        return len(sessions)
    except TypeDBUnavailable:
        return 0


def _task_to_dict(task) -> Dict[str, Any]:
    """Convert TypeDB Task entity to dict format."""
    return {
        "task_id": task.id,
        "description": task.name or task.description or "",
        "phase": task.phase,
        "status": task.status,
        "agent_id": task.agent_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "body": task.body,
        "linked_rules": task.linked_rules,
        "linked_sessions": task.linked_sessions,
        "gap_id": task.gap_id,
        "evidence": task.evidence
    }


def _session_to_dict(session) -> Dict[str, Any]:
    """Convert TypeDB Session entity to dict format."""
    return {
        "session_id": session.id,
        "start_time": session.started_at.isoformat() if session.started_at else datetime.now().isoformat(),
        "end_time": session.completed_at.isoformat() if session.completed_at else None,
        "status": session.status,
        "tasks_completed": session.tasks_completed or 0,
        "agent_id": session.agent_id,
        "description": session.description,
        "file_path": session.file_path,
        "evidence_files": session.evidence_files,
        "linked_rules_applied": session.linked_rules_applied,
        "linked_decisions": session.linked_decisions
    }


# =============================================================================
# AGENT CONFIGURATION AND METRICS
# =============================================================================

_AGENT_METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "agent_metrics.json")

# Base agent definitions (static config - fallback if TypeDB unavailable)
_AGENT_BASE_CONFIG = {
    "task-orchestrator": {"name": "Task Orchestrator", "agent_type": "orchestrator", "base_trust": 0.95},
    "rules-curator": {"name": "Rules Curator", "agent_type": "curator", "base_trust": 0.90},
    "research-agent": {"name": "Research Agent", "agent_type": "researcher", "base_trust": 0.85},
    "code-agent": {"name": "Code Agent", "agent_type": "coder", "base_trust": 0.88},
    "local-assistant": {"name": "Local Assistant", "agent_type": "assistant", "base_trust": 0.92},
}


def _load_agent_metrics() -> Dict[str, Dict[str, Any]]:
    """Load persistent agent metrics from JSON file. Per P11.9."""
    metrics = {}
    if os.path.exists(_AGENT_METRICS_FILE):
        try:
            with open(_AGENT_METRICS_FILE, "r") as f:
                metrics = json.load(f)
        except Exception:
            pass
    return metrics


def _save_agent_metrics(metrics: Dict[str, Any]) -> None:
    """Save agent metrics to JSON file. Per P11.9."""
    os.makedirs(os.path.dirname(_AGENT_METRICS_FILE), exist_ok=True)
    with open(_AGENT_METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)


def _calculate_trust_score(agent_id: str, tasks_executed: int, base_trust: float) -> float:
    """
    Calculate trust score from real metrics.
    Per P11.9: GAP-AGENT-001 fix.

    Formula: base_trust * (1 + log10(tasks + 1) * 0.05)
    - New agents start at base_trust
    - Trust increases logarithmically with tasks executed
    - Max boost is ~15% after 1000 tasks
    """
    if tasks_executed == 0:
        return base_trust
    # Logarithmic growth: more tasks = higher trust, but diminishing returns
    task_boost = math.log10(tasks_executed + 1) * 0.05
    return min(1.0, base_trust * (1 + task_boost))


def _update_agent_metrics_on_claim(agent_id: str) -> None:
    """
    Update agent metrics when a task is claimed.
    Per P11.9: Centralized agent metrics update.
    """
    if agent_id in _agents_store:
        _agents_store[agent_id]["tasks_executed"] += 1
        _agents_store[agent_id]["last_active"] = datetime.now().isoformat()

        # Recalculate trust score
        base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
        _agents_store[agent_id]["trust_score"] = _calculate_trust_score(
            agent_id,
            _agents_store[agent_id]["tasks_executed"],
            base_trust
        )

        # Persist metrics
        metrics = _load_agent_metrics()
        metrics[agent_id] = {
            "tasks_executed": _agents_store[agent_id]["tasks_executed"],
            "last_active": _agents_store[agent_id]["last_active"]
        }
        _save_agent_metrics(metrics)


def _build_agents_store() -> Dict[str, Dict[str, Any]]:
    """Build agents store with persistent metrics merged with base config."""
    metrics = _load_agent_metrics()
    agents = {}

    for agent_id, config in _AGENT_BASE_CONFIG.items():
        agent_metrics = metrics.get(agent_id, {})
        tasks_executed = agent_metrics.get("tasks_executed", 0)
        last_active = agent_metrics.get("last_active", None)

        agents[agent_id] = {
            "agent_id": agent_id,
            "name": config["name"],
            "agent_type": config["agent_type"],
            "status": "ACTIVE",
            "tasks_executed": tasks_executed,
            "trust_score": _calculate_trust_score(agent_id, tasks_executed, config["base_trust"]),
            "last_active": last_active
        }

    return agents


# Initialize agents store with persistent metrics
_agents_store: Dict[str, Dict[str, Any]] = _build_agents_store()


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
    import uuid
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
    import re
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}-\d+)', filename)
    return match.group(1) if match else None


# =============================================================================
# CHAT HELPERS
# =============================================================================

def generate_chat_session_id() -> str:
    """Generate a chat session ID."""
    import uuid
    return f"CHAT-{uuid.uuid4().hex[:8].upper()}"


def get_available_agents_for_chat() -> List[Dict[str, Any]]:
    """Get agents available for chat."""
    return list(_agents_store.values())
