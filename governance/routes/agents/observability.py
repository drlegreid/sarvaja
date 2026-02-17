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

try:
    from conflict_checker import get_conflict_summary, check_merge_conflicts
    CONFLICT_CHECKER_AVAILABLE = True
except ImportError:
    CONFLICT_CHECKER_AVAILABLE = False


@router.get("/agents/status/summary")
async def get_agents_status_summary():
    """
    Get agent observability summary.

    Per MULTI-007: Monitoring for multi-agent workflows.
    Includes: stuck agents, stale locks, merge conflicts, alerts.
    """
    if not AGENT_STATUS_AVAILABLE:
        return {
            "error": "Agent status checker not available",
            "status": "UNAVAILABLE"
        }

    summary = get_agent_status_summary()

    # Add conflict status if available (MULTI-007 completion)
    if CONFLICT_CHECKER_AVAILABLE:
        conflict_summary = get_conflict_summary()
        summary["conflicts"] = conflict_summary.get("conflicts", [])
        summary["conflict_count"] = conflict_summary.get("conflict_count", 0)
        summary["has_conflicts"] = conflict_summary.get("has_conflicts", False)

        # BUG-224-OBS-001: Guard against missing "alerts" key
        alerts = summary.get("alerts", [])
        for alert in conflict_summary.get("alerts", []):
            alerts.append(alert)
        summary["alerts"] = alerts
        summary["alert_count"] = len(alerts)

        # Update overall status if conflicts found
        if conflict_summary.get("has_conflicts"):
            summary["status"] = "CRITICAL"

    return summary


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

    # BUG-294-OBS-003: Whitelist status and agent_type, cap current_task length
    _valid_statuses = {"active", "idle", "blocked", "unknown"}
    if status not in _valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of {sorted(_valid_statuses)}")
    _valid_types = {"claude-code", "docker-agent", "ci", "unknown"}
    if agent_type not in _valid_types:
        agent_type = "unknown"
    if current_task and len(current_task) > 512:
        current_task = current_task[:512]

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

    # BUG-294-OBS-001: Sanitize resource name to prevent path traversal
    import re as _re
    if not _re.match(r'^[A-Za-z0-9_\-\.]{1,128}$', resource):
        raise HTTPException(status_code=422, detail="Invalid resource name: must be alphanumeric/dash/dot, max 128 chars")
    # BUG-294-OBS-002: Cap timeout to prevent event loop blocking
    timeout = max(1, min(60, timeout))

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

    # BUG-325-OBS-001: Validate resource name (matches acquire_lock validation)
    import re as _re
    if not _re.match(r'^[A-Za-z0-9_\-\.]{1,128}$', resource):
        raise HTTPException(status_code=422, detail="Invalid resource name: must be alphanumeric/dash/dot, max 128 chars")

    released = release_file_lock(resource, agent_id)
    if released:
        return {"released": True, "resource": resource, "agent_id": agent_id}
    raise HTTPException(status_code=404, detail=f"Lock not found or not owned by {agent_id}")


@router.get("/agents/status/conflicts")
async def get_merge_conflicts():
    """
    Get git merge conflict status.

    Per MULTI-007: Merge conflict detection for multi-agent workflows.
    Detects unmerged files and conflict markers.
    """
    if not CONFLICT_CHECKER_AVAILABLE:
        return {
            "error": "Conflict checker not available",
            "has_conflicts": False,
            "conflicts": [],
            "status": "UNAVAILABLE"
        }

    return get_conflict_summary()


@router.get("/monitor/events")
async def get_monitor_events(
    days: int = 1,
    limit: int = 100,
    event_type: Optional[str] = None,
    severity: Optional[str] = None
):
    """
    Get monitor events from audit files.

    Per GAP-MONITOR-IPC-001: Cross-process event sharing via audit files.
    Enables Dashboard UI to display real events from MCP tools.

    Args:
        days: Number of days to read (1-7)
        limit: Max events to return (1-1000)
        event_type: Filter by event type
        severity: Filter by severity (INFO, WARNING, CRITICAL)
    """
    from agent.governance_ui.data_access.monitoring import read_audit_events

    # Validate parameters
    days = max(1, min(7, days))
    limit = max(1, min(1000, limit))

    events = read_audit_events(
        days=days,
        limit=limit,
        event_type=event_type,
        severity=severity
    )

    return {
        "events": events,
        "count": len(events),
        "filters": {
            "days": days,
            "limit": limit,
            "event_type": event_type,
            "severity": severity
        }
    }
