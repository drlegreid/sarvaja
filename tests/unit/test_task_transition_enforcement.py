"""
Unit tests for status transition enforcement in update_task().

SRVJ-BUG-DEAD-LIFECYCLE-01: validate_status_transition() was defined with
36+ passing unit tests but NEVER called from production code. Phase 1 of
EPIC-TASK-WORKFLOW-HEAL-01 wires it into tasks_mutations.update_task().

BDD Scenarios:
  - TODO -> DONE raises ValueError (must go through IN_PROGRESS)
  - OPEN -> IN_PROGRESS succeeds
  - DONE -> BLOCKED raises ValueError
  - IN_PROGRESS -> DONE succeeds (DONE gate runs after)
  - CANCELED -> DONE raises ValueError
  - First update (no prior status) accepts any valid status
  - CLOSED normalizes to DONE before validation
  - Same-status transition is a no-op (allowed)
  - Legacy/unknown status in store skips validation gracefully
"""

from unittest.mock import patch, MagicMock

import pytest

_SVC = "governance.services.tasks_mutations"


def _make_task(task_id="T-TEST-001", status="TODO", **extra):
    """Build a minimal task dict for _tasks_store."""
    task = {
        "task_id": task_id,
        "description": "test",
        "status": status,
        "phase": "",
        "agent_id": None,
        "created_at": "2026-01-01T00:00:00",
        "priority": "MEDIUM",
        "task_type": "chore",
        "linked_sessions": [],
        "linked_documents": [],
        "linked_rules": [],
        "linked_commits": [],
    }
    task.update(extra)
    return task


@pytest.fixture(autouse=True)
def _isolate_store():
    """Isolate _tasks_store and stub TypeDB + audit for every test."""
    with (
        patch(f"{_SVC}.get_typedb_client", return_value=None),
        patch(f"{_SVC}.record_audit"),
        patch(f"{_SVC}._monitor"),
        patch(f"{_SVC}.log_event"),
    ):
        yield


# ── Scenario: Invalid transitions raise ValueError ──────────────────


