"""
Agent Observability Routes (MULTI-007).

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/routes/agents.py

Created: 2026-01-14
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agent Observability"])

# Import agent status checker for MULTI-007 observability
_hooks_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "hooks" / "checkers"
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

try:
    from agent_status import (
        get_agent_status_summary,
        update_agent_heartbeat,
        check_stuck_agents,
        check_file_locks,
        acquire_file_lock,
        release_file_lock
    )
    AGENT_STATUS_AVAILABLE = True
except ImportError:
    AGENT_STATUS_AVAILABLE = False


@router.get("/agents/status/summary")
async def get_agents_status_summary():
    """
    Get agent observability summary.

    Per MULTI-007: Monitoring for multi-agent workflows.
    Includes: stuck agents, stale locks, alerts.
    """
    if not AGENT_STATUS_AVAILABLE:
        return {
            "error": "Agent status checker not available",
            "status": "UNAVAILABLE"
        }

    return get_agent_status_summary()


@router.get("/agents/status/stuck")
async def get_stuck_agents():
    """
    Get agents that haven't sent heartbeat in >5 minutes.

    Per MULTI-007: Agent stuck detection.
    """
    if not AGENT_STATUS_AVAILABLE:
        return {"stuck_agents": [], "error": "Agent status checker not available"}

    return {"stuck_agents": check_stuck_agents()}


@router.get("/agents/status/locks")
async def get_stale_locks():
    """
    Get file locks held for >2 minutes.

    Per MULTI-007: File lock monitoring.
    """
    if not AGENT_STATUS_AVAILABLE:
        return {"stale_locks": [], "error": "Agent status checker not available"}

    return {"stale_locks": check_file_locks()}


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    agent_type: str = "unknown",
    current_task: Optional[str] = None,
    status: str = "active"
):
    """
    Register agent heartbeat.

    Per MULTI-007: Agent activity tracking.
    Call this periodically from agents to indicate they're alive.
    """
    if not AGENT_STATUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent status checker not available")

    result = update_agent_heartbeat(agent_id, agent_type, current_task, status)
    return {"agent_id": agent_id, "heartbeat": result}


@router.post("/agents/locks/acquire")
async def acquire_lock(resource: str, agent_id: str, timeout: int = 30):
    """
    Acquire a file lock.

    Per MULTI-007: File lock management.
    """
    if not AGENT_STATUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent status checker not available")

    lock_path = acquire_file_lock(resource, agent_id, timeout)
    if lock_path:
        return {"acquired": True, "resource": resource, "agent_id": agent_id}
    raise HTTPException(status_code=409, detail=f"Could not acquire lock for {resource}")


@router.post("/agents/locks/release")
async def release_lock(resource: str, agent_id: str):
    """
    Release a file lock.

    Per MULTI-007: File lock management.
    """
    if not AGENT_STATUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent status checker not available")

    released = release_file_lock(resource, agent_id)
    if released:
        return {"released": True, "resource": resource, "agent_id": agent_id}
    raise HTTPException(status_code=404, detail=f"Lock not found or not owned by {agent_id}")
