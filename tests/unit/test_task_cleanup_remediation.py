"""
Tests for Task Cleanup Remediation Script.

Per EPIC-GOV-TASKS-V2 Phase 9e: Data quality remediation covering
junk task detection, session batch-linking, and EPIC phase closure.

TDD-first: these tests written BEFORE implementation.
Created: 2026-03-21
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _task(tid, name="Real task", status="OPEN", body="Has body",
          task_type="feature", linked_sessions=None, phase="P10",
          created_at=None, completed_at=None):
    return {
        "task_id": tid, "name": name, "status": status, "body": body,
        "task_type": task_type, "linked_sessions": linked_sessions or [],
        "phase": phase, "created_at": created_at, "completed_at": completed_at,
    }


def _session(sid, start_time, end_time=None, status="COMPLETED"):
    return {
        "session_id": sid, "start_time": start_time,
        "end_time": end_time, "status": status,
    }


# ---------------------------------------------------------------------------
# TestJunkDetection
# ---------------------------------------------------------------------------

class TestJunkDetection:
    """detect_junk_tasks() identifies test artifact tasks."""

    def test_crud_prefix_detected(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("CRUD-5A0FE054", "CRUD lifecycle test")]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 1
        assert result["details"][0]["task_id"] == "CRUD-5A0FE054"

    def test_inttest_prefix_detected(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("INTTEST-XENT-4DFBEF12", "Cross-entity test task")]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 1

    def test_generic_name_null_body_detected(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("BUG-002", "Agent task", body=None)]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 1

    def test_generic_name_with_body_not_flagged(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("BUG-002", "Agent task", body="Real bug description")]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 0

    def test_legitimate_task_not_flagged(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("FEAT-006", "Add WASD movement controls", body="Real feature")]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 0

    def test_e2e_tax_prefix_detected(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("E2E-TAX-001", "E2E taxonomy test", body=None)]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 1

    def test_lifecycle_test_with_null_body(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [_task("BUG-001", "Lifecycle test", body=None)]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 1

    def test_multiple_junk_detected(self):
        from scripts.remediate_task_cleanup import detect_junk_tasks
        tasks = [
            _task("CRUD-AAA", "CRUD lifecycle test"),
            _task("INTTEST-BBB", "Integration Test Task"),
            _task("BUG-002", "Agent task", body=None),
            _task("FEAT-006", "Add WASD controls", body="Real"),
        ]
        result = detect_junk_tasks(tasks)
        assert result["found"] == 3


# ---------------------------------------------------------------------------
# TestSessionBatchLink
# ---------------------------------------------------------------------------

class TestSessionBatchLink:
    """batch_link_sessions() timestamp-based matching."""

    def test_only_worked_tasks_processed(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [
            _task("T-1", status="OPEN"),
            _task("T-2", status="IN_PROGRESS", created_at="2026-03-20T10:00:00"),
            _task("T-3", status="DONE", created_at="2026-03-20T10:00:00"),
        ]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result["skipped"] >= 1  # OPEN task skipped

    def test_already_linked_tasks_skipped(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [_task("T-1", status="DONE", linked_sessions=["S-1"],
                       created_at="2026-03-20T10:00:00")]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result["skipped"] >= 1

    def test_timestamp_overlap_matches(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [_task("T-1", status="DONE", created_at="2026-03-20T10:30:00")]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result["matched"] >= 1

    def test_no_overlap_no_match(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [_task("T-1", status="DONE", created_at="2026-03-19T10:00:00")]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result["matched"] == 0

    def test_dry_run_does_not_mutate(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [_task("T-1", status="DONE", created_at="2026-03-20T10:30:00")]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result.get("applied", 0) == 0

    def test_empty_tasks_returns_zeros(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        result = batch_link_sessions([], [], dry_run=True)
        assert result["matched"] == 0
        assert result["skipped"] == 0

    def test_null_created_at_skipped(self):
        from scripts.remediate_task_cleanup import batch_link_sessions
        tasks = [_task("T-1", status="DONE", created_at=None)]
        sessions = [_session("S-1", "2026-03-20T09:00:00", "2026-03-20T12:00:00")]
        result = batch_link_sessions(tasks, sessions, dry_run=True)
        assert result["skipped"] >= 1


# ---------------------------------------------------------------------------
# TestEpicPhaseDetection
# ---------------------------------------------------------------------------

class TestEpicPhaseDetection:
    """detect_completed_epic_tasks() finds stale OPEN phase tasks."""

    DONE_PHASES = {
        "EPIC-TASKS-V2-P9A": "V2-P9A",
        "EPIC-TASKS-V2-P9B": "V2-P9B",
    }

    def test_open_task_in_done_phase_detected(self):
        from scripts.remediate_task_cleanup import detect_completed_epic_tasks
        tasks = [_task("EPIC-TASKS-V2-P9A", status="OPEN", phase="V2-P9A")]
        result = detect_completed_epic_tasks(tasks, self.DONE_PHASES)
        assert result["found"] == 1

    def test_done_task_in_done_phase_not_flagged(self):
        from scripts.remediate_task_cleanup import detect_completed_epic_tasks
        tasks = [_task("EPIC-TASKS-V2-P9A", status="DONE", phase="V2-P9A")]
        result = detect_completed_epic_tasks(tasks, self.DONE_PHASES)
        assert result["found"] == 0

    def test_open_task_in_active_phase_not_flagged(self):
        from scripts.remediate_task_cleanup import detect_completed_epic_tasks
        tasks = [_task("EPIC-RULES-V3-P1", status="OPEN", phase="V3-P1")]
        result = detect_completed_epic_tasks(tasks, self.DONE_PHASES)
        assert result["found"] == 0

    def test_multiple_stale_detected(self):
        from scripts.remediate_task_cleanup import detect_completed_epic_tasks
        tasks = [
            _task("EPIC-TASKS-V2-P9A", status="OPEN", phase="V2-P9A"),
            _task("EPIC-TASKS-V2-P9B", status="OPEN", phase="V2-P9B"),
            _task("EPIC-RULES-V3-P1", status="OPEN", phase="V3-P1"),
        ]
        result = detect_completed_epic_tasks(tasks, self.DONE_PHASES)
        assert result["found"] == 2

    def test_empty_tasks_returns_zero(self):
        from scripts.remediate_task_cleanup import detect_completed_epic_tasks
        result = detect_completed_epic_tasks([], self.DONE_PHASES)
        assert result["found"] == 0
