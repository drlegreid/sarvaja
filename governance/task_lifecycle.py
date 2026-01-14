"""
Task Lifecycle Management.

Per GAP-UI-046: Task status/resolution per Agile DoR/DoD
Per TEST-FIX-01-v1: All fixes need verification evidence

Agile Definitions:
- Status (lifecycle): OPEN → IN_PROGRESS → CLOSED
- Resolution (outcome): NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED

Created: 2026-01-14
"""

from enum import Enum
from typing import Tuple


class TaskStatus(str, Enum):
    """Task lifecycle status (Definition of Ready)."""
    OPEN = "OPEN"  # Ready to be worked on
    IN_PROGRESS = "IN_PROGRESS"  # Being worked on
    CLOSED = "CLOSED"  # Work complete


class TaskResolution(str, Enum):
    """Task resolution outcome (Definition of Done)."""
    NONE = "NONE"  # No resolution yet (task not closed)
    DEFERRED = "DEFERRED"  # Postponed for later
    IMPLEMENTED = "IMPLEMENTED"  # Code/solution delivered
    VALIDATED = "VALIDATED"  # Tests pass, solution verified
    CERTIFIED = "CERTIFIED"  # User feedback enrolled


# Valid transitions
VALID_STATUS_TRANSITIONS = {
    TaskStatus.OPEN: [TaskStatus.IN_PROGRESS, TaskStatus.CLOSED],
    TaskStatus.IN_PROGRESS: [TaskStatus.OPEN, TaskStatus.CLOSED],  # Can reopen
    TaskStatus.CLOSED: [TaskStatus.OPEN, TaskStatus.IN_PROGRESS],  # Can reopen
}

VALID_RESOLUTION_TRANSITIONS = {
    TaskResolution.NONE: [TaskResolution.DEFERRED, TaskResolution.IMPLEMENTED],
    TaskResolution.DEFERRED: [TaskResolution.NONE, TaskResolution.IMPLEMENTED],
    TaskResolution.IMPLEMENTED: [TaskResolution.VALIDATED, TaskResolution.DEFERRED],
    TaskResolution.VALIDATED: [TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED],
    TaskResolution.CERTIFIED: [TaskResolution.VALIDATED],  # Can downgrade if issue found
}

# Backward compatibility mapping from old to new status values
STATUS_MIGRATION_MAP = {
    "TODO": TaskStatus.OPEN,
    "IN_PROGRESS": TaskStatus.IN_PROGRESS,
    "DONE": TaskStatus.CLOSED,
    "BLOCKED": TaskStatus.IN_PROGRESS,  # Blocked tasks are still in progress
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
    if status in [TaskStatus.OPEN, TaskStatus.IN_PROGRESS]:
        if resolution != TaskResolution.NONE:
            return False, f"Active tasks (status={status}) cannot have resolution {resolution}"
    elif status == TaskStatus.CLOSED:
        if resolution == TaskResolution.NONE:
            return False, "CLOSED tasks must have a resolution"
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
