"""DSP-05: Task Lifecycle Gap Tests.

Covers missing test paths identified during DSP audit:
1. Invalid status transitions (TODO→DONE, TODO→BLOCKED, BLOCKED→DONE)
2. CANCELED state transitions (in/out)
3. Terminal states property (is_terminal, terminal_states())
4. TaskStatus helper methods (valid_values, ui_edit_values)
5. Resolution transition invalid paths
6. Status/resolution combo edge cases (BLOCKED, TODO, CANCELED)
7. get_resolution_for_close edge cases
8. migrate_legacy_status with new statuses (CANCELED, BLOCKED)
"""
import pytest

from governance.task_lifecycle import (
    TaskStatus,
    TaskResolution,
    VALID_STATUS_TRANSITIONS,
    VALID_RESOLUTION_TRANSITIONS,
    validate_status_transition,
    validate_resolution_transition,
    validate_status_resolution_combo,
    migrate_legacy_status,
    get_resolution_for_close,
    reopen_task_resolution,
)


# =============================================================================
# 1. Invalid Status Transitions
# =============================================================================


class TestInvalidStatusTransitions:
    """Transitions NOT in VALID_STATUS_TRANSITIONS must be rejected."""

    def test_todo_to_done_invalid(self):
        """TODO→DONE not allowed — must go through IN_PROGRESS first."""
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.DONE) is False

    def test_todo_to_blocked_invalid(self):
        """TODO→BLOCKED not allowed — must start work first."""
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.BLOCKED) is False

    def test_todo_to_open_invalid(self):
        """TODO→OPEN not allowed (no path)."""
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.OPEN) is False

    def test_blocked_to_done_invalid(self):
        """BLOCKED→DONE not allowed — must unblock first."""
        assert validate_status_transition(TaskStatus.BLOCKED, TaskStatus.DONE) is False

    def test_blocked_to_todo_invalid(self):
        """BLOCKED→TODO not allowed."""
        assert validate_status_transition(TaskStatus.BLOCKED, TaskStatus.TODO) is False

    def test_open_to_todo_invalid(self):
        """OPEN→TODO not allowed."""
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.TODO) is False

    def test_open_to_blocked_invalid(self):
        """OPEN→BLOCKED not allowed — must start work first."""
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.BLOCKED) is False

    def test_done_to_todo_invalid(self):
        """DONE→TODO not allowed (can only go to OPEN or IN_PROGRESS)."""
        assert validate_status_transition(TaskStatus.DONE, TaskStatus.TODO) is False

    def test_done_to_blocked_invalid(self):
        """DONE→BLOCKED not allowed."""
        assert validate_status_transition(TaskStatus.DONE, TaskStatus.BLOCKED) is False

    def test_done_to_canceled_invalid(self):
        """DONE→CANCELED not allowed."""
        assert validate_status_transition(TaskStatus.DONE, TaskStatus.CANCELED) is False

    def test_canceled_to_in_progress_invalid(self):
        """CANCELED→IN_PROGRESS not allowed (must re-activate to OPEN/TODO first)."""
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.IN_PROGRESS) is False

    def test_canceled_to_done_invalid(self):
        """CANCELED→DONE not allowed."""
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.DONE) is False

    def test_canceled_to_blocked_invalid(self):
        """CANCELED→BLOCKED not allowed."""
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.BLOCKED) is False


# =============================================================================
# 2. CANCELED State — Valid Transitions
# =============================================================================


class TestCanceledTransitions:
    """CANCELED transitions in and out."""

    def test_open_to_canceled(self):
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.CANCELED) is True

    def test_todo_to_canceled(self):
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.CANCELED) is True

    def test_in_progress_to_canceled(self):
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.CANCELED) is True

    def test_blocked_to_canceled(self):
        assert validate_status_transition(TaskStatus.BLOCKED, TaskStatus.CANCELED) is True

    def test_canceled_to_open(self):
        """Re-activate canceled task."""
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.OPEN) is True

    def test_canceled_to_todo(self):
        """Re-activate canceled task to backlog."""
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.TODO) is True

    def test_canceled_same_allowed(self):
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.CANCELED) is True


# =============================================================================
# 3. Terminal States
# =============================================================================


class TestTerminalStates:
    """TaskStatus.terminal_states() and is_terminal property."""

    def test_terminal_states_contains_done(self):
        assert TaskStatus.DONE in TaskStatus.terminal_states()

    def test_terminal_states_contains_canceled(self):
        assert TaskStatus.CANCELED in TaskStatus.terminal_states()

    def test_terminal_states_exactly_two(self):
        assert len(TaskStatus.terminal_states()) == 2

    def test_done_is_terminal(self):
        assert TaskStatus.DONE.is_terminal is True

    def test_canceled_is_terminal(self):
        assert TaskStatus.CANCELED.is_terminal is True

    def test_open_not_terminal(self):
        assert TaskStatus.OPEN.is_terminal is False

    def test_todo_not_terminal(self):
        assert TaskStatus.TODO.is_terminal is False

    def test_in_progress_not_terminal(self):
        assert TaskStatus.IN_PROGRESS.is_terminal is False

    def test_blocked_not_terminal(self):
        assert TaskStatus.BLOCKED.is_terminal is False


