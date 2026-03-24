"""
Task Lifecycle Management.

Per GAP-UI-046: Task status/resolution per Agile DoR/DoD
Per TEST-FIX-01-v1: All fixes need verification evidence
Per EPIC-TASK-QUALITY-V3 P14: Canonical TaskStatus enum — single source of truth

Agile Definitions:
- Status (lifecycle): OPEN/TODO → IN_PROGRESS → DONE/CLOSED | BLOCKED | CANCELED
- Resolution (outcome): NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED

Created: 2026-01-14
Updated: 2026-03-24 — P14: Added TODO, DONE, BLOCKED, CANCELED states
"""

from enum import Enum
from typing import List, Set, Tuple


class TaskStatus(str, Enum):
    """Task lifecycle status — canonical enum, single source of truth.

    Per EPIC-TASK-QUALITY-V3 P14: All layers (TypeDB, MCP, UI) import from here.
    """
    OPEN = "OPEN"           # Ready to be worked on
    TODO = "TODO"           # Backlog / not yet started
    IN_PROGRESS = "IN_PROGRESS"  # Being worked on
    BLOCKED = "BLOCKED"     # Waiting on external dependency
    DONE = "DONE"           # Work complete (legacy synonym for CLOSED)
    CANCELED = "CANCELED"   # Abandoned / no longer needed
    CLOSED = "CLOSED"       # Work complete (Agile canonical)

    @classmethod
    def valid_values(cls) -> Set[str]:
        """All valid status strings for TypeDB validation."""
        return {s.value for s in cls}

    @classmethod
    def ui_edit_values(cls) -> List[str]:
        """Status values for the UI edit dropdown (excludes CLOSED — use DONE)."""
        return ["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "CANCELED"]

    @classmethod
    def terminal_states(cls) -> Set["TaskStatus"]:
        """States where the task is finished — Delete is allowed here."""
        return {cls.DONE, cls.CLOSED, cls.CANCELED}

    @property
    def is_terminal(self) -> bool:
        """Whether this status represents a finished/abandoned task."""
        return self in self.terminal_states()


class TaskResolution(str, Enum):
    """Task resolution outcome (Definition of Done)."""
    NONE = "NONE"  # No resolution yet (task not closed)
    DEFERRED = "DEFERRED"  # Postponed for later
    IMPLEMENTED = "IMPLEMENTED"  # Code/solution delivered
    VALIDATED = "VALIDATED"  # Tests pass, solution verified
    CERTIFIED = "CERTIFIED"  # User feedback enrolled


# Valid transitions — P14: includes TODO, DONE, BLOCKED, CANCELED
VALID_STATUS_TRANSITIONS = {
    TaskStatus.OPEN: [TaskStatus.IN_PROGRESS, TaskStatus.CLOSED, TaskStatus.CANCELED],
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELED],
    TaskStatus.IN_PROGRESS: [TaskStatus.OPEN, TaskStatus.DONE, TaskStatus.CLOSED,
                             TaskStatus.BLOCKED, TaskStatus.CANCELED],
    TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.OPEN, TaskStatus.CANCELED],
    TaskStatus.DONE: [TaskStatus.OPEN, TaskStatus.IN_PROGRESS],  # Reopen
    TaskStatus.CANCELED: [TaskStatus.OPEN, TaskStatus.TODO],  # Re-activate
    TaskStatus.CLOSED: [TaskStatus.OPEN, TaskStatus.IN_PROGRESS],  # Reopen
}

VALID_RESOLUTION_TRANSITIONS = {
    TaskResolution.NONE: [TaskResolution.DEFERRED, TaskResolution.IMPLEMENTED],
    TaskResolution.DEFERRED: [TaskResolution.NONE, TaskResolution.IMPLEMENTED],
    TaskResolution.IMPLEMENTED: [TaskResolution.VALIDATED, TaskResolution.DEFERRED],
    TaskResolution.VALIDATED: [TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED],
    TaskResolution.CERTIFIED: [TaskResolution.VALIDATED],  # Can downgrade if issue found
}

