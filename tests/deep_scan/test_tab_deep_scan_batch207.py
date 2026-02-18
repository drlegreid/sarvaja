"""Batch 207 — Heuristic runner + store defense tests.

Validates fixes for:
- BUG-207-STORE-001: _test_results dict cap to prevent unbounded growth
- BUG-207-INGESTION-001: False PASS in check_cc_ingestion_complete
"""
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-207-STORE-001: _test_results cap ─────────────────────────────

class TestTestResultsCap:
    """_test_results must have a retention cap."""

    def test_max_test_results_constant_exists(self):
        """runner_store.py must define _MAX_TEST_RESULTS."""
        from governance.routes.tests.runner_store import _MAX_TEST_RESULTS
        assert _MAX_TEST_RESULTS == 200

    def test_cap_function_exists(self):
        """runner_store.py must have _cap_test_results()."""
        from governance.routes.tests.runner_store import _cap_test_results
        assert callable(_cap_test_results)

    def test_cap_evicts_oldest(self):
        """_cap_test_results evicts oldest when over limit."""
        from governance.routes.tests import runner_store
        original = dict(runner_store._test_results)
        try:
            runner_store._test_results.clear()
            # Insert 210 entries
            for i in range(210):
                runner_store._test_results[f"RUN-{i:05d}"] = {"status": "ok"}
            assert len(runner_store._test_results) == 210
            runner_store._cap_test_results()
            assert len(runner_store._test_results) <= 200
            # Oldest should have been evicted
            assert "RUN-00000" not in runner_store._test_results
        finally:
            runner_store._test_results.clear()
            runner_store._test_results.update(original)

    def test_cap_noop_under_limit(self):
        """_cap_test_results is a no-op when under limit."""
        from governance.routes.tests import runner_store
        original = dict(runner_store._test_results)
        try:
            runner_store._test_results.clear()
            runner_store._test_results["TEST-1"] = {"status": "ok"}
            runner_store._cap_test_results()
            assert "TEST-1" in runner_store._test_results
        finally:
            runner_store._test_results.clear()
            runner_store._test_results.update(original)


# ── BUG-207-INGESTION-001: False PASS guard ──────────────────────────

class TestIngestionCheckSkipGuard:
    """check_cc_ingestion_complete must SKIP when checked==0."""

    def test_returns_skip_when_api_unreachable(self):
        """When all ingestion status calls fail, result should be SKIP."""
        from governance.routes.tests.heuristic_checks_cc import (
            check_cc_ingestion_complete,
        )
        # Mock _api_get to return sessions but fail on status checks
        with patch(
            "governance.routes.tests.heuristic_checks_cc._api_get"
        ) as mock_api:
            # First call: return some CC sessions
            # Subsequent calls: return [] (API failure for ingestion status)
            mock_api.side_effect = lambda url, ep: (
                [
                    {"session_id": "SESSION-2026-02-01-CC-TEST1"},
                    {"session_id": "SESSION-2026-02-01-CC-TEST2"},
                ]
                if "sessions" in ep
                else []  # ingestion status returns empty (API failure)
            )
            result = check_cc_ingestion_complete("http://fake:8082")
        assert result["status"] == "SKIP", f"Expected SKIP, got {result['status']}"
        assert "unreachable" in result["message"].lower() or "could not" in result["message"].lower()

    def test_skip_guard_code_exists(self):
        """Source code must check for checked == 0."""
        src = (SRC / "governance/routes/tests/heuristic_checks_cc.py").read_text()
        assert "checked == 0" in src


# ── Runner store defense ─────────────────────────────────────────────

class TestRunnerStoreDefense:
    """Defense tests for runner_store module."""

    def test_test_results_is_dict(self):
        from governance.routes.tests.runner_store import _test_results
        assert isinstance(_test_results, dict)

    def test_resolve_test_root_returns_string(self):
        from governance.routes.tests.runner_store import _resolve_test_root
        result = _resolve_test_root()
        assert isinstance(result, str)

    def test_persist_result_callable(self):
        from governance.routes.tests.runner_store import _persist_result
        assert callable(_persist_result)

    def test_load_persisted_results_callable(self):
        from governance.routes.tests.runner_store import _load_persisted_results
        assert callable(_load_persisted_results)


# ── Heuristic checks CC defense ──────────────────────────────────────

class TestHeuristicChecksCCDefense:
    """Defense tests for CC heuristic check functions."""

    def test_check_cc_session_uuid_callable(self):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_uuid
        assert callable(check_cc_session_uuid)

    def test_check_cc_session_project_link_callable(self):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_project_link
        assert callable(check_cc_session_project_link)

    def test_check_project_has_content_callable(self):
        from governance.routes.tests.heuristic_checks_cc import check_project_has_content
        assert callable(check_project_has_content)

    def test_check_cc_ingestion_complete_callable(self):
        from governance.routes.tests.heuristic_checks_cc import check_cc_ingestion_complete
        assert callable(check_cc_ingestion_complete)

    def test_cc_project_checks_registry_has_4_items(self):
        from governance.routes.tests.heuristic_checks_cc import CC_PROJECT_CHECKS
        assert len(CC_PROJECT_CHECKS) == 4

    def test_all_checks_return_skip_on_no_sessions(self):
        """All checks should return SKIP when no sessions exist."""
        from governance.routes.tests.heuristic_checks_cc import (
            check_cc_session_uuid,
            check_cc_session_project_link,
            check_cc_ingestion_complete,
        )
        with patch(
            "governance.routes.tests.heuristic_checks_cc._api_get", return_value=[]
        ):
            for fn in [check_cc_session_uuid, check_cc_session_project_link, check_cc_ingestion_complete]:
                result = fn("http://fake:8082")
                assert result["status"] == "SKIP", f"{fn.__name__} should SKIP on empty sessions"


# ── Runner exec defense ──────────────────────────────────────────────

class TestRunnerExecDefense:
    """Defense tests for runner_exec module."""

    def test_execute_tests_callable(self):
        from governance.routes.tests.runner_exec import execute_tests
        assert callable(execute_tests)

    def test_execute_regression_callable(self):
        from governance.routes.tests.runner_exec import execute_regression
        assert callable(execute_regression)

    def test_execute_heuristic_callable(self):
        from governance.routes.tests.runner_exec import execute_heuristic
        assert callable(execute_heuristic)

    def test_remediate_violations_callable(self):
        from governance.routes.tests.runner_exec import remediate_violations
        assert callable(remediate_violations)

    def test_remediate_returns_error_for_missing_run(self):
        from governance.routes.tests.runner_exec import remediate_violations
        result = remediate_violations("NONEXISTENT-RUN-123")
        assert "error" in result
