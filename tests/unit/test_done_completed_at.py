"""TDD Tests for Cycle 13-14: DONE Tasks Must Have completed_at.

H-TASK-003: Every task with status=DONE must have a completed_at timestamp.
Prevention: update_task() auto-sets completed_at on DONE transition.
"""
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest


class TestUpdateTaskSetsCompletedAt:
    """update_task auto-sets completed_at when status becomes DONE."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_status_done_sets_completed_at(self, mock_client_fn):
        """Setting status to DONE auto-populates completed_at."""
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.update_task_status.return_value = True
        # P14: _preload_task_from_typedb() now always refreshes — mock get_task()
        task_obj = MagicMock()
        task_obj.name = "Test task"
        task_obj.phase = "P14"
        task_obj.status = "IN_PROGRESS"
        task_obj.agent_id = "code-agent"
        task_obj.created_at = datetime(2026, 3, 24)
        task_obj.claimed_at = None
        task_obj.completed_at = None
        task_obj.linked_sessions = ["SESSION-DONE-TEST"]
        task_obj.linked_documents = [".claude/plans/test-plan.md"]
        task_obj.linked_rules = []
        task_obj.linked_commits = []
        task_obj.summary = "Test > Done > Completed At > Timestamp"
        mock_client.get_task.return_value = task_obj

        from governance.services.tasks_mutations import _tasks_store, update_task

        task_id = "T-DONE-TEST-001"
        _tasks_store[task_id] = {
            "task_id": task_id,
            "description": "Test task",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "Test > Done > Completed At > Timestamp",
            "linked_sessions": ["SESSION-DONE-TEST"],
            "linked_documents": [".claude/plans/test-plan.md"],
            "completed_at": None,
        }

        try:
            result = update_task(task_id, status="DONE")
            assert result["completed_at"] is not None
            # Verify it's a valid ISO timestamp
            parsed = datetime.fromisoformat(result["completed_at"])
            assert isinstance(parsed, datetime)
        finally:
            _tasks_store.pop(task_id, None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_status_non_done_does_not_set_completed_at(self, mock_client_fn):
        """Setting status to IN_PROGRESS does NOT set completed_at."""
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.update_task_status.return_value = True

        from governance.services.tasks_mutations import _tasks_store, update_task

        task_id = "T-DONE-TEST-002"
        _tasks_store[task_id] = {
            "task_id": task_id,
            "description": "Test task 2",
            "status": "TODO",
            "completed_at": None,
        }

        try:
            result = update_task(task_id, status="IN_PROGRESS")
            assert result.get("completed_at") is None
        finally:
            _tasks_store.pop(task_id, None)


class TestHeuristicCheckPasses:
    """H-TASK-003 heuristic check validates completed_at presence."""

    def test_heuristic_check_importable(self):
        """check_done_completed_at can be imported."""
        from governance.routes.tests.heuristic_checks import check_done_completed_at
        assert callable(check_done_completed_at)

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_all_done_have_completed_at_passes(self, mock_api):
        """All DONE tasks with completed_at → PASS."""
        mock_api.return_value = [
            {"task_id": "T-1", "status": "DONE", "completed_at": "2026-02-15T10:00:00"},
            {"task_id": "T-2", "status": "DONE", "completed_at": "2026-02-15T11:00:00"},
        ]

        from governance.routes.tests.heuristic_checks import check_done_completed_at
        result = check_done_completed_at("http://localhost:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_missing_completed_at_fails(self, mock_api):
        """DONE task without completed_at → FAIL."""
        mock_api.return_value = [
            {"task_id": "T-BAD", "status": "DONE", "completed_at": None},
        ]

        from governance.routes.tests.heuristic_checks import check_done_completed_at
        result = check_done_completed_at("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert "T-BAD" in result["violations"]
