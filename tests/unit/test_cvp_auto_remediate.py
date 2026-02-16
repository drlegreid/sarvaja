"""TDD Tests: CVP auto-remediation after sweep.

Per RELIABILITY-PLAN-01-v1 Priority 3:
CVP sweep should auto-fix known patterns (missing completed_at, agent_id).
"""
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest


class TestRemediateFunctionExists:
    """remediate_violations() can be imported."""

    def test_importable(self):
        from governance.routes.tests.runner_exec import remediate_violations
        assert callable(remediate_violations)


class TestRemediateHTASK003:
    """Auto-fix DONE tasks missing completed_at."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-TEST": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-003",
                    "status": "FAIL",
                    "violations": ["T-MISSING-001", "T-MISSING-002"],
                },
                {
                    "id": "H-TASK-001",
                    "status": "PASS",
                    "violations": [],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec.update_task")
    def test_fixes_completed_at_violations(self, mock_update):
        """Calls update_task for each H-TASK-003 violation."""
        mock_update.return_value = {"task_id": "T-MISSING-001", "completed_at": "2026-02-15T10:00:00"}

        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-TEST")

        assert result["fixes_applied"] >= 2
        assert mock_update.call_count == 2

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-CLEAN": {
            "status": "completed",
            "checks": [
                {"id": "H-TASK-003", "status": "PASS", "violations": []},
            ],
        }
    })
    def test_no_fixes_when_all_pass(self):
        """No remediation needed when all checks pass."""
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-CLEAN")
        assert result["fixes_applied"] == 0

    def test_returns_error_for_unknown_run_id(self):
        """Returns error dict for non-existent run_id."""
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-NONEXISTENT")
        assert "error" in result


class TestRemediateHTASK002:
    """Auto-fix IN_PROGRESS tasks missing agent_id."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-AGENT": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-002",
                    "status": "FAIL",
                    "violations": ["T-NO-AGENT-001"],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec.update_task")
    def test_fixes_agent_id_violations(self, mock_update):
        """Calls update_task with agent_id for H-TASK-002 violations."""
        mock_update.return_value = {"task_id": "T-NO-AGENT-001", "agent_id": "code-agent"}

        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-AGENT")

        assert result["fixes_applied"] >= 1
        # Verify agent_id was set
        call_kwargs = mock_update.call_args_list[0]
        assert "agent_id" in str(call_kwargs)


class TestRemediateDryRun:
    """dry_run mode previews fixes without applying."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-DRY": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-003",
                    "status": "FAIL",
                    "violations": ["T-DRY-001"],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec.update_task")
    def test_dry_run_does_not_apply(self, mock_update):
        """dry_run=True returns planned fixes but doesn't call update_task."""
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-DRY", dry_run=True)

        assert result["dry_run"] is True
        assert result["planned_fixes"] >= 1
        mock_update.assert_not_called()
