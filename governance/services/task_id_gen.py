"""Task ID Auto-Generation Service (META-TAXON-01-v1).

Generates sequential task IDs based on task type prefix.
Pattern: {PREFIX}-{NNN} where NNN is 3-digit zero-padded sequence.

Per DOC-SIZE-01-v1: Single responsibility module.
"""
import re
import logging
from typing import Optional

from agent.governance_ui.state.constants import TASK_TYPE_PREFIX

logger = logging.getLogger(__name__)

# In-memory counters as fallback when TypeDB is unavailable
_counters: dict = {}


def generate_task_id(task_type: str, client=None) -> str:
    """Generate next sequential task ID based on type prefix.

    Queries TypeDB for max existing ID with prefix, increments by 1.
    Falls back to in-memory counter if TypeDB unavailable.

    Args:
        task_type: One of the TASK_TYPE_PREFIX keys (bug, feature, etc.)
        client: Optional TypeDB client for querying existing IDs.

    Returns:
        Generated task ID like "BUG-001", "FEAT-042", etc.
    """
    prefix = TASK_TYPE_PREFIX.get(task_type, "TASK")
    max_num = _counters.get(prefix, 0)

    # Try to find max existing ID from TypeDB
    if client:
        try:
            max_num = _find_max_id_from_typedb(client, prefix)
        except Exception as e:
            # BUG-477-TIG-1: Sanitize debug/info logger
            logger.debug(f"TypeDB ID scan for {prefix}: {type(e).__name__}")

    # Also check in-memory store for IDs that may not be in TypeDB yet
    try:
        from governance.stores import _tasks_store
        for tid in _tasks_store:
            num = _extract_sequence(tid, prefix)
            if num > max_num:
                max_num = num
    except Exception:
        pass

    next_num = max_num + 1
    _counters[prefix] = next_num
    return f"{prefix}-{next_num:03d}"


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
        # BUG-477-TIG-2: Sanitize debug/info logger
        logger.debug(f"TypeDB task scan for prefix {prefix}: {type(e).__name__}")
    return max_num


def _extract_sequence(task_id: str, prefix: str) -> int:
    """Extract numeric sequence from a task ID like 'BUG-042'."""
    pattern = rf"^{re.escape(prefix)}-(\d+)$"
    match = re.match(pattern, task_id)
    if match:
        return int(match.group(1))
    return 0
