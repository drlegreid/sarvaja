"""
Unit tests for regression runner and playwright checks.

Tests the three-phase regression cycle:
  Phase 1: Static (pytest)
  Phase 2: Heuristic (data integrity)
  Phase 3: Dynamic (Playwright UI)

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock


# =====================================================================
# Regression Runner Tests
# =====================================================================

class TestRegressionRunner:
    """Tests for regression_runner.run_regression()."""

    @patch("governance.routes.tests.regression_runner._run_dynamic_phase")
    @patch("governance.routes.tests.regression_runner._run_heuristic_phase")
    @patch("governance.routes.tests.regression_runner._run_static_phase")
    def test_run_regression_all_phases(self, mock_static, mock_heur, mock_dyn):
        """Regression runs all 3 phases."""
        mock_static.return_value = {
            "name": "Static Tests", "phase": 1, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 10, "failed": 0,
            "skipped": 0, "total": 10,
        }
        mock_heur.return_value = {
            "name": "Heuristic Integrity", "phase": 2, "verdict": "PASS",
            "duration_seconds": 2.0, "passed": 5, "failed": 0,
            "skipped": 0, "errors": 0, "total": 5,
        }
        mock_dyn.return_value = {
            "name": "Dynamic UI (Playwright)", "phase": 3, "verdict": "PASS",
            "duration_seconds": 3.0, "passed": 8, "failed": 0,
            "skipped": 0, "errors": 0, "total": 8,
        }

        from governance.routes.tests.regression_runner import run_regression
        result = run_regression(
            api_base_url="http://test:8082",
            dashboard_url="http://test:8081",
            record_session=False,
        )

        assert result["verdict"] == "PASS"
        assert len(result["phases"]) == 3
        assert result["summary"]["passed_phases"] == 3
        assert result["summary"]["failed_phases"] == 0

    @patch("governance.routes.tests.regression_runner._run_heuristic_phase")
    @patch("governance.routes.tests.regression_runner._run_static_phase")
    def test_skip_dynamic(self, mock_static, mock_heur):
        """skip_dynamic=True runs only 2 phases."""
        mock_static.return_value = {
            "name": "Static Tests", "phase": 1, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 10, "failed": 0,
            "skipped": 0, "total": 10,
        }
        mock_heur.return_value = {
            "name": "Heuristic Integrity", "phase": 2, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 5, "failed": 0,
            "skipped": 0, "errors": 0, "total": 5,
        }

        from governance.routes.tests.regression_runner import run_regression
        result = run_regression(
            api_base_url="http://test:8082",
            skip_dynamic=True,
            record_session=False,
        )

        assert len(result["phases"]) == 2
        assert result["verdict"] == "PASS"

    @patch("governance.routes.tests.regression_runner._run_dynamic_phase")
    @patch("governance.routes.tests.regression_runner._run_heuristic_phase")
    @patch("governance.routes.tests.regression_runner._run_static_phase")
    def test_verdict_fail_on_phase_failure(self, mock_static, mock_heur, mock_dyn):
        """Overall verdict is FAIL if any phase fails."""
        mock_static.return_value = {
            "name": "Static Tests", "phase": 1, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 10, "failed": 0,
            "skipped": 0, "total": 10,
        }
        mock_heur.return_value = {
            "name": "Heuristic Integrity", "phase": 2, "verdict": "FAIL",
            "duration_seconds": 1.0, "passed": 3, "failed": 2,
            "skipped": 0, "errors": 0, "total": 5,
        }
        mock_dyn.return_value = {
            "name": "Dynamic UI", "phase": 3, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 8, "failed": 0,
            "skipped": 0, "errors": 0, "total": 8,
        }

        from governance.routes.tests.regression_runner import run_regression
        result = run_regression(
            api_base_url="http://test:8082",
            record_session=False,
        )

        assert result["verdict"] == "FAIL"
        assert result["summary"]["failed_phases"] == 1

    @patch("governance.routes.tests.regression_runner._run_dynamic_phase")
    @patch("governance.routes.tests.regression_runner._run_heuristic_phase")
    @patch("governance.routes.tests.regression_runner._run_static_phase")
    def test_verdict_error_on_phase_error(self, mock_static, mock_heur, mock_dyn):
        """Overall verdict is ERROR if any phase errors."""
        mock_static.return_value = {
            "name": "Static", "phase": 1, "verdict": "ERROR",
            "duration_seconds": 0.1, "error": "timeout",
        }
        mock_heur.return_value = {
            "name": "Heuristic", "phase": 2, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 5, "failed": 0,
            "skipped": 0, "errors": 0, "total": 5,
        }
        mock_dyn.return_value = {
            "name": "Dynamic", "phase": 3, "verdict": "PASS",
            "duration_seconds": 1.0, "passed": 8, "failed": 0,
            "skipped": 0, "errors": 0, "total": 8,
        }

        from governance.routes.tests.regression_runner import run_regression
        result = run_regression(
            api_base_url="http://test:8082",
            record_session=False,
        )

        assert result["verdict"] == "ERROR"

    def test_result_has_timestamp(self):
        """Result includes ISO timestamp."""
        with patch("governance.routes.tests.regression_runner._run_static_phase") as ms, \
             patch("governance.routes.tests.regression_runner._run_heuristic_phase") as mh:
            ms.return_value = {"name": "S", "phase": 1, "verdict": "PASS",
                               "duration_seconds": 0, "passed": 0, "failed": 0,
                               "skipped": 0, "total": 0}
            mh.return_value = {"name": "H", "phase": 2, "verdict": "PASS",
                               "duration_seconds": 0, "passed": 0, "failed": 0,
                               "skipped": 0, "errors": 0, "total": 0}

            from governance.routes.tests.regression_runner import run_regression
            result = run_regression(
                api_base_url="http://test:8082",
                skip_dynamic=True,
                record_session=False,
            )
            assert "timestamp" in result
            assert "T" in result["timestamp"]  # ISO format


# =====================================================================
# Playwright Checks Tests
# =====================================================================

class TestPlaywrightChecks:
    """Tests for playwright_checks module."""

    def test_tally_pass(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "PASS"}, 0, 0, 0)
        assert p == 1 and f == 0 and e == 0

    def test_tally_fail(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "FAIL"}, 0, 0, 0)
        assert p == 0 and f == 1 and e == 0

    def test_tally_error(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "ERROR"}, 0, 0, 0)
        assert p == 0 and f == 0 and e == 1

    def test_dashboard_screens_defined(self):
        from governance.routes.tests.playwright_checks import DASHBOARD_SCREENS
        assert len(DASHBOARD_SCREENS) >= 6
        nav_keys = [s[0] for s in DASHBOARD_SCREENS]
        assert "rules" in nav_keys
        assert "tasks" in nav_keys
        assert "sessions" in nav_keys
        assert "agents" in nav_keys

    @patch("governance.routes.tests.playwright_api_fallback.httpx")
    def test_check_api_data_integrity_pass(self, mock_httpx):
        """Data integrity check passes when all endpoints return 200 with pagination."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [], "pagination": {"total": 0, "offset": 0, "limit": 1, "has_more": False, "returned": 0}
        }
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        result = check_api_data_integrity("http://test:8082")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-INTEGRITY-001"

    @patch("governance.routes.tests.playwright_api_fallback.httpx")
    def test_check_api_data_integrity_missing_pagination(self, mock_httpx):
        """Data integrity fails when pagination missing."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": []}  # No pagination
        mock_httpx.get.return_value = mock_resp

        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        result = check_api_data_integrity("http://test:8082")
        assert result["status"] == "FAIL"
        assert len(result["violations"]) > 0

    @patch("governance.routes.tests.playwright_checks._try_playwright_import")
    @patch("governance.routes.tests.playwright_api_fallback.httpx")
    def test_api_fallback_used_when_no_playwright(self, mock_httpx, mock_pw):
        """Falls back to API checks when playwright not installed."""
        mock_pw.return_value = None
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [], "pagination": {
            "total": 0, "offset": 0, "limit": 5, "has_more": False, "returned": 0
        }}
        mock_resp.text = ""
        mock_httpx.get.return_value = mock_resp
        mock_httpx.post.return_value = mock_resp

        from governance.routes.tests.playwright_checks import run_playwright_checks
        result = run_playwright_checks(
            dashboard_url="http://test:8081",
            api_base_url="http://test:8082",
        )
        assert "checks" in result
        assert "summary" in result
        assert result["summary"]["total"] > 0


# =====================================================================
# Runner Endpoint Tests
# =====================================================================

class TestRegressionEndpoint:
    """Tests for the regression endpoint in runner.py."""

    def test_categories_include_regression(self):
        """Regression appears in test categories."""
        import asyncio
        from governance.routes.tests.runner import list_test_categories
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        ids = [c["id"] for c in result["categories"]]
        assert "regression" in ids

    def test_regression_category_is_default(self):
        """Regression category marked as default."""
        import asyncio
        from governance.routes.tests.runner import list_test_categories
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        reg = [c for c in result["categories"] if c["id"] == "regression"][0]
        assert "default" in reg["description"].lower()


# =====================================================================
# UI View Tests
# =====================================================================

class TestRegressionUI:
    """Tests for regression UI components."""

    def test_regression_card_function_exists(self):
        from agent.governance_ui.views.tests_view import build_regression_card
        assert callable(build_regression_card)

    def test_regression_phases_panel_exists(self):
        from agent.governance_ui.views.tests_view import build_regression_phases_panel
        assert callable(build_regression_phases_panel)

    def test_state_has_tests_running(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "tests_running" in state
        assert state["tests_running"] is False

    def test_state_has_tests_current_run(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "tests_current_run" in state
        assert state["tests_current_run"] is None
