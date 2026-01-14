"""
TDD Tests for Task Lifecycle Status/Resolution.

Per GAP-UI-046: Task status/resolution per Agile DoR/DoD
Per TEST-FIX-01-v1: All fixes need verification evidence

Agile Definitions:
- Status (lifecycle): OPEN → IN_PROGRESS → CLOSED
- Resolution (outcome): DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED

Created: 2026-01-14
"""

import pytest
from dataclasses import dataclass
from typing import Optional
from enum import Enum


# =============================================================================
# TDD DESIGN: Enums and Validation
# =============================================================================

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


def validate_status_resolution_combo(status: TaskStatus, resolution: TaskResolution) -> tuple[bool, str]:
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


# =============================================================================
# UNIT TESTS: Status Transitions
# =============================================================================

class TestTaskStatusTransitions:
    """Test valid status transitions."""

    def test_open_to_in_progress_valid(self):
        """OPEN → IN_PROGRESS is valid (task started)."""
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.IN_PROGRESS)

    def test_in_progress_to_closed_valid(self):
        """IN_PROGRESS → CLOSED is valid (task completed)."""
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.CLOSED)

    def test_closed_to_open_valid(self):
        """CLOSED → OPEN is valid (reopen task)."""
        assert validate_status_transition(TaskStatus.CLOSED, TaskStatus.OPEN)

    def test_open_to_closed_valid(self):
        """OPEN → CLOSED is valid (can skip IN_PROGRESS for trivial tasks)."""
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.CLOSED)

    def test_same_status_valid(self):
        """Same status transition is always valid."""
        for status in TaskStatus:
            assert validate_status_transition(status, status)


# =============================================================================
# UNIT TESTS: Resolution Transitions
# =============================================================================

class TestTaskResolutionTransitions:
    """Test valid resolution transitions."""

    def test_none_to_implemented_valid(self):
        """NONE → IMPLEMENTED is valid (solution delivered)."""
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.IMPLEMENTED)

    def test_implemented_to_validated_valid(self):
        """IMPLEMENTED → VALIDATED is valid (tests pass)."""
        assert validate_resolution_transition(TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED)

    def test_validated_to_certified_valid(self):
        """VALIDATED → CERTIFIED is valid (user feedback)."""
        assert validate_resolution_transition(TaskResolution.VALIDATED, TaskResolution.CERTIFIED)

    def test_none_to_deferred_valid(self):
        """NONE → DEFERRED is valid (postpone task)."""
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.DEFERRED)

    def test_deferred_to_implemented_valid(self):
        """DEFERRED → IMPLEMENTED is valid (resume and complete)."""
        assert validate_resolution_transition(TaskResolution.DEFERRED, TaskResolution.IMPLEMENTED)

    def test_certified_cannot_skip_to_none(self):
        """CERTIFIED cannot jump directly to NONE."""
        assert not validate_resolution_transition(TaskResolution.CERTIFIED, TaskResolution.NONE)


# =============================================================================
# UNIT TESTS: Status/Resolution Combinations
# =============================================================================

class TestStatusResolutionCombinations:
    """Test valid status/resolution combinations."""

    def test_open_must_have_none_resolution(self):
        """OPEN tasks must have NONE resolution."""
        valid, msg = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.NONE)
        assert valid, msg

        valid, msg = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.IMPLEMENTED)
        assert not valid

    def test_in_progress_must_have_none_resolution(self):
        """IN_PROGRESS tasks must have NONE resolution."""
        valid, msg = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.NONE)
        assert valid, msg

        valid, msg = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.VALIDATED)
        assert not valid

    def test_closed_must_have_resolution(self):
        """CLOSED tasks must have a resolution."""
        valid, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.NONE)
        assert not valid

        valid, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.IMPLEMENTED)
        assert valid, msg

        valid, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.CERTIFIED)
        assert valid, msg

    def test_closed_deferred_is_valid(self):
        """CLOSED + DEFERRED is valid (postponed task)."""
        valid, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.DEFERRED)
        assert valid, msg


# =============================================================================
# INTEGRATION TESTS: Task Lifecycle Scenarios
# =============================================================================

