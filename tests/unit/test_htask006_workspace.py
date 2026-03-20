"""TDD Tests: H-TASK-006 — workspace assignment check.

Per EPIC-GOV-TASKS-V2 Phase 7:
New heuristic check: worked tasks (IN_PROGRESS/DONE) should have workspace_id.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestHTASK006Registered:
    """H-TASK-006 is registered in HEURISTIC_CHECKS."""

    def test_in_registry(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        ids = [c["id"] for c in HEURISTIC_CHECKS]
        assert "H-TASK-006" in ids

    def test_domain_is_task(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        check = next(c for c in HEURISTIC_CHECKS if c["id"] == "H-TASK-006")
        assert check["domain"] == "TASK"

    def test_has_check_fn(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        check = next(c for c in HEURISTIC_CHECKS if c["id"] == "H-TASK-006")
        assert callable(check["check_fn"])


class TestHTASK006Detection:
    """H-TASK-006 detects worked tasks without workspace_id."""

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_detects_missing_workspace(self, mock_httpx):
        """FAIL when IN_PROGRESS task has no workspace_id."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"task_id": "T-001", "status": "IN_PROGRESS", "workspace_id": None},
                {"task_id": "T-002", "status": "DONE", "workspace_id": "WS-MAIN"},
            ]
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert result["status"] == "FAIL"
        assert "T-001" in result["violations"]
        assert "T-002" not in result["violations"]

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_pass_when_all_linked(self, mock_httpx):
        """PASS when all worked tasks have workspace_id."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"task_id": "T-001", "status": "IN_PROGRESS", "workspace_id": "WS-MAIN"},
                {"task_id": "T-002", "status": "DONE", "workspace_id": "WS-MAIN"},
            ]
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert result["status"] == "PASS"
        assert len(result["violations"]) == 0

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_skips_open_todo_tasks(self, mock_httpx):
        """OPEN/TODO tasks without workspace are not violations."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"task_id": "T-001", "status": "OPEN", "workspace_id": None},
                {"task_id": "T-002", "status": "TODO", "workspace_id": None},
            ]
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_skips_test_tasks(self, mock_httpx):
        """TEST-* tasks are excluded from check."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"task_id": "TEST-001", "status": "IN_PROGRESS", "workspace_id": None},
                {"task_id": "T-002", "status": "IN_PROGRESS", "workspace_id": "WS-MAIN"},
            ]
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert result["status"] == "PASS"
        assert "TEST-001" not in result.get("violations", [])

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_violations_capped_at_20(self, mock_httpx):
        """Violations list capped at 20 entries."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        tasks = [{"task_id": f"T-{i:03d}", "status": "IN_PROGRESS", "workspace_id": None}
                 for i in range(30)]
        mock_resp.json.return_value = {"items": tasks}
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 20

    @patch("governance.routes.tests.heuristic_checks.httpx")
    def test_message_includes_counts(self, mock_httpx):
        """Message includes violation count and total tasks."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"task_id": "T-001", "status": "IN_PROGRESS", "workspace_id": None},
                {"task_id": "T-002", "status": "DONE", "workspace_id": "WS-MAIN"},
                {"task_id": "T-003", "status": "OPEN", "workspace_id": None},
            ]
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.heuristic_checks import check_task_workspace_assignment
        result = check_task_workspace_assignment("http://localhost:8082")

        assert "1" in result["message"]  # 1 violation
        assert "2" in result["message"]  # 2 worked tasks checked


class TestHTASK006RemediationRegistered:
    """H-TASK-006 has remediation in _REMEDIATION_MAP."""

    def test_in_remediation_map(self):
        from governance.routes.tests.runner_exec import _REMEDIATION_MAP
        assert "H-TASK-006" in _REMEDIATION_MAP
