"""
Robot Framework Library for Task Lifecycle Status/Resolution Tests.

Per GAP-UI-046: Task status/resolution per Agile DoR/DoD.
Migrated from tests/test_task_lifecycle.py

Agile Definitions:
- Status (lifecycle): OPEN -> IN_PROGRESS -> CLOSED
- Resolution (outcome): DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
"""
from enum import Enum
from robot.api.deco import keyword


# =============================================================================
# Enums and Validation (from test file)
# =============================================================================

class TaskStatus(str, Enum):
    """Task lifecycle status (Definition of Ready)."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class TaskResolution(str, Enum):
    """Task resolution outcome (Definition of Done)."""
    NONE = "NONE"
    DEFERRED = "DEFERRED"
    IMPLEMENTED = "IMPLEMENTED"
    VALIDATED = "VALIDATED"
    CERTIFIED = "CERTIFIED"


VALID_STATUS_TRANSITIONS = {
    TaskStatus.OPEN: [TaskStatus.IN_PROGRESS, TaskStatus.CLOSED],
    TaskStatus.IN_PROGRESS: [TaskStatus.OPEN, TaskStatus.CLOSED],
    TaskStatus.CLOSED: [TaskStatus.OPEN, TaskStatus.IN_PROGRESS],
}

VALID_RESOLUTION_TRANSITIONS = {
    TaskResolution.NONE: [TaskResolution.DEFERRED, TaskResolution.IMPLEMENTED],
    TaskResolution.DEFERRED: [TaskResolution.NONE, TaskResolution.IMPLEMENTED],
    TaskResolution.IMPLEMENTED: [TaskResolution.VALIDATED, TaskResolution.DEFERRED],
    TaskResolution.VALIDATED: [TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED],
    TaskResolution.CERTIFIED: [TaskResolution.VALIDATED],
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


def validate_status_resolution_combo(status: TaskStatus, resolution: TaskResolution) -> tuple:
    """Validate status and resolution combination."""
    if status in [TaskStatus.OPEN, TaskStatus.IN_PROGRESS]:
        if resolution != TaskResolution.NONE:
            return False, f"Active tasks (status={status}) cannot have resolution {resolution}"
    elif status == TaskStatus.CLOSED:
        if resolution == TaskResolution.NONE:
            return False, "CLOSED tasks must have a resolution"
    return True, "OK"


class TaskLifecycleLibrary:
    """Library for testing task lifecycle status/resolution."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Status Transitions Tests
    # =============================================================================

    @keyword("Open To In Progress Valid")
    def open_to_in_progress_valid(self):
        """OPEN -> IN_PROGRESS is valid (task started)."""
        return {"valid": validate_status_transition(TaskStatus.OPEN, TaskStatus.IN_PROGRESS)}

    @keyword("In Progress To Closed Valid")
    def in_progress_to_closed_valid(self):
        """IN_PROGRESS -> CLOSED is valid (task completed)."""
        return {"valid": validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.CLOSED)}

    @keyword("Closed To Open Valid")
    def closed_to_open_valid(self):
        """CLOSED -> OPEN is valid (reopen task)."""
        return {"valid": validate_status_transition(TaskStatus.CLOSED, TaskStatus.OPEN)}

    @keyword("Open To Closed Valid")
    def open_to_closed_valid(self):
        """OPEN -> CLOSED is valid (skip IN_PROGRESS for trivial tasks)."""
        return {"valid": validate_status_transition(TaskStatus.OPEN, TaskStatus.CLOSED)}

    @keyword("Same Status Valid")
    def same_status_valid(self):
        """Same status transition is always valid."""
        results = {}
        for status in TaskStatus:
            results[f"{status.value}_same"] = validate_status_transition(status, status)
        return results

    # =============================================================================
    # Resolution Transitions Tests
    # =============================================================================

    @keyword("None To Implemented Valid")
    def none_to_implemented_valid(self):
        """NONE -> IMPLEMENTED is valid (solution delivered)."""
        return {"valid": validate_resolution_transition(TaskResolution.NONE, TaskResolution.IMPLEMENTED)}

    @keyword("Implemented To Validated Valid")
    def implemented_to_validated_valid(self):
        """IMPLEMENTED -> VALIDATED is valid (tests pass)."""
        return {"valid": validate_resolution_transition(TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED)}

    @keyword("Validated To Certified Valid")
    def validated_to_certified_valid(self):
        """VALIDATED -> CERTIFIED is valid (user feedback)."""
        return {"valid": validate_resolution_transition(TaskResolution.VALIDATED, TaskResolution.CERTIFIED)}

    @keyword("None To Deferred Valid")
    def none_to_deferred_valid(self):
        """NONE -> DEFERRED is valid (postpone task)."""
        return {"valid": validate_resolution_transition(TaskResolution.NONE, TaskResolution.DEFERRED)}

    @keyword("Deferred To Implemented Valid")
    def deferred_to_implemented_valid(self):
        """DEFERRED -> IMPLEMENTED is valid (resume and complete)."""
        return {"valid": validate_resolution_transition(TaskResolution.DEFERRED, TaskResolution.IMPLEMENTED)}

    @keyword("Certified Cannot Skip To None")
    def certified_cannot_skip_to_none(self):
        """CERTIFIED cannot jump directly to NONE."""
        return {"invalid": not validate_resolution_transition(TaskResolution.CERTIFIED, TaskResolution.NONE)}

    # =============================================================================
    # Status/Resolution Combinations Tests
    # =============================================================================

    @keyword("Open Must Have None Resolution")
    def open_must_have_none_resolution(self):
        """OPEN tasks must have NONE resolution."""
        valid_none, _ = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.NONE)
        valid_impl, _ = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.IMPLEMENTED)
        return {
            "none_valid": valid_none,
            "implemented_invalid": not valid_impl
        }

    @keyword("In Progress Must Have None Resolution")
    def in_progress_must_have_none_resolution(self):
        """IN_PROGRESS tasks must have NONE resolution."""
        valid_none, _ = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.NONE)
        valid_val, _ = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.VALIDATED)
        return {
            "none_valid": valid_none,
            "validated_invalid": not valid_val
        }

    @keyword("Closed Must Have Resolution")
    def closed_must_have_resolution(self):
        """CLOSED tasks must have a resolution."""
        valid_none, _ = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.NONE)
        valid_impl, _ = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.IMPLEMENTED)
        valid_cert, _ = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.CERTIFIED)
        return {
            "none_invalid": not valid_none,
            "implemented_valid": valid_impl,
            "certified_valid": valid_cert
        }

    @keyword("Closed Deferred Is Valid")
    def closed_deferred_is_valid(self):
        """CLOSED + DEFERRED is valid (postponed task)."""
        valid, _ = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.DEFERRED)
        return {"valid": valid}

    # =============================================================================
    # Task Lifecycle Scenarios Tests
    # =============================================================================

    @keyword("Happy Path To Certified")
    def happy_path_to_certified(self):
        """Test full lifecycle: OPEN -> IN_PROGRESS -> CLOSED(CERTIFIED)."""
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE

        # Start
        start_valid, _ = validate_status_resolution_combo(status, resolution)

        # Begin work
        trans1 = validate_status_transition(status, TaskStatus.IN_PROGRESS)
        status = TaskStatus.IN_PROGRESS

        # Complete implementation
        trans2 = validate_status_transition(status, TaskStatus.CLOSED)
        status = TaskStatus.CLOSED
        trans3 = validate_resolution_transition(resolution, TaskResolution.IMPLEMENTED)
        resolution = TaskResolution.IMPLEMENTED

        # Validate
        trans4 = validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED

        # Certify
        trans5 = validate_resolution_transition(resolution, TaskResolution.CERTIFIED)
        resolution = TaskResolution.CERTIFIED

        # Final state valid
        final_valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "start_valid": start_valid,
            "trans1": trans1,
            "trans2": trans2,
            "trans3": trans3,
            "trans4": trans4,
            "trans5": trans5,
            "final_valid": final_valid
        }

    @keyword("Defer And Resume")
    def defer_and_resume(self):
        """Test defer then resume: OPEN -> CLOSED(DEFERRED) -> OPEN -> CLOSED(IMPLEMENTED)."""
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE

        # Defer
        status = TaskStatus.CLOSED
        resolution = TaskResolution.DEFERRED
        defer_valid, _ = validate_status_resolution_combo(status, resolution)

        # Reopen
        status = TaskStatus.OPEN
        resolution = TaskResolution.NONE
        reopen_valid, _ = validate_status_resolution_combo(status, resolution)

        # Complete
        status = TaskStatus.CLOSED
        resolution = TaskResolution.IMPLEMENTED
        complete_valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "defer_valid": defer_valid,
            "reopen_valid": reopen_valid,
            "complete_valid": complete_valid
        }

    @keyword("Bug Found Downgrade")
    def bug_found_downgrade(self):
        """Test downgrade: CERTIFIED -> VALIDATED if bug found."""
        status, resolution = TaskStatus.CLOSED, TaskResolution.CERTIFIED

        # Bug found, need to revalidate
        trans = validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED

        # Still valid combination
        valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "downgrade_valid": trans,
            "final_valid": valid
        }

    # =============================================================================
    # TypeDB Schema Tests
    # =============================================================================

    @keyword("Status Values Match Enum")
    def status_values_match_enum(self):
        """Verify TypeDB status values match our enum."""
        typedb_values = ["OPEN", "IN_PROGRESS", "CLOSED"]
        all_match = all(val in [s.value for s in TaskStatus] for val in typedb_values)
        return {"all_match": all_match}

    @keyword("Resolution Values Match Enum")
    def resolution_values_match_enum(self):
        """Verify TypeDB resolution values match our enum."""
        typedb_values = ["NONE", "DEFERRED", "IMPLEMENTED", "VALIDATED", "CERTIFIED"]
        all_match = all(val in [r.value for r in TaskResolution] for val in typedb_values)
        return {"all_match": all_match}

    @keyword("Backward Compatible Status Mapping")
    def backward_compatible_status_mapping(self):
        """Map old status values to new lifecycle."""
        mapping = {
            "TODO": TaskStatus.OPEN,
            "IN_PROGRESS": TaskStatus.IN_PROGRESS,
            "DONE": TaskStatus.CLOSED,
            "BLOCKED": TaskStatus.IN_PROGRESS,
        }
        all_valid = all(new_status in TaskStatus for new_status in mapping.values())
        return {"all_valid": all_valid}

    # =============================================================================
    # BDD Scenario Tests
    # =============================================================================

    @keyword("Scenario Developer Completes Task")
    def scenario_developer_completes_task(self):
        """
        GIVEN a task in OPEN status with NONE resolution
        WHEN developer starts and finishes
        THEN valid transitions occur
        """
        # Given
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE

        # When starts working
        status = TaskStatus.IN_PROGRESS
        working_valid, _ = validate_status_resolution_combo(status, resolution)

        # When finishes
        status = TaskStatus.CLOSED
        resolution = TaskResolution.IMPLEMENTED
        complete_valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "working_valid": working_valid,
            "complete_valid": complete_valid
        }

    @keyword("Scenario QA Validates Task")
    def scenario_qa_validates_task(self):
        """
        GIVEN a task in CLOSED status with IMPLEMENTED resolution
        WHEN QA validates
        THEN resolution changes to VALIDATED
        """
        # Given
        status, resolution = TaskStatus.CLOSED, TaskResolution.IMPLEMENTED

        # When QA validates
        trans = validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED
        valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "transition_valid": trans,
            "combo_valid": valid
        }

    @keyword("Scenario User Certifies Task")
    def scenario_user_certifies_task(self):
        """
        GIVEN a task in CLOSED status with VALIDATED resolution
        WHEN user certifies
        THEN resolution changes to CERTIFIED
        """
        # Given
        status, resolution = TaskStatus.CLOSED, TaskResolution.VALIDATED

        # When user certifies
        trans = validate_resolution_transition(resolution, TaskResolution.CERTIFIED)
        resolution = TaskResolution.CERTIFIED
        valid, _ = validate_status_resolution_combo(status, resolution)

        return {
            "transition_valid": trans,
            "combo_valid": valid
        }