# Backward compatibility mapping — P14: all values now canonical enum members
STATUS_MIGRATION_MAP = {
    "TODO": TaskStatus.TODO,
    "IN_PROGRESS": TaskStatus.IN_PROGRESS,
    "DONE": TaskStatus.DONE,
    "BLOCKED": TaskStatus.BLOCKED,
    "CANCELED": TaskStatus.CANCELED,
    "OPEN": TaskStatus.OPEN,
    "CLOSED": TaskStatus.CLOSED,
}


def validate_status_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """Validate if a status transition is allowed."""
    if from_status == to_status:
        return True
    return to_status in VALID_STATUS_TRANSITIONS.get(from_status, [])


def validate_resolution_transition(from_res: TaskResolution, to_res: TaskResolution) -> bool:
    """Validate if a resolution transition is allowed."""
    if from_res == to_res:
        return True
    return to_res in VALID_RESOLUTION_TRANSITIONS.get(from_res, [])


def validate_status_resolution_combo(status: TaskStatus, resolution: TaskResolution) -> Tuple[bool, str]:
    """Validate status and resolution combination.

    Rules:
    1. OPEN/IN_PROGRESS tasks must have resolution NONE
    2. CLOSED tasks must have a resolution (not NONE)
    3. CERTIFIED requires prior VALIDATED state
    """
    active_states = [TaskStatus.OPEN, TaskStatus.TODO, TaskStatus.IN_PROGRESS,
                     TaskStatus.BLOCKED, TaskStatus.CANCELED]
    if status in active_states:
        if resolution != TaskResolution.NONE:
            return False, f"Active tasks (status={status}) cannot have resolution {resolution}"
    elif status in [TaskStatus.CLOSED, TaskStatus.DONE]:
        if resolution == TaskResolution.NONE:
            return False, f"{status} tasks must have a resolution"
    return True, "OK"


def migrate_legacy_status(old_status: str) -> str:
    """Migrate legacy status value to new lifecycle status.

    Args:
        old_status: Legacy status (TODO, IN_PROGRESS, DONE, BLOCKED)

    Returns:
        New lifecycle status (OPEN, IN_PROGRESS, CLOSED)
    """
    if old_status in STATUS_MIGRATION_MAP:
        return STATUS_MIGRATION_MAP[old_status].value
    # If already new format, return as-is
    try:
        return TaskStatus(old_status).value
    except ValueError:
        # Unknown status, default to OPEN
        return TaskStatus.OPEN.value


def get_resolution_for_close(
    current_resolution: TaskResolution = TaskResolution.NONE,
    has_evidence: bool = False,
    has_tests: bool = False,
    has_user_feedback: bool = False
) -> TaskResolution:
    """Determine appropriate resolution when closing a task.

    Args:
        current_resolution: Current resolution state
        has_evidence: Task has completion evidence
        has_tests: Task has passing tests
        has_user_feedback: Task has user acceptance

    Returns:
        Recommended resolution
    """
    if has_user_feedback and has_tests:
        return TaskResolution.CERTIFIED
    elif has_tests:
        return TaskResolution.VALIDATED
    elif has_evidence:
        return TaskResolution.IMPLEMENTED
    elif current_resolution == TaskResolution.DEFERRED:
        return TaskResolution.DEFERRED
    else:
        return TaskResolution.IMPLEMENTED


def reopen_task_resolution() -> TaskResolution:
    """Get resolution when reopening a task.

    When a task is reopened, resolution resets to NONE.
    """
    return TaskResolution.NONE


__all__ = [
    'TaskStatus',
    'TaskResolution',
    'VALID_STATUS_TRANSITIONS',
    'VALID_RESOLUTION_TRANSITIONS',
    'STATUS_MIGRATION_MAP',
    'validate_status_transition',
    'validate_resolution_transition',
    'validate_status_resolution_combo',
    'migrate_legacy_status',
    'get_resolution_for_close',
    'reopen_task_resolution',
]
