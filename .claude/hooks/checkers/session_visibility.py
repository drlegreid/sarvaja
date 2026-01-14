"""
Session Visibility Module - Track Session-Task-Rule Relationships
==================================================================
Per user request: Visibility for agentic platform work.

Features:
1. Session logs mapped to tasks
2. Rules applied in agent work context
3. Token usage tracking (via Anthropic API)

Created: 2026-01-14
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VISIBILITY_FILE = PROJECT_ROOT / ".claude" / "agents" / "SESSION_VISIBILITY.json"
ENV_FILE = PROJECT_ROOT / ".env"


@dataclass
class TaskContext:
    """Task being worked on with associated rules and session."""
    task_id: str
    task_name: str
    session_id: str
    started_at: str
    rules_applied: List[str]
    tool_calls: List[Dict[str, Any]]
    status: str = "in_progress"
    completed_at: Optional[str] = None
    tokens_used: int = 0


def load_env_var(var_name: str) -> Optional[str]:
    """Load environment variable from .env file."""
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{var_name}="):
                        # Handle quoted values
                        value = line.split("=", 1)[1].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        return value
        except Exception:
            pass
    return os.getenv(var_name)


def ensure_dirs() -> None:
    """Ensure visibility directories exist."""
    VISIBILITY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_visibility() -> Dict[str, Any]:
    """Load current visibility state."""
    if not VISIBILITY_FILE.exists():
        return {
            "current_session": None,
            "active_tasks": {},
            "completed_tasks": [],
            "token_usage": {"total": 0, "by_session": {}},
            "last_updated": None
        }
    try:
        with open(VISIBILITY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "current_session": None,
            "active_tasks": {},
            "completed_tasks": [],
            "token_usage": {"total": 0, "by_session": {}},
            "last_updated": None
        }


def save_visibility(state: Dict[str, Any]) -> None:
    """Save visibility state."""
    ensure_dirs()
    state["last_updated"] = datetime.now().isoformat()
    with open(VISIBILITY_FILE, "w") as f:
        json.dump(state, f, indent=2)


def start_session(session_id: str) -> Dict[str, Any]:
    """Start tracking a new session."""
    state = load_visibility()
    state["current_session"] = {
        "session_id": session_id,
        "started_at": datetime.now().isoformat(),
        "tasks_worked": [],
        "rules_applied": [],
        "tool_calls": 0,
        "tokens_used": 0
    }
    save_visibility(state)
    return state["current_session"]


def start_task(
    task_id: str,
    task_name: str,
    session_id: Optional[str] = None
) -> TaskContext:
    """Start working on a task within the current session."""
    state = load_visibility()

    # Use current session if not specified
    if not session_id and state.get("current_session"):
        session_id = state["current_session"]["session_id"]

    task = TaskContext(
        task_id=task_id,
        task_name=task_name,
        session_id=session_id or "UNKNOWN",
        started_at=datetime.now().isoformat(),
        rules_applied=[],
        tool_calls=[]
    )

    state["active_tasks"][task_id] = asdict(task)

    # Update session's task list
    if state.get("current_session"):
        if task_id not in state["current_session"].get("tasks_worked", []):
            state["current_session"]["tasks_worked"].append(task_id)

    save_visibility(state)
    return task


def record_rule_application(
    task_id: str,
    rule_id: str,
    context: str = ""
) -> None:
    """Record that a rule was applied while working on a task."""
    state = load_visibility()

    if task_id in state["active_tasks"]:
        if rule_id not in state["active_tasks"][task_id]["rules_applied"]:
            state["active_tasks"][task_id]["rules_applied"].append(rule_id)

    # Also track at session level
    if state.get("current_session"):
        if rule_id not in state["current_session"].get("rules_applied", []):
            state["current_session"]["rules_applied"].append(rule_id)

    save_visibility(state)


def record_tool_call(
    task_id: str,
    tool_name: str,
    duration_ms: int = 0,
    rules_applied: List[str] = None,
    tokens: int = 0
) -> None:
    """Record a tool call within a task."""
    state = load_visibility()

    call_record = {
        "tool_name": tool_name,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": duration_ms,
        "rules_applied": rules_applied or [],
        "tokens": tokens
    }

    if task_id in state["active_tasks"]:
        state["active_tasks"][task_id]["tool_calls"].append(call_record)
        state["active_tasks"][task_id]["tokens_used"] += tokens

    # Update session metrics
    if state.get("current_session"):
        state["current_session"]["tool_calls"] = state["current_session"].get("tool_calls", 0) + 1
        state["current_session"]["tokens_used"] = state["current_session"].get("tokens_used", 0) + tokens

        # Track rules at session level
        for rule_id in (rules_applied or []):
            if rule_id not in state["current_session"].get("rules_applied", []):
                state["current_session"]["rules_applied"].append(rule_id)

    # Update global token usage
    state["token_usage"]["total"] += tokens
    session_id = state.get("current_session", {}).get("session_id", "unknown")
    state["token_usage"]["by_session"][session_id] = \
        state["token_usage"]["by_session"].get(session_id, 0) + tokens

    save_visibility(state)


def complete_task(task_id: str, status: str = "completed") -> Optional[Dict[str, Any]]:
    """Mark a task as complete and move to completed list."""
    state = load_visibility()

    if task_id not in state["active_tasks"]:
        return None

    task = state["active_tasks"].pop(task_id)
    task["status"] = status
    task["completed_at"] = datetime.now().isoformat()

    # Keep last 50 completed tasks
    state["completed_tasks"].insert(0, task)
    state["completed_tasks"] = state["completed_tasks"][:50]

    save_visibility(state)
    return task


def get_session_visibility() -> Dict[str, Any]:
    """Get full visibility report for current session."""
    state = load_visibility()

    return {
        "current_session": state.get("current_session"),
        "active_tasks": state.get("active_tasks", {}),
        "active_task_count": len(state.get("active_tasks", {})),
        "completed_tasks_recent": state.get("completed_tasks", [])[:10],
        "completed_task_count": len(state.get("completed_tasks", [])),
        "token_usage": state.get("token_usage", {}),
        "last_updated": state.get("last_updated")
    }


def get_task_rules_summary(task_id: str) -> Dict[str, Any]:
    """Get summary of rules applied for a specific task."""
    state = load_visibility()

    # Check active tasks
    if task_id in state.get("active_tasks", {}):
        task = state["active_tasks"][task_id]
        return {
            "task_id": task_id,
            "task_name": task.get("task_name"),
            "status": "active",
            "rules_applied": task.get("rules_applied", []),
            "rule_count": len(task.get("rules_applied", [])),
            "tool_calls": len(task.get("tool_calls", [])),
            "tokens_used": task.get("tokens_used", 0)
        }

    # Check completed tasks
    for task in state.get("completed_tasks", []):
        if task.get("task_id") == task_id:
            return {
                "task_id": task_id,
                "task_name": task.get("task_name"),
                "status": task.get("status"),
                "rules_applied": task.get("rules_applied", []),
                "rule_count": len(task.get("rules_applied", [])),
                "tool_calls": len(task.get("tool_calls", [])),
                "tokens_used": task.get("tokens_used", 0),
                "completed_at": task.get("completed_at")
            }

    return {"error": f"Task {task_id} not found"}


def get_token_usage_report() -> Dict[str, Any]:
    """Get token usage report."""
    state = load_visibility()
    token_usage = state.get("token_usage", {"total": 0, "by_session": {}})

    # Load API key status
    api_key = load_env_var("ANTHROPIC_API_KEY")
    has_api_key = bool(api_key and len(api_key) > 10)

    return {
        "total_tokens": token_usage.get("total", 0),
        "by_session": token_usage.get("by_session", {}),
        "api_key_configured": has_api_key,
        "tracking_enabled": has_api_key,
        "note": "Token tracking requires manual recording via record_tool_call()" if not has_api_key
                else "Token tracking active"
    }


# =============================================================================
# COMMIT INFO TRACKING (Per User Request: files changed per task)
# =============================================================================

def record_commit_info(
    task_id: str,
    commit_hash: str,
    files_changed: List[str],
    commit_message: str = ""
) -> None:
    """Record git commit info associated with a task.

    Per user request: Allow checking changed files from task.
    """
    state = load_visibility()

    commit_record = {
        "commit_hash": commit_hash,
        "files_changed": files_changed,
        "commit_message": commit_message,
        "recorded_at": datetime.now().isoformat()
    }

    # Store in active or completed task
    if task_id in state.get("active_tasks", {}):
        if "commits" not in state["active_tasks"][task_id]:
            state["active_tasks"][task_id]["commits"] = []
        state["active_tasks"][task_id]["commits"].append(commit_record)
    else:
        # Check completed tasks
        for task in state.get("completed_tasks", []):
            if task.get("task_id") == task_id:
                if "commits" not in task:
                    task["commits"] = []
                task["commits"].append(commit_record)
                break

    save_visibility(state)


def get_task_commit_info(task_id: str) -> Dict[str, Any]:
    """Get commit info and files changed for a task."""
    state = load_visibility()

    # Check active tasks
    if task_id in state.get("active_tasks", {}):
        task = state["active_tasks"][task_id]
        commits = task.get("commits", [])
        all_files = []
        for c in commits:
            all_files.extend(c.get("files_changed", []))
        return {
            "task_id": task_id,
            "commits": commits,
            "files_changed": list(set(all_files)),
            "commit_count": len(commits)
        }

    # Check completed tasks
    for task in state.get("completed_tasks", []):
        if task.get("task_id") == task_id:
            commits = task.get("commits", [])
            all_files = []
            for c in commits:
                all_files.extend(c.get("files_changed", []))
            return {
                "task_id": task_id,
                "commits": commits,
                "files_changed": list(set(all_files)),
                "commit_count": len(commits)
            }

    return {"error": f"Task {task_id} not found", "task_id": task_id}


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "start-session" and len(sys.argv) >= 3:
            result = start_session(sys.argv[2])
            print(json.dumps(result, indent=2))

        elif cmd == "start-task" and len(sys.argv) >= 4:
            result = start_task(sys.argv[2], sys.argv[3])
            print(json.dumps(asdict(result), indent=2))

        elif cmd == "apply-rule" and len(sys.argv) >= 4:
            record_rule_application(sys.argv[2], sys.argv[3])
            print(f"Rule {sys.argv[3]} applied to task {sys.argv[2]}")

        elif cmd == "complete-task" and len(sys.argv) >= 3:
            result = complete_task(sys.argv[2])
            print(json.dumps(result, indent=2))

        elif cmd == "status":
            result = get_session_visibility()
            print(json.dumps(result, indent=2))

        elif cmd == "tokens":
            result = get_token_usage_report()
            print(json.dumps(result, indent=2))

        else:
            print("Usage: python session_visibility.py [start-session|start-task|apply-rule|complete-task|status|tokens]")
    else:
        result = get_session_visibility()
        print(json.dumps(result, indent=2))
