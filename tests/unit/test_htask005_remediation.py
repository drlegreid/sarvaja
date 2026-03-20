"""TDD Tests: H-TASK-005 remediation — link orphan tasks to active session.

Per EPIC-GOV-TASKS-V2 Phase 7:
CVP sweep should auto-fix H-TASK-005 violations (worked tasks without linked_sessions)
by linking them to the current active session.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestHTASK005RemediationRegistered:
    """H-TASK-005 exists in _REMEDIATION_MAP."""

    def test_in_remediation_map(self):
        from governance.routes.tests.runner_exec import _REMEDIATION_MAP
        assert "H-TASK-005" in _REMEDIATION_MAP

    def test_remediation_is_callable(self):
        from governance.routes.tests.runner_exec import _REMEDIATION_MAP
        assert callable(_REMEDIATION_MAP["H-TASK-005"])


class TestHTASK005RemediationLinksSession:
    """H-TASK-005 remediation calls link_task_to_session with active session."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-ORPHAN": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-005",
                    "status": "FAIL",
                    "violations": ["T-ORPHAN-001", "T-ORPHAN-002"],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec._remediate_session_linkage")
    def test_remediates_all_violations(self, mock_remediate):
        """Calls remediation for each H-TASK-005 violation."""
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-ORPHAN")

        assert result["fixes_applied"] == 2
        assert mock_remediate.call_count == 2
        mock_remediate.assert_any_call("T-ORPHAN-001")
        mock_remediate.assert_any_call("T-ORPHAN-002")

    @patch("governance.routes.tests.runner_exec.link_task_to_session")
    @patch("governance.routes.tests.runner_exec._get_active_session_id",
           return_value="SESSION-2026-03-21-CVP")
    def test_links_to_active_session(self, mock_get_sid, mock_link):
        """_remediate_session_linkage links task to active session."""
        mock_link.return_value = True
        from governance.routes.tests.runner_exec import _remediate_session_linkage
        _remediate_session_linkage("T-ORPHAN-001")

        mock_get_sid.assert_called_once()
        mock_link.assert_called_once_with("T-ORPHAN-001", "SESSION-2026-03-21-CVP")

    @patch("governance.routes.tests.runner_exec._get_active_session_id",
           return_value=None)
    def test_raises_when_no_active_session(self, mock_get_sid):
        """Raises ValueError if no active session available."""
        from governance.routes.tests.runner_exec import _remediate_session_linkage
        with pytest.raises(ValueError, match="No active session"):
            _remediate_session_linkage("T-ORPHAN-001")

    @patch("governance.routes.tests.runner_exec.link_task_to_session")
    @patch("governance.routes.tests.runner_exec._get_active_session_id",
           return_value="SESSION-2026-03-21-CVP")
    def test_raises_when_link_fails(self, mock_get_sid, mock_link):
        """Raises if link_task_to_session returns False."""
        mock_link.return_value = False
        from governance.routes.tests.runner_exec import _remediate_session_linkage
        with pytest.raises(RuntimeError, match="Failed to link"):
            _remediate_session_linkage("T-ORPHAN-001")


class TestHTASK005DryRun:
    """dry_run mode for H-TASK-005 previews without linking."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-DRY5": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-005",
                    "status": "FAIL",
                    "violations": ["T-DRY-ORPHAN-001"],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec._remediate_session_linkage")
    def test_dry_run_does_not_link(self, mock_remediate):
        """dry_run=True records planned fix but doesn't call remediation."""
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-DRY5", dry_run=True)

        assert result["dry_run"] is True
        assert result["planned_fixes"] >= 1
        mock_remediate.assert_not_called()


class TestHTASK005EndToEnd:
    """Full CVP sweep → remediate flow for H-TASK-005."""

    @patch("governance.routes.tests.runner_exec._test_results", {
        "CVP-T3-E2E": {
            "status": "failed",
            "checks": [
                {
                    "id": "H-TASK-005",
                    "status": "FAIL",
                    "violations": ["T-E2E-001"],
                },
                {
                    "id": "H-TASK-003",
                    "status": "FAIL",
                    "violations": ["T-E2E-002"],
                },
            ],
        }
    })
    @patch("governance.routes.tests.runner_exec._remediate_session_linkage")
    @patch("governance.routes.tests.runner_exec.update_task")
    def test_remediates_both_005_and_003(self, mock_update, mock_remediate):
        """CVP sweep with both H-TASK-005 and H-TASK-003 violations remediates both."""
        mock_update.return_value = {"task_id": "T-E2E-002"}
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("CVP-T3-E2E")

        assert result["fixes_applied"] == 2
        mock_remediate.assert_called_once_with("T-E2E-001")
        mock_update.assert_called_once()
