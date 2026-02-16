"""Orchestrator state creation and manipulation.

Per WORKFLOW-ORCH-01-v1: State tracks backlog, current phase,
cycle history, and validation results for the continuous loop.
"""

from datetime import datetime
from typing import Any, Dict, List

PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
MAX_RETRIES = 3


def create_initial_state(
    max_cycles: int = 10, dry_run: bool = False,
) -> Dict[str, Any]:
    """Create initial orchestrator state with empty backlog."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return {
        "cycle_id": f"ORCH-{ts}",
        "current_phase": "idle",
        "status": "pending",
        "backlog": [],
        "current_task": None,
        "specification": None,
        "implementation": None,
        "validation_results": None,
        "validation_passed": None,
        "gaps_discovered": [],
        "cycles_completed": 0,
        "max_cycles": max_cycles,
        "cycle_history": [],
        "retry_count": 0,
        "gate_decision": None,
        "dry_run": dry_run,
        # BUG-STATE-001: Initialize budget tracking fields
        "value_delivered": 0,
        "tokens_used": 0,
    }


def add_to_backlog(
    state: Dict[str, Any],
    task_id: str,
    priority: str,
    description: str,
) -> Dict[str, Any]:
    """Add a task to the backlog, sorted by priority. Rejects duplicates."""
    existing_ids = {t["task_id"] for t in state["backlog"]}
    if task_id in existing_ids:
        return state

    entry = {
        "task_id": task_id,
        "priority": priority,
        "description": description,
    }
    backlog = state["backlog"] + [entry]
    backlog.sort(key=lambda t: PRIORITY_ORDER.get(t["priority"], 99))
    state["backlog"] = backlog
    return state