# =============================================================================
# 4. TaskStatus Helper Methods
# =============================================================================


class TestTaskStatusHelpers:
    """valid_values(), ui_edit_values(), canonical_values()."""

    def test_valid_values_is_set_of_strings(self):
        vals = TaskStatus.valid_values()
        assert isinstance(vals, set)
        assert all(isinstance(v, str) for v in vals)

    def test_valid_values_contains_all_six(self):
        expected = {"OPEN", "TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED"}
        assert TaskStatus.valid_values() == expected

    def test_valid_values_excludes_closed(self):
        assert "CLOSED" not in TaskStatus.valid_values()

    def test_ui_edit_values_is_list(self):
        vals = TaskStatus.ui_edit_values()
        assert isinstance(vals, list)

    def test_ui_edit_values_excludes_open(self):
        """OPEN is the initial state, not selectable in edit."""
        assert "OPEN" not in TaskStatus.ui_edit_values()

    def test_ui_edit_values_contains_done(self):
        assert "DONE" in TaskStatus.ui_edit_values()

    def test_ui_edit_values_contains_canceled(self):
        assert "CANCELED" in TaskStatus.ui_edit_values()

    def test_canonical_values_equals_valid_values(self):
        assert TaskStatus.canonical_values() == TaskStatus.valid_values()


# =============================================================================
# 5. Resolution Transition Invalid Paths
# =============================================================================


class TestInvalidResolutionTransitions:
    """Resolution transitions NOT in VALID_RESOLUTION_TRANSITIONS."""

    def test_none_to_validated_invalid(self):
        """Can't skip to VALIDATED without going through IMPLEMENTED."""
        assert validate_resolution_transition(
            TaskResolution.NONE, TaskResolution.VALIDATED
        ) is False

    def test_none_to_certified_invalid(self):
        """Can't skip to CERTIFIED from NONE."""
        assert validate_resolution_transition(
            TaskResolution.NONE, TaskResolution.CERTIFIED
        ) is False

    def test_deferred_to_validated_invalid(self):
        """DEFERRED→VALIDATED not allowed — must implement first."""
        assert validate_resolution_transition(
            TaskResolution.DEFERRED, TaskResolution.VALIDATED
        ) is False

    def test_deferred_to_certified_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.DEFERRED, TaskResolution.CERTIFIED
        ) is False

    def test_implemented_to_certified_invalid(self):
        """Must validate before certifying."""
        assert validate_resolution_transition(
            TaskResolution.IMPLEMENTED, TaskResolution.CERTIFIED
        ) is False

    def test_implemented_to_none_invalid(self):
        """Can't go backward from IMPLEMENTED to NONE."""
        assert validate_resolution_transition(
            TaskResolution.IMPLEMENTED, TaskResolution.NONE
        ) is False

    def test_validated_to_none_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.VALIDATED, TaskResolution.NONE
        ) is False

    def test_validated_to_deferred_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.VALIDATED, TaskResolution.DEFERRED
        ) is False

    def test_certified_to_none_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.CERTIFIED, TaskResolution.NONE
        ) is False

    def test_certified_to_deferred_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.CERTIFIED, TaskResolution.DEFERRED
        ) is False

    def test_certified_to_implemented_invalid(self):
        assert validate_resolution_transition(
            TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED
        ) is False


# =============================================================================
# 6. Status/Resolution Combo Edge Cases
# =============================================================================


class TestStatusResolutionComboEdgeCases:
    """Combo validation for states not covered in original tests."""

    def test_todo_none_valid(self):
        ok, _ = validate_status_resolution_combo(TaskStatus.TODO, TaskResolution.NONE)
        assert ok is True

    def test_todo_with_resolution_invalid(self):
        ok, msg = validate_status_resolution_combo(
            TaskStatus.TODO, TaskResolution.IMPLEMENTED
        )
        assert ok is False
        assert "Active" in msg or "cannot" in msg.lower()

    def test_blocked_none_valid(self):
        ok, _ = validate_status_resolution_combo(
            TaskStatus.BLOCKED, TaskResolution.NONE
        )
        assert ok is True

    def test_blocked_with_resolution_invalid(self):
        ok, msg = validate_status_resolution_combo(
            TaskStatus.BLOCKED, TaskResolution.DEFERRED
        )
        assert ok is False

    def test_canceled_none_valid(self):
        ok, _ = validate_status_resolution_combo(
            TaskStatus.CANCELED, TaskResolution.NONE
        )
        assert ok is True

    def test_canceled_with_resolution_invalid(self):
        ok, msg = validate_status_resolution_combo(
            TaskStatus.CANCELED, TaskResolution.IMPLEMENTED
        )
        assert ok is False

    def test_done_deferred_valid(self):
        ok, _ = validate_status_resolution_combo(
            TaskStatus.DONE, TaskResolution.DEFERRED
        )
        assert ok is True

    def test_done_validated_valid(self):
        ok, _ = validate_status_resolution_combo(
            TaskStatus.DONE, TaskResolution.VALIDATED
        )
        assert ok is True

    def test_done_certified_valid(self):
        ok, _ = validate_status_resolution_combo(
            TaskStatus.DONE, TaskResolution.CERTIFIED
        )
        assert ok is True


