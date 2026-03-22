"""Task ID Auto-Generation Service (META-TAXON-01-v1 + FIX-NOM-001/002).

Generates sequential task IDs based on task type prefix.
Pattern without project: {TYPE}-{NNN} (e.g., BUG-001)
Pattern with project:    {PROJECT}-{TYPE}-{NNN} (e.g., SARVAJA-BUG-001)

Per DOC-SIZE-01-v1: Single responsibility module.
"""
import re
import logging
from typing import Optional

from agent.governance_ui.state.constants import TASK_TYPE_PREFIX

logger = logging.getLogger(__name__)

# Known project_id prefixes to strip (common patterns like PROJ-)
_STRIP_PREFIXES = ("PROJ-",)

# In-memory counters as fallback when TypeDB is unavailable
_counters: dict = {}


def derive_project_prefix(project_id: Optional[str]) -> str:
    """Derive a short uppercase prefix from a project_id.

    Examples:
        "sarvaja-platform" → "SARVAJA"
        "PROJ-GAMEDEV"     → "GAMEDEV"
        "jobhunt-2026"     → "JOBHUNT"
        "myproject"        → "MYPROJECT"
    """
    if not project_id:
        return ""

    pid = project_id.upper()
    # Strip known prefixes like "PROJ-"
    for strip in _STRIP_PREFIXES:
        if pid.startswith(strip):
            pid = pid[len(strip):]
            break

    # Take first segment before hyphen, strip trailing numbers/dates
    parts = pid.split("-")
    prefix = parts[0]
    return prefix


def resolve_project_prefix(workspace_id: Optional[str], ws_store: dict) -> str:
    """Resolve project prefix from workspace_id via workspace store lookup.

    Args:
        workspace_id: Workspace ID (e.g., "WS-9147535A")
        ws_store: Dict of workspace_id → workspace data (must have project_id)

    Returns:
        Project prefix string, or "" if not resolvable.
    """
    if not workspace_id:
        return ""
    ws = ws_store.get(workspace_id, {})
    project_id = ws.get("project_id", "")
    return derive_project_prefix(project_id)


def generate_task_id(
    task_type: str,
    client=None,
    project_prefix: str = "",
) -> str:
    """Generate next sequential task ID based on type prefix.

    Queries TypeDB for max existing ID with prefix, increments by 1.
    Falls back to in-memory counter if TypeDB unavailable.

    Args:
        task_type: One of the TASK_TYPE_PREFIX keys (bug, feature, etc.)
        client: Optional TypeDB client for querying existing IDs.
        project_prefix: Optional project prefix (e.g., "SARVAJA").
            When provided, generates "{PROJECT}-{TYPE}-{NNN}".

    Returns:
        Generated task ID like "BUG-001" or "SARVAJA-BUG-001".
    """
    type_prefix = TASK_TYPE_PREFIX.get(task_type, "TASK")
    full_prefix = f"{project_prefix}-{type_prefix}" if project_prefix else type_prefix
    max_num = _counters.get(full_prefix, 0)

    # Try to find max existing ID from TypeDB
    if client:
        try:
            max_num = _find_max_id_from_typedb(client, full_prefix)
        except Exception as e:
            logger.debug(f"TypeDB ID scan for {full_prefix}: {type(e).__name__}")

    # Also check in-memory store for IDs that may not be in TypeDB yet
    try:
        from governance.stores import _tasks_store
        for tid in _tasks_store:
            num = _extract_sequence(tid, full_prefix)
            if num > max_num:
                max_num = num
    except Exception:
        pass

    next_num = max_num + 1
    _counters[full_prefix] = next_num
    return f"{full_prefix}-{next_num:03d}"


def _find_max_id_from_typedb(client, prefix: str) -> int:
    """Query TypeDB for the maximum sequence number with given prefix."""
    max_num = 0
    try:
        all_tasks = client.get_all_tasks()
        for task in all_tasks:
            task_id = task.id if hasattr(task, 'id') else str(task)
            num = _extract_sequence(task_id, prefix)
            if num > max_num:
                max_num = num
    except Exception as e:
        logger.debug(f"TypeDB task scan for prefix {prefix}: {type(e).__name__}")
    return max_num


def _extract_sequence(task_id: str, prefix: str) -> int:
    """Extract numeric sequence from a task ID like 'BUG-042' or 'SARVAJA-BUG-042'."""
    pattern = rf"^{re.escape(prefix)}-(\d+)$"
    match = re.match(pattern, task_id)
    if match:
        return int(match.group(1))
    return 0