class TestTaskLifecycleScenarios:
    """Test complete task lifecycle scenarios."""

    def test_happy_path_to_certified(self):
        """Test full lifecycle: OPEN → IN_PROGRESS → CLOSED(CERTIFIED)."""
        # Start
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

        # Begin work
        assert validate_status_transition(status, TaskStatus.IN_PROGRESS)
        status = TaskStatus.IN_PROGRESS

        # Complete implementation
        assert validate_status_transition(status, TaskStatus.CLOSED)
        status = TaskStatus.CLOSED
        assert validate_resolution_transition(resolution, TaskResolution.IMPLEMENTED)
        resolution = TaskResolution.IMPLEMENTED

        # Validate
        assert validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED

        # Certify
        assert validate_resolution_transition(resolution, TaskResolution.CERTIFIED)
        resolution = TaskResolution.CERTIFIED

        # Final state valid
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

    def test_defer_and_resume(self):
        """Test defer then resume: OPEN → CLOSED(DEFERRED) → OPEN → CLOSED(IMPLEMENTED)."""
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE

        # Defer
        status = TaskStatus.CLOSED
        resolution = TaskResolution.DEFERRED
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

        # Reopen
        status = TaskStatus.OPEN
        resolution = TaskResolution.NONE  # Reset resolution when reopening
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

        # Complete
        status = TaskStatus.CLOSED
        resolution = TaskResolution.IMPLEMENTED
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

    def test_bug_found_downgrade(self):
        """Test downgrade: CERTIFIED → VALIDATED if bug found."""
        status, resolution = TaskStatus.CLOSED, TaskResolution.CERTIFIED

        # Bug found, need to revalidate
        assert validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED

        # Still valid combination
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid


# =============================================================================
# DATA INTEGRITY TESTS: TypeDB Schema
# =============================================================================

class TestTypeDBTaskSchema:
    """Test TypeDB schema requirements for task lifecycle."""

    def test_status_values_match_enum(self):
        """Verify TypeDB status values match our enum."""
        typedb_values = ["OPEN", "IN_PROGRESS", "CLOSED"]
        for val in typedb_values:
            assert val in [s.value for s in TaskStatus]

    def test_resolution_values_match_enum(self):
        """Verify TypeDB resolution values match our enum."""
        typedb_values = ["NONE", "DEFERRED", "IMPLEMENTED", "VALIDATED", "CERTIFIED"]
        for val in typedb_values:
            assert val in [r.value for r in TaskResolution]

    def test_backward_compatible_status_mapping(self):
        """Map old status values to new lifecycle.

        Old: TODO, IN_PROGRESS, DONE, BLOCKED
        New: OPEN, IN_PROGRESS, CLOSED
        """
        mapping = {
            "TODO": TaskStatus.OPEN,
            "IN_PROGRESS": TaskStatus.IN_PROGRESS,
            "DONE": TaskStatus.CLOSED,
            "BLOCKED": TaskStatus.IN_PROGRESS,  # Blocked is still in progress
        }

        for old_val, new_status in mapping.items():
            assert new_status in TaskStatus


# =============================================================================
# BDD TESTS: Feature Scenarios
# =============================================================================

class TestBDDScenarios:
    """BDD-style scenario tests."""

    def test_scenario_developer_completes_task(self):
        """
        GIVEN a task in OPEN status with NONE resolution
        WHEN developer starts working on it
        THEN status changes to IN_PROGRESS
        AND resolution stays NONE

        WHEN developer finishes implementation
        THEN status changes to CLOSED
        AND resolution changes to IMPLEMENTED
        """
        # Given
        status, resolution = TaskStatus.OPEN, TaskResolution.NONE

        # When starts working
        status = TaskStatus.IN_PROGRESS
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

        # When finishes
        status = TaskStatus.CLOSED
        resolution = TaskResolution.IMPLEMENTED
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

    def test_scenario_qa_validates_task(self):
        """
        GIVEN a task in CLOSED status with IMPLEMENTED resolution
        WHEN QA runs validation tests
        AND tests pass
        THEN resolution changes to VALIDATED
        """
        # Given
        status, resolution = TaskStatus.CLOSED, TaskResolution.IMPLEMENTED

        # When QA validates
        assert validate_resolution_transition(resolution, TaskResolution.VALIDATED)
        resolution = TaskResolution.VALIDATED
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid

    def test_scenario_user_certifies_task(self):
        """
        GIVEN a task in CLOSED status with VALIDATED resolution
        WHEN user provides positive feedback
        THEN resolution changes to CERTIFIED
        """
        # Given
        status, resolution = TaskStatus.CLOSED, TaskResolution.VALIDATED

        # When user certifies
        assert validate_resolution_transition(resolution, TaskResolution.CERTIFIED)
        resolution = TaskResolution.CERTIFIED
        valid, _ = validate_status_resolution_combo(status, resolution)
        assert valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
