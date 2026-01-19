"""
Governance Compatibility Module
===============================
Provides standalone tool functions for testing and backward compatibility.

These wrapper functions can be called directly without MCP registration.
They use the same implementation as the MCP tools but are importable.

Per GAP-MCP-NAMING-001: Migration complete - new names only.
"""

import json
from dataclasses import asdict
from typing import Optional

from governance.mcp_tools.common import get_typedb_client


# =============================================================================
# AGENT TOOLS
# =============================================================================

def agent_create(agent_id: str, name: str, agent_type: str,
                 trust_score: float = 0.8) -> str:
    """Create a new agent in TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        success = client.insert_agent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            trust_score=trust_score
        )

        if success:
            return json.dumps({
                "agent_id": agent_id,
                "name": name,
                "agent_type": agent_type,
                "trust_score": trust_score,
                "message": f"Agent {agent_id} created successfully"
            }, indent=2)
        else:
            return json.dumps({"error": f"Failed to create agent {agent_id}"})
    finally:
        client.close()


def agent_get(agent_id: str) -> str:
    """Get agent by ID from TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        agent = client.get_agent(agent_id)
        if agent:
            return json.dumps(asdict(agent), indent=2, default=str)
        else:
            return json.dumps({"error": f"Agent {agent_id} not found"})
    finally:
        client.close()


def agents_list() -> str:
    """List all agents from TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        agents = client.get_all_agents()
        return json.dumps({
            "agents": [asdict(a) for a in agents],
            "count": len(agents),
            "source": "typedb"
        }, indent=2, default=str)
    finally:
        client.close()


def agent_trust_update(agent_id: str, trust_score: float) -> str:
    """Update agent trust score."""
    if not 0.0 <= trust_score <= 1.0:
        return json.dumps({"error": "Trust score must be between 0.0 and 1.0"})

    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        success = client.update_agent_trust(
            agent_id=agent_id,
            trust_score=trust_score
        )

        if success:
            agent = client.get_agent(agent_id)
            if agent:
                result = asdict(agent)
                result["message"] = f"Agent {agent_id} trust updated to {trust_score}"
                return json.dumps(result, indent=2, default=str)
            return json.dumps({
                "agent_id": agent_id,
                "trust_score": trust_score,
                "message": f"Agent {agent_id} trust updated"
            }, indent=2)
        else:
            return json.dumps({"error": f"Failed to update agent {agent_id}"})
    finally:
        client.close()


# =============================================================================
# TASK TOOLS
# =============================================================================

def task_create(task_id: str, name: str, description: str = "",
                phase: str = "P10", priority: str = "MEDIUM",
                status: str = "pending") -> str:
    """Create a new task in TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        success = client.insert_task(
            task_id=task_id,
            name=name,
            status=status,
            priority=priority,
            phase=phase
        )

        if success:
            return json.dumps({
                "task_id": task_id,
                "name": name,
                "status": status,
                "priority": priority,
                "phase": phase,
                "message": f"Task {task_id} created successfully"
            }, indent=2)
        else:
            return json.dumps({"error": f"Failed to create task {task_id}"})
    finally:
        client.close()


def task_get(task_id: str) -> str:
    """Get task by ID from TypeDB."""
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


def tasks_list() -> str:
    """List all tasks from TypeDB."""
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


def task_update(task_id: str, name: Optional[str] = None,
                status: Optional[str] = None, phase: Optional[str] = None) -> str:
    """Update task in TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        success = client.update_task(
            task_id=task_id,
            name=name,
            status=status,
            phase=phase
        )

        if success:
            task = client.get_task(task_id)
            if task:
                result = asdict(task)
                result["message"] = f"Task {task_id} updated"
                return json.dumps(result, indent=2, default=str)
            return json.dumps({
                "task_id": task_id,
                "message": f"Task {task_id} updated"
            }, indent=2)
        else:
            return json.dumps({"error": f"Failed to update task {task_id}"})
    finally:
        client.close()


def task_delete(task_id: str) -> str:
    """Delete task from TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        success = client.delete_task(task_id)

        if success:
            return json.dumps({
                "task_id": task_id,
                "message": f"Task {task_id} deleted successfully"
            }, indent=2)
        else:
            return json.dumps({"error": f"Failed to delete task {task_id}"})
    finally:
        client.close()


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES (for legacy test imports)
# =============================================================================

# Agent aliases
governance_create_agent = agent_create
governance_get_agent = agent_get
governance_list_agents = agents_list
governance_update_agent_trust = agent_trust_update

# Task aliases
governance_create_task = task_create
governance_get_task = task_get
governance_list_all_tasks = tasks_list
governance_update_task = task_update
governance_delete_task = task_delete


# =============================================================================
# EVIDENCE/SESSION TOOLS
# =============================================================================

def governance_list_sessions(limit: int = 20, session_type: Optional[str] = None) -> str:
    """List session evidence files."""
    import glob
    from pathlib import Path

    EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"
    sessions = []

    pattern = EVIDENCE_DIR / "SESSION-*.md"
    for filepath in sorted(glob.glob(str(pattern)), reverse=True)[:limit]:
        try:
            path = Path(filepath)
            filename = path.name
            # Extract session ID from filename
            session_id = filename.replace(".md", "")
            sessions.append({
                "session_id": session_id,
                "file": str(path),
                "source": "evidence"
            })
        except Exception:
            pass

    return json.dumps({
        "sessions": sessions,
        "count": len(sessions)
    }, indent=2)


def governance_get_session(session_id: str) -> str:
    """Get session evidence content."""
    from pathlib import Path

    EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"
    filepath = EVIDENCE_DIR / f"{session_id}.md"

    if filepath.exists():
        content = filepath.read_text()
        return json.dumps({
            "session_id": session_id,
            "content": content[:5000],  # Truncate for safety
            "file": str(filepath)
        }, indent=2)
    else:
        return json.dumps({"error": f"Session {session_id} not found"})


def governance_list_decisions() -> str:
    """List strategic decisions from TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        decisions = client.get_all_decisions()
        return json.dumps({
            "decisions": [asdict(d) for d in decisions] if decisions else [],
            "count": len(decisions) if decisions else 0
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "decisions": [], "count": 0})
    finally:
        client.close()


def governance_get_decision(decision_id: str) -> str:
    """Get decision details from TypeDB."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        decision = client.get_decision(decision_id)
        if decision:
            return json.dumps(asdict(decision), indent=2, default=str)
        else:
            return json.dumps({"error": f"Decision {decision_id} not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        client.close()


def governance_list_tasks(phase: Optional[str] = None, status: Optional[str] = None) -> str:
    """List tasks with optional filters."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        tasks = client.get_all_tasks()

        # Apply filters
        if phase:
            tasks = [t for t in tasks if getattr(t, 'phase', '') == phase]
        if status:
            tasks = [t for t in tasks if getattr(t, 'status', '') == status]

        return json.dumps({
            "tasks": [asdict(t) for t in tasks],
            "count": len(tasks),
            "filters": {"phase": phase, "status": status}
        }, indent=2, default=str)
    finally:
        client.close()


def governance_get_task_deps(task_id: str) -> str:
    """Get task dependencies."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        deps = client.get_task_dependencies(task_id)
        return json.dumps({
            "task_id": task_id,
            "blocked_by": deps.get("blocked_by", []),
            "blocks": deps.get("blocks", [])
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "task_id": task_id,
            "blocked_by": [],
            "blocks": [],
            "note": str(e)
        }, indent=2)
    finally:
        client.close()
