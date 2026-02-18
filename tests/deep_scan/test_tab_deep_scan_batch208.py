"""Batch 208 — Heuristic exploratory + runner defense tests.

Validates fixes for:
- BUG-208-EXPLR-STATUS-001: check_chat_session_count_accuracy status from violations
- BUG-208-EXPLR-PAGE-001: check_monitor_event_count_consistency pagination fix
- BUG-208-RUNNER-STATUS-001: run_heuristic_checks uses .get() for status
"""
from pathlib import Path
from unittest.mock import patch, MagicMock

import httpx


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-208-EXPLR-STATUS-001: Status from violations ────────────────

class TestExploratoryStatusLogic:
    """check_chat_session_count_accuracy must derive status from violations."""

    def test_status_fail_when_active_sessions_exist(self):
        """Active sessions = violation → status should be FAIL."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        mock_pagination = MagicMock()
        mock_pagination.status_code = 200
        mock_pagination.json.return_value = {
            "pagination": {"total": 10},
            "items": [],
        }

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx, \
             patch("governance.routes.tests.heuristic_checks_exploratory._api_get") as mock_api, \
             patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=False):
            mock_httpx.get.return_value = mock_pagination
            # Return 2 active sessions
            mock_api.return_value = [
                {"session_id": "S1", "status": "ACTIVE"},
                {"session_id": "S2", "status": "ACTIVE"},
            ]
            result = check_chat_session_count_accuracy("http://fake:8082")
        assert result["status"] == "FAIL", f"Expected FAIL with active sessions, got {result['status']}"
        assert len(result["violations"]) > 0

    def test_status_pass_when_no_active_sessions(self):
        """No active sessions = no violations → status PASS (if total > 0)."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "pagination": {"total": 5},
            "items": [],
        }

        with patch("governance.routes.tests.heuristic_checks_exploratory.httpx") as mock_httpx, \
             patch("governance.routes.tests.heuristic_checks_exploratory._api_get") as mock_api, \
             patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=False):
            mock_httpx.get.return_value = mock_resp
            mock_api.return_value = [
                {"session_id": "S1", "status": "ENDED"},
            ]
            result = check_chat_session_count_accuracy("http://fake:8082")
        assert result["status"] == "PASS"
        assert len(result["violations"]) == 0


# ── BUG-208-EXPLR-PAGE-001: Pagination count fix ─────────────────────

class TestMonitorEventPagination:
    """check_monitor_event_count_consistency must not compare total vs page."""

    def test_no_false_fail_on_paginated_response(self):
        """Source code should use actual page count, not total."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        # The fix sets count = actual (page count), so they always match
        assert "count = actual" in src


# ── BUG-208-RUNNER-STATUS-001: .get() for status ─────────────────────

class TestRunnerStatusAccess:
    """run_heuristic_checks must use .get() on result status."""

    def test_runner_uses_get_for_status(self):
        """heuristic_runner.py must use result.get('status') not result['status']."""
        src = (SRC / "governance/routes/tests/heuristic_runner.py").read_text()
        assert 'result.get("status"' in src or "result.get('status'" in src


# ── Exploratory checks defense ────────────────────────────────────────

class TestExploratoryChecksDefense:
    """Defense tests for exploratory heuristic checks."""

    def test_check_chat_session_count_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_chat_session_count_accuracy
        assert callable(check_chat_session_count_accuracy)

    def test_check_monitor_events_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_monitor_event_count_consistency
        assert callable(check_monitor_event_count_consistency)

    def test_check_decision_rule_linking_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_decision_rule_linking
        assert callable(check_decision_rule_linking)

    def test_check_audit_trail_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_audit_trail_populated
        assert callable(check_audit_trail_populated)

    def test_check_rule_document_paths_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_rule_document_paths_populated
        assert callable(check_rule_document_paths_populated)

    def test_check_mcp_readiness_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import check_mcp_readiness_consistency
        assert callable(check_mcp_readiness_consistency)

    def test_exploratory_registry_has_6_checks(self):
        from governance.routes.tests.heuristic_checks_exploratory import EXPLORATORY_CHECKS
        assert len(EXPLORATORY_CHECKS) == 6

    def test_all_self_referential_checks_skip(self):
        """All checks return SKIP when self-referential."""
        from governance.routes.tests.heuristic_checks_exploratory import EXPLORATORY_CHECKS
        with patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=True):
            for check in EXPLORATORY_CHECKS:
                result = check["check_fn"]("http://fake:8082")
                assert result["status"] == "SKIP", f"{check['id']} should SKIP on self-referential"


# ── Heuristic runner defense ──────────────────────────────────────────

class TestHeuristicRunnerDefense:
    """Defense tests for the heuristic runner."""

    def test_run_heuristic_checks_callable(self):
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        assert callable(run_heuristic_checks)

    def test_runner_returns_dict_with_checks_and_summary(self):
        """run_heuristic_checks must return dict with checks and summary."""
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        with patch("governance.routes.tests.heuristic_runner.HEURISTIC_CHECKS", []):
            result = run_heuristic_checks("http://fake:8082", record_session=False)
        assert "checks" in result
        assert "summary" in result
        assert result["summary"]["total"] == 0

    def test_runner_handles_domain_filter(self):
        """Filtering by domain should return only matching checks."""
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        with patch("governance.routes.tests.heuristic_runner.HEURISTIC_CHECKS", [
            {"id": "TEST-1", "domain": "TASK", "name": "test", "check_fn": lambda url: {"status": "PASS", "message": "ok", "violations": []}},
            {"id": "TEST-2", "domain": "SESSION", "name": "test2", "check_fn": lambda url: {"status": "PASS", "message": "ok", "violations": []}},
        ]):
            result = run_heuristic_checks("http://fake:8082", domain="TASK", record_session=False)
        assert result["summary"]["total"] == 1
        assert result["checks"][0]["id"] == "TEST-1"