class TestInvalidTransitionsBlocked:
    """Transitions not in VALID_STATUS_TRANSITIONS must raise ValueError."""

    def test_todo_to_done_blocked(self):
        """TODO -> DONE skips IN_PROGRESS — must be rejected."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-1"] = _make_task("T-1", status="TODO")

        with pytest.raises(ValueError, match="Invalid status transition: TODO → DONE"):
            update_task("T-1", status="DONE")

    def test_done_to_blocked_blocked(self):
        """DONE -> BLOCKED is not a valid reopen path."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-2"] = _make_task("T-2", status="DONE")

        with pytest.raises(ValueError, match="Invalid status transition: DONE → BLOCKED"):
            update_task("T-2", status="BLOCKED")

    def test_canceled_to_done_blocked(self):
        """CANCELED -> DONE must go through OPEN/TODO first."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-3"] = _make_task("T-3", status="CANCELED")

        with pytest.raises(ValueError, match="Invalid status transition: CANCELED → DONE"):
            update_task("T-3", status="DONE")

    def test_blocked_to_done_blocked(self):
        """BLOCKED -> DONE must go through IN_PROGRESS first."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-4"] = _make_task("T-4", status="BLOCKED")

        with pytest.raises(ValueError, match="Invalid status transition: BLOCKED → DONE"):
            update_task("T-4", status="DONE")

    def test_todo_to_blocked_blocked(self):
        """TODO -> BLOCKED is not valid (only IN_PROGRESS/CANCELED)."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-5"] = _make_task("T-5", status="TODO")

        with pytest.raises(ValueError, match="Invalid status transition: TODO → BLOCKED"):
            update_task("T-5", status="BLOCKED")


# ── Scenario: Valid transitions succeed ──────────────────────────────


class TestValidTransitionsAllowed:
    """Transitions listed in VALID_STATUS_TRANSITIONS must pass."""

    def test_open_to_in_progress(self):
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-10"] = _make_task("T-10", status="OPEN")
        result = update_task("T-10", status="IN_PROGRESS")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"

    def test_in_progress_to_done(self):
        """IN_PROGRESS -> DONE is valid; DONE gate runs separately after."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-11"] = _make_task(
            "T-11", status="IN_PROGRESS", agent_id="code-agent",
            summary="Has summary", task_type="chore",
        )
        result = update_task("T-11", status="DONE")

        assert result is not None
        assert result["status"] == "DONE"

    def test_in_progress_to_blocked(self):
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-12"] = _make_task("T-12", status="IN_PROGRESS")
        result = update_task("T-12", status="BLOCKED")

        assert result is not None
        assert result["status"] == "BLOCKED"

    def test_blocked_to_in_progress(self):
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-13"] = _make_task("T-13", status="BLOCKED")
        result = update_task("T-13", status="IN_PROGRESS")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"

    def test_done_to_open_reopen(self):
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-14"] = _make_task("T-14", status="DONE")
        result = update_task("T-14", status="OPEN")

        assert result is not None
        assert result["status"] == "OPEN"

    def test_canceled_to_todo_reactivate(self):
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-15"] = _make_task("T-15", status="CANCELED")
        result = update_task("T-15", status="TODO")

        assert result is not None
        assert result["status"] == "TODO"

    def test_same_status_noop(self):
        """Same-status transition is always allowed."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-16"] = _make_task("T-16", status="IN_PROGRESS")
        result = update_task("T-16", status="IN_PROGRESS")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"


# ── Scenario: First update (no prior status) ────────────────────────


class TestFirstUpdateAllowsAnyStatus:
    """When task has no prior status in _tasks_store, allow any valid status."""

    def test_first_update_skips_transition_check(self):
        """Task not in _tasks_store — no from_status, transition check skipped."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        # Task not in _tasks_store — update_task returns None (no client, no store)
        # Use IN_PROGRESS to avoid DONE gate (which fires independently)
        result = update_task("T-NEW-1", status="IN_PROGRESS")

        # Returns None because task doesn't exist anywhere
        assert result is None

    def test_first_update_no_prior_status_field(self):
        """Task in store but status field is None — skip validation."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-NEW-2"] = _make_task("T-NEW-2", status=None)
        result = update_task("T-NEW-2", status="IN_PROGRESS")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"


# ── Scenario: CLOSED normalizes to DONE before validation ────────────


class TestClosedNormalization:
    """CLOSED is normalized to DONE at service boundary BEFORE transition check."""

    def test_closed_normalizes_to_done(self):
        """IN_PROGRESS -> CLOSED normalizes to IN_PROGRESS -> DONE (valid)."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-20"] = _make_task(
            "T-20", status="IN_PROGRESS", agent_id="code-agent",
            summary="Has summary", task_type="chore",
        )
        result = update_task("T-20", status="CLOSED")

        assert result is not None
        assert result["status"] == "DONE"  # Normalized

    def test_closed_from_todo_still_blocked(self):
        """TODO -> CLOSED normalizes to TODO -> DONE — still invalid."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-21"] = _make_task("T-21", status="TODO")

        with pytest.raises(ValueError, match="Invalid status transition: TODO → DONE"):
            update_task("T-21", status="CLOSED")


# ── Scenario: Legacy status in store degrades gracefully ─────────────


class TestLegacyStatusGracefulDegradation:
    """Unknown status values in _tasks_store skip validation with a warning."""

    def test_unknown_current_status_skips_check(self):
        """Legacy status like 'REVIEW' in store should not crash."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-30"] = _make_task("T-30", status="REVIEW")
        # Should not raise — logs warning and skips validation
        result = update_task("T-30", status="IN_PROGRESS")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"


# ── Scenario: Case normalization happens before validation ───────────


class TestCaseNormalization:
    """Status is uppercased before transition validation runs."""

    def test_lowercase_status_normalized(self):
        """'in_progress' → 'IN_PROGRESS' before validation."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-40"] = _make_task("T-40", status="OPEN")
        result = update_task("T-40", status="in_progress")

        assert result is not None
        assert result["status"] == "IN_PROGRESS"

    def test_lowercase_invalid_still_blocked(self):
        """'done' normalized to 'DONE', still blocked from TODO."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        _tasks_store["T-41"] = _make_task("T-41", status="TODO")

        with pytest.raises(ValueError, match="Invalid status transition: TODO → DONE"):
            update_task("T-41", status="done")
