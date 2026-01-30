"""
Tests for task lifecycle management.

Per GAP-UI-046: Task status/resolution per Agile DoR/DoD.
Covers status transitions, resolution transitions, combo validation, and migration.

Created: 2026-01-30
"""

import pytest

from governance.task_lifecycle import (
    TaskStatus,
    TaskResolution,
    validate_status_transition,
    validate_resolution_transition,
    validate_status_resolution_combo,
    migrate_legacy_status,
    get_resolution_for_close,
    reopen_task_resolution,
    STATUS_MIGRATION_MAP,
)


class TestTaskStatusEnum:
    """Test TaskStatus enum values."""

    def test_values(self):
        assert TaskStatus.OPEN.value == "OPEN"
        assert TaskStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert TaskStatus.CLOSED.value == "CLOSED"

    def test_str_enum(self):
        """TaskStatus inherits from str."""
        assert TaskStatus.OPEN == "OPEN"


class TestTaskResolutionEnum:
    """Test TaskResolution enum values."""

    def test_values(self):
        assert TaskResolution.NONE.value == "NONE"
        assert TaskResolution.DEFERRED.value == "DEFERRED"
        assert TaskResolution.IMPLEMENTED.value == "IMPLEMENTED"
        assert TaskResolution.VALIDATED.value == "VALIDATED"
        assert TaskResolution.CERTIFIED.value == "CERTIFIED"


class TestValidateStatusTransition:
    """Test status transition validation."""

    def test_same_status_allowed(self):
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.OPEN) is True

    def test_open_to_in_progress(self):
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.IN_PROGRESS) is True

    def test_open_to_closed(self):
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.CLOSED) is True

    def test_in_progress_to_closed(self):
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.CLOSED) is True

    def test_in_progress_to_open(self):
        """Can reopen from in_progress."""
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.OPEN) is True

    def test_closed_to_open(self):
        """Can reopen closed tasks."""
        assert validate_status_transition(TaskStatus.CLOSED, TaskStatus.OPEN) is True

    def test_closed_to_in_progress(self):
        """Can resume closed tasks."""
        assert validate_status_transition(TaskStatus.CLOSED, TaskStatus.IN_PROGRESS) is True


class TestValidateResolutionTransition:
    """Test resolution transition validation."""

    def test_same_resolution_allowed(self):
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.NONE) is True

    def test_none_to_implemented(self):
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.IMPLEMENTED) is True

    def test_none_to_deferred(self):
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.DEFERRED) is True

    def test_implemented_to_validated(self):
        assert validate_resolution_transition(TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED) is True

    def test_validated_to_certified(self):
        assert validate_resolution_transition(TaskResolution.VALIDATED, TaskResolution.CERTIFIED) is True

    def test_none_to_certified_invalid(self):
        """Cannot skip from NONE directly to CERTIFIED."""
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.CERTIFIED) is False

    def test_none_to_validated_invalid(self):
        """Cannot skip from NONE directly to VALIDATED."""
        assert validate_resolution_transition(TaskResolution.NONE, TaskResolution.VALIDATED) is False

    def test_certified_can_downgrade(self):
        assert validate_resolution_transition(TaskResolution.CERTIFIED, TaskResolution.VALIDATED) is True


class TestValidateStatusResolutionCombo:
    """Test status+resolution combination validation."""

    def test_open_none_valid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.NONE)
        assert ok is True

    def test_in_progress_none_valid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.NONE)
        assert ok is True

    def test_open_with_resolution_invalid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.OPEN, TaskResolution.IMPLEMENTED)
        assert ok is False

    def test_in_progress_with_resolution_invalid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.IN_PROGRESS, TaskResolution.VALIDATED)
        assert ok is False

    def test_closed_none_invalid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.NONE)
        assert ok is False
        assert "must have a resolution" in msg

    def test_closed_implemented_valid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.IMPLEMENTED)
        assert ok is True

    def test_closed_certified_valid(self):
        ok, msg = validate_status_resolution_combo(TaskStatus.CLOSED, TaskResolution.CERTIFIED)
        assert ok is True


class TestMigrateLegacyStatus:
    """Test legacy status migration."""

    def test_todo_to_open(self):
        assert migrate_legacy_status("TODO") == "OPEN"

    def test_done_to_closed(self):
        assert migrate_legacy_status("DONE") == "CLOSED"

    def test_blocked_to_in_progress(self):
        assert migrate_legacy_status("BLOCKED") == "IN_PROGRESS"

    def test_in_progress_unchanged(self):
        assert migrate_legacy_status("IN_PROGRESS") == "IN_PROGRESS"

    def test_already_new_format(self):
        assert migrate_legacy_status("OPEN") == "OPEN"
        assert migrate_legacy_status("CLOSED") == "CLOSED"

    def test_unknown_defaults_to_open(self):
        assert migrate_legacy_status("INVALID") == "OPEN"


class TestGetResolutionForClose:
    """Test resolution recommendation for closing tasks."""

    def test_with_user_feedback_and_tests(self):
        r = get_resolution_for_close(has_evidence=True, has_tests=True, has_user_feedback=True)
        assert r == TaskResolution.CERTIFIED

    def test_with_tests_only(self):
        r = get_resolution_for_close(has_tests=True)
        assert r == TaskResolution.VALIDATED

    def test_with_evidence_only(self):
        r = get_resolution_for_close(has_evidence=True)
        assert r == TaskResolution.IMPLEMENTED

    def test_no_evidence(self):
        r = get_resolution_for_close()
        assert r == TaskResolution.IMPLEMENTED

    def test_deferred_preserved(self):
        r = get_resolution_for_close(current_resolution=TaskResolution.DEFERRED)
        assert r == TaskResolution.DEFERRED

    def test_feedback_without_tests_gives_validated(self):
        """User feedback without tests still gives VALIDATED via has_tests check."""
        r = get_resolution_for_close(has_user_feedback=True, has_tests=False)
        assert r == TaskResolution.IMPLEMENTED


class TestReopenTaskResolution:
    """Test reopening resets resolution."""

    def test_returns_none(self):
        assert reopen_task_resolution() == TaskResolution.NONE
