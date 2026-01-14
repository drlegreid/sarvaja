"""
Agent Status Checker - Multi-Agent Observability
=================================================
Per MULTI-007: Implement monitoring for multi-agent workflows.

Detects:
- Stuck agents (no heartbeat >5 min)
- Agent activity tracking
- File lock monitoring

Status File: .claude/agents/AGENT_STATUS.json
Lock Directory: .claude/agents/.agent-locks/

Created: 2026-01-14
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration
STUCK_THRESHOLD_SECONDS = 300  # 5 minutes
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STATUS_FILE = PROJECT_ROOT / ".claude" / "agents" / "AGENT_STATUS.json"
LOCKS_DIR = PROJECT_ROOT / ".claude" / "agents" / ".agent-locks"


def ensure_dirs() -> None:
    """Ensure agent directories exist."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)


def load_agent_status() -> Dict[str, Any]:
    """Load current agent status from file."""
    if not STATUS_FILE.exists():
        return {"agents": {}, "last_updated": None}
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"agents": {}, "last_updated": None}


def save_agent_status(status: Dict[str, Any]) -> None:
    """Save agent status to file."""
    ensure_dirs()
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def update_agent_heartbeat(
    agent_id: str,
    agent_type: str = "unknown",
    current_task: Optional[str] = None,
    status: str = "active"
) -> Dict[str, Any]:
    """
    Update agent heartbeat - call this periodically from agents.

    Args:
        agent_id: Unique agent identifier
        agent_type: Agent type (claude-code, docker-agent, etc.)
        current_task: Current task being worked on
        status: Agent status (active, idle, blocked)

    Returns:
        Updated agent status dict
    """
    all_status = load_agent_status()

    all_status["agents"][agent_id] = {
        "agent_type": agent_type,
        "last_heartbeat": datetime.now().isoformat(),
        "current_task": current_task,
        "status": status,
        "heartbeat_count": all_status["agents"].get(agent_id, {}).get("heartbeat_count", 0) + 1
    }

    save_agent_status(all_status)
    return all_status["agents"][agent_id]


def check_stuck_agents() -> List[Dict[str, Any]]:
    """
    Check for agents that haven't sent heartbeat in >5 minutes.

    Returns:
        List of stuck agent info dicts
    """
    all_status = load_agent_status()
    stuck_agents = []
    now = time.time()

    for agent_id, agent_info in all_status.get("agents", {}).items():
        last_heartbeat = agent_info.get("last_heartbeat")
        if not last_heartbeat:
            continue

        try:
            heartbeat_time = datetime.fromisoformat(last_heartbeat)
            age_seconds = now - heartbeat_time.timestamp()

            if age_seconds > STUCK_THRESHOLD_SECONDS:
                stuck_agents.append({
                    "agent_id": agent_id,
                    "agent_type": agent_info.get("agent_type", "unknown"),
                    "last_heartbeat": last_heartbeat,
                    "stuck_duration_seconds": int(age_seconds),
                    "stuck_duration_human": f"{int(age_seconds / 60)} min {int(age_seconds % 60)} sec",
                    "last_task": agent_info.get("current_task"),
                    "severity": "CRITICAL" if age_seconds > 600 else "WARNING"
                })
        except (ValueError, TypeError):
            continue

    return stuck_agents


def check_file_locks() -> List[Dict[str, Any]]:
    """
    Check for stale file locks (held >2 minutes).

    Returns:
        List of stale lock info dicts
    """
    ensure_dirs()
    stale_locks = []
    now = time.time()
    lock_threshold = 120  # 2 minutes

    if not LOCKS_DIR.exists():
        return []

    for lock_file in LOCKS_DIR.glob("*.lock"):
        try:
            # Check file age
            age_seconds = now - lock_file.stat().st_mtime

            if age_seconds > lock_threshold:
                # Try to read lock content for agent info
                try:
                    with open(lock_file, "r") as f:
                        lock_info = json.load(f)
                except (json.JSONDecodeError, IOError):
                    lock_info = {}

                stale_locks.append({
                    "file": lock_file.name,
                    "locked_resource": lock_file.stem,
                    "held_by": lock_info.get("agent_id", "unknown"),
                    "lock_time": lock_info.get("acquired_at"),
                    "age_seconds": int(age_seconds),
                    "age_human": f"{int(age_seconds / 60)} min {int(age_seconds % 60)} sec",
                    "severity": "CRITICAL" if age_seconds > 300 else "WARNING"
                })
        except (OSError, IOError):
            continue

    return stale_locks