# =============================================================================
# 7. get_resolution_for_close Edge Cases
# =============================================================================


class TestGetResolutionForCloseEdgeCases:
    """Edge cases for resolution recommendation on close."""

    def test_all_flags_true_gives_certified(self):
        r = get_resolution_for_close(
            has_evidence=True, has_tests=True, has_user_feedback=True,
        )
        assert r == TaskResolution.CERTIFIED

    def test_tests_without_evidence_gives_validated(self):
        r = get_resolution_for_close(has_tests=True, has_evidence=False)
        assert r == TaskResolution.VALIDATED

    def test_feedback_with_tests_gives_certified(self):
        r = get_resolution_for_close(has_user_feedback=True, has_tests=True)
        assert r == TaskResolution.CERTIFIED

    def test_feedback_alone_gives_implemented(self):
        """User feedback without tests is not enough for VALIDATED."""
        r = get_resolution_for_close(has_user_feedback=True)
        assert r == TaskResolution.IMPLEMENTED

    def test_deferred_preserved_over_evidence(self):
        """DEFERRED current_resolution is preserved when no evidence/tests."""
        r = get_resolution_for_close(
            current_resolution=TaskResolution.DEFERRED,
            has_evidence=False, has_tests=False,
        )
        assert r == TaskResolution.DEFERRED

    def test_deferred_overridden_by_tests(self):
        """Tests override deferred resolution."""
        r = get_resolution_for_close(
            current_resolution=TaskResolution.DEFERRED,
            has_tests=True,
        )
        assert r == TaskResolution.VALIDATED


# =============================================================================
# 8. migrate_legacy_status New Statuses
# =============================================================================


class TestMigrateLegacyStatusExtended:
    """Verify CANCELED, BLOCKED, and edge cases in migration."""

    def test_canceled_maps_to_canceled(self):
        assert migrate_legacy_status("CANCELED") == "CANCELED"

    def test_blocked_maps_to_blocked(self):
        assert migrate_legacy_status("BLOCKED") == "BLOCKED"

    def test_open_maps_to_open(self):
        assert migrate_legacy_status("OPEN") == "OPEN"

    def test_closed_maps_to_done(self):
        assert migrate_legacy_status("CLOSED") == "DONE"

    def test_empty_string_defaults_to_open(self):
        """Empty string is unknown, defaults to OPEN."""
        assert migrate_legacy_status("") == "OPEN"

    def test_random_string_defaults_to_open(self):
        assert migrate_legacy_status("BANANA") == "OPEN"

    def test_lowercase_invalid_defaults_to_open(self):
        assert migrate_legacy_status("done") == "OPEN"


# =============================================================================
# 9. VALID_STATUS_TRANSITIONS Completeness
# =============================================================================


class TestTransitionMapCompleteness:
    """Every TaskStatus must have an entry in VALID_STATUS_TRANSITIONS."""

    def test_all_statuses_have_transition_entry(self):
        for status in TaskStatus:
            assert status in VALID_STATUS_TRANSITIONS, (
                f"Missing transition entry for {status}"
            )

    def test_all_transition_targets_are_valid_statuses(self):
        for from_status, targets in VALID_STATUS_TRANSITIONS.items():
            for target in targets:
                assert isinstance(target, TaskStatus), (
                    f"Invalid target {target} in transitions for {from_status}"
                )


class TestResolutionTransitionMapCompleteness:
    """Every TaskResolution must have an entry in VALID_RESOLUTION_TRANSITIONS."""

    def test_all_resolutions_have_transition_entry(self):
        for resolution in TaskResolution:
            assert resolution in VALID_RESOLUTION_TRANSITIONS, (
                f"Missing transition entry for {resolution}"
            )

    def test_all_transition_targets_are_valid_resolutions(self):
        for from_res, targets in VALID_RESOLUTION_TRANSITIONS.items():
            for target in targets:
                assert isinstance(target, TaskResolution), (
                    f"Invalid target {target} in transitions for {from_res}"
                )
