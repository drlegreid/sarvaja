#!/usr/bin/env python3
"""
Todo → Gov-Tasks Sync Hook - PostToolUse:TodoWrite

Per GAP-TASK-SYNC-001: Auto-sync Claude TodoWrite entries to gov-tasks MCP.
Per WORKFLOW-AUTO-01-v1: Silent fail, never block workflow.

When Claude calls TodoWrite, this hook reads the todo items from
CLAUDE_TOOL_INPUT and syncs completed/in-progress items to gov-tasks
via the REST API at localhost:8082.

Usage:
    Configured in .claude/settings.local.json PostToolUse matcher "TodoWrite"
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
STATE_FILE = HOOKS_DIR / ".todo_sync_state.json"
API_BASE = os.environ.get("SARVAJA_API_URL", "http://localhost:8082")


def _warn(message: str) -> None:
    """Write warning to stderr (visible to Claude Code model).

    Per GOV-MCP-FIRST-01-v1: Make sync failures visible so model
    is nudged toward direct MCP tool usage.
    """
    sys.stderr.write(f"[TODO-SYNC WARN] {message}\n")
    sys.stderr.flush()


def _load_state() -> dict:
    """Load last synced state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"synced_todos": {}, "last_sync": None}


def _save_state(state: dict) -> None:
    """Save sync state."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _sync_todo_to_api(todo: dict, state: dict) -> bool:
    """Sync a single todo item to gov-tasks REST API.

    Returns True if synced successfully.
    """
    try:
        import httpx
    except ImportError:
        return False

    content = todo.get("content", "").strip()
    status = todo.get("status", "pending")

    if not content:
        return False

    # Map TodoWrite status to gov-tasks status
    status_map = {
        "pending": "TODO",
        "in_progress": "IN_PROGRESS",
        "completed": "DONE",
    }
    gov_status = status_map.get(status, "TODO")

    # Generate a stable task_id from content
    task_id = "TODO-" + content[:40].replace(" ", "-").replace(":", "").upper()

    # Check if already synced with same status
    prev = state.get("synced_todos", {}).get(task_id)
    if prev and prev.get("status") == gov_status:
        return True  # Already synced

    try:
        with httpx.Client(timeout=3.0) as client:
            # Try to update existing task first
            resp = client.get(f"{API_BASE}/api/tasks/{task_id}")
            if resp.status_code == 200:
                # Task exists, update status
                client.patch(
                    f"{API_BASE}/api/tasks/{task_id}",
                    json={"status": gov_status, "description": content},
                )
            elif resp.status_code == 404:
                # Create new task
                client.post(
                    f"{API_BASE}/api/tasks",
                    json={
                        "task_id": task_id,
                        "description": content,
                        "phase": "implementation",
                        "status": gov_status,
                        "agent_id": "code-agent",
                    },
                )

        # Record sync
        state.setdefault("synced_todos", {})[task_id] = {
            "status": gov_status,
            "content": content,
            "synced_at": datetime.now().isoformat(),
        }
        return True
    except Exception:
        return False


def main() -> int:
    """Process TodoWrite tool output and sync to gov-tasks."""
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        data = json.loads(tool_input)
    except json.JSONDecodeError:
        return 0

    todos = data.get("todos", [])
    if not todos:
        return 0

    state = _load_state()
    synced = 0
    failed = 0

    for todo in todos:
        if _sync_todo_to_api(todo, state):
            synced += 1
        else:
            failed += 1

    state["last_sync"] = datetime.now().isoformat()
    state["last_count"] = len(todos)
    state["last_synced"] = synced
    state["last_failed"] = failed
    _save_state(state)

    if failed > 0:
        _warn(
            f"{failed}/{len(todos)} tasks failed to sync to TypeDB. "
            f"Use mcp__gov-tasks__task_create() for reliable persistence."
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block workflow, but make failure visible
        _warn(f"Hook error: {str(e)[:100]}. Tasks NOT synced to TypeDB.")
        sys.exit(0)