def acquire_file_lock(
    resource: str,
    agent_id: str,
    timeout_seconds: int = 30
) -> Optional[Path]:
    """
    Acquire a file lock for a resource.

    Args:
        resource: Resource name to lock (e.g., "TODO.md", "GAP-INDEX.md")
        agent_id: Agent acquiring the lock
        timeout_seconds: How long to try before giving up

    Returns:
        Lock file path if acquired, None if failed
    """
    ensure_dirs()
    lock_file = LOCKS_DIR / f"{resource}.lock"

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if not lock_file.exists():
            # Try to create lock
            try:
                lock_info = {
                    "agent_id": agent_id,
                    "resource": resource,
                    "acquired_at": datetime.now().isoformat()
                }
                with open(lock_file, "x") as f:
                    json.dump(lock_info, f)
                return lock_file
            except FileExistsError:
                # Race condition, someone else got it
                pass
        time.sleep(0.5)

    return None


def release_file_lock(resource: str, agent_id: str) -> bool:
    """
    Release a file lock.

    Args:
        resource: Resource name to unlock
        agent_id: Agent releasing the lock (must match acquirer)

    Returns:
        True if released, False if not owner or not exists
    """
    lock_file = LOCKS_DIR / f"{resource}.lock"

    if not lock_file.exists():
        return False

    try:
        with open(lock_file, "r") as f:
            lock_info = json.load(f)

        if lock_info.get("agent_id") != agent_id:
            return False  # Not the owner

        lock_file.unlink()
        return True
    except (json.JSONDecodeError, IOError, OSError):
        return False


def get_agent_status_summary() -> Dict[str, Any]:
    """
    Get complete agent status summary for dashboard.

    Returns:
        Dict with agents, stuck_agents, stale_locks, alerts
    """
    all_status = load_agent_status()
    stuck_agents = check_stuck_agents()
    stale_locks = check_file_locks()

    # Build alerts
    alerts = []
    for agent in stuck_agents:
        alerts.append({
            "type": "STUCK_AGENT",
            "severity": agent["severity"],
            "message": f"Agent {agent['agent_id']} stuck for {agent['stuck_duration_human']}",
            "details": agent
        })

    for lock in stale_locks:
        alerts.append({
            "type": "STALE_LOCK",
            "severity": lock["severity"],
            "message": f"Lock on {lock['locked_resource']} held for {lock['age_human']}",
            "details": lock
        })

    return {
        "agents": all_status.get("agents", {}),
        "agent_count": len(all_status.get("agents", {})),
        "stuck_agents": stuck_agents,
        "stuck_count": len(stuck_agents),
        "stale_locks": stale_locks,
        "stale_lock_count": len(stale_locks),
        "alerts": alerts,
        "alert_count": len(alerts),
        "last_updated": all_status.get("last_updated"),
        "status": "OK" if not alerts else ("CRITICAL" if any(a["severity"] == "CRITICAL" for a in alerts) else "WARNING")
    }


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "heartbeat" and len(sys.argv) >= 3:
            agent_id = sys.argv[2]
            task = sys.argv[3] if len(sys.argv) > 3 else None
            result = update_agent_heartbeat(agent_id, "cli-test", task, "active")
            print(json.dumps(result, indent=2))

        elif cmd == "status":
            result = get_agent_status_summary()
            print(json.dumps(result, indent=2))

        elif cmd == "stuck":
            stuck = check_stuck_agents()
            print(json.dumps(stuck, indent=2))

        elif cmd == "locks":
            locks = check_file_locks()
            print(json.dumps(locks, indent=2))

        else:
            print("Usage: python agent_status.py [heartbeat <agent_id> [task] | status | stuck | locks]")
    else:
        # Default: show status
        result = get_agent_status_summary()
        print(json.dumps(result, indent=2))
