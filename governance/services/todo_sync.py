"""
TypeDB → TODO.md One-Way Sync Service.

Per GOV-MCP-FIRST-01-v1 (MANDATORY): TypeDB is source of truth.
TODO.md is fallback visibility only. This service:
  1. sync_typedb_to_todomd() — fetches tasks from TypeDB API, writes TODO.md
  2. sync_fallback_to_typedb() — imports fallback tasks back on MCP recovery

Created: 2026-03-21 (EPIC-GOV-TASKS-V2 Phase 8)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Marker line that separates header from synced tasks
SYNC_SECTION_MARKER = "## Synced Tasks (TypeDB)"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    fetched: int = 0
    synced: int = 0
    failed: int = 0
    error: Optional[str] = None


def _format_task_line(task: dict) -> str:
    """Format a single task dict as a TODO.md line.

    Status mapping:
      TODO → - [ ]
      IN_PROGRESS → - [~]
      DONE → - [x]
    """
    status = task.get("status", "TODO").upper()
    task_id = task.get("task_id", "???")
    name = task.get("name", task.get("description", "Untitled"))
    priority = task.get("priority", "")

    checkbox = {"TODO": "- [ ]", "IN_PROGRESS": "- [~]", "DONE": "- [x]"}
    marker = checkbox.get(status, "- [ ]")

    priority_tag = f" **{priority}**" if priority else ""
    return f"{marker} `{task_id}`{priority_tag} {name}"


def sync_typedb_to_todomd(
    todo_md_path: str,
    api_base: str = "http://localhost:8082",
) -> SyncResult:
    """Fetch tasks from TypeDB API and write to TODO.md.

    Preserves the existing header content above the sync section marker.
    Replaces everything below the marker with fresh TypeDB data.
    """
    try:
        import httpx
    except ImportError:
        return SyncResult(error="httpx not installed")

    result = SyncResult()

    # Fetch tasks from API
    try:
        resp = httpx.get(
            f"{api_base}/api/tasks",
            params={"limit": 200},
            timeout=5.0,
        )
        if resp.status_code != 200:
            result.error = f"API returned {resp.status_code}"
            return result

        data = resp.json()
        tasks = data.get("tasks", [])
        result.fetched = len(tasks)
    except Exception as e:
        result.error = str(e)
        return result

    # Read existing TODO.md to preserve header
    todo_path = Path(todo_md_path)
    header = ""
    if todo_path.exists():
        content = todo_path.read_text()
        if SYNC_SECTION_MARKER in content:
            header = content[:content.index(SYNC_SECTION_MARKER)]
        else:
            header = content.rstrip() + "\n\n"

    # Group tasks by status
    by_status = {"TODO": [], "IN_PROGRESS": [], "DONE": []}
    for t in tasks:
        status = t.get("status", "TODO").upper()
        by_status.setdefault(status, []).append(t)

    # Build synced section
    lines = [SYNC_SECTION_MARKER, ""]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"*Auto-synced from TypeDB at {ts} | {len(tasks)} tasks*\n")

    if by_status.get("IN_PROGRESS"):
        lines.append("### In Progress")
        for t in by_status["IN_PROGRESS"]:
            lines.append(_format_task_line(t))
        lines.append("")

    if by_status.get("TODO"):
        lines.append("### Todo")
        for t in by_status["TODO"]:
            lines.append(_format_task_line(t))
        lines.append("")

    if by_status.get("DONE"):
        lines.append("### Done")
        for t in by_status["DONE"]:
            lines.append(_format_task_line(t))
        lines.append("")

    # Write
    try:
        todo_path.write_text(header + "\n".join(lines) + "\n")
        result.synced = len(tasks)
    except Exception as e:
        result.error = f"Write failed: {e}"
        result.failed = len(tasks)

    return result


def sync_fallback_to_typedb(
    state_path: str,
    api_base: str = "http://localhost:8082",
) -> SyncResult:
    """Import tasks created during MCP outage back to TypeDB.

    Reads the todo_sync hook's state file for entries with
    source="fallback" and POSTs them to the TypeDB API.
    Marks successfully imported tasks as source="synced".
    """
    try:
        import httpx
    except ImportError:
        return SyncResult(error="httpx not installed")

    result = SyncResult()
    state_file = Path(state_path)

    if not state_file.exists():
        return result

    try:
        state = json.loads(state_file.read_text())
    except Exception as e:
        result.error = f"State read failed: {e}"
        return result

    synced_todos = state.get("synced_todos", {})
    fallback_tasks = {
        tid: info for tid, info in synced_todos.items()
        if info.get("source") == "fallback"
    }

    if not fallback_tasks:
        return result

    result.fetched = len(fallback_tasks)

    try:
        with httpx.Client(timeout=5.0) as client:
            for task_id, info in fallback_tasks.items():
                try:
                    # Check if task already exists in TypeDB
                    resp = client.get(f"{api_base}/api/tasks/{task_id}")
                    if resp.status_code == 200:
                        # Already exists — mark as synced
                        info["source"] = "synced"
                        result.synced += 1
                        continue

                    # Create task in TypeDB
                    post_resp = client.post(
                        f"{api_base}/api/tasks",
                        json={
                            "task_id": task_id,
                            "description": info.get("content", ""),
                            "status": info.get("status", "TODO"),
                            "agent_id": "code-agent",
                            "phase": "implementation",
                        },
                    )
                    if post_resp.is_success:
                        info["source"] = "synced"
                        info["synced_at"] = datetime.now().isoformat()
                        result.synced += 1
                    else:
                        result.failed += 1
                except Exception:
                    result.failed += 1
    except Exception as e:
        result.error = str(e)
        result.failed = result.fetched - result.synced
        return result

    # Persist updated state
    try:
        state_file.write_text(json.dumps(state, indent=2))
    except Exception:
        pass

    return result
