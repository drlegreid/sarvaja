"""
Tests for heuristic data integrity test runner.

Per D.4: Heuristic-driven dynamic testing.
Verifies:
- Heuristic checks can be loaded per domain
- Checks return structured results
- API endpoint exists for running checks
- Results are formatted for UI display

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestHeuristicChecks:
    """Tests for heuristic check definitions."""

    def test_heuristic_checks_module_exists(self):
        """heuristic_checks module should be importable."""
        from governance.routes.tests import heuristic_checks
        assert hasattr(heuristic_checks, 'HEURISTIC_CHECKS')

    def test_checks_cover_all_domains(self):
        """Checks should cover TASK, SESSION, RULE, AGENT, API, CROSS-ENTITY, UI domains."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        domains = set(c['domain'] for c in HEURISTIC_CHECKS)
        assert 'TASK' in domains
        assert 'SESSION' in domains
        assert 'RULE' in domains
        assert 'AGENT' in domains
        assert 'API' in domains
        assert 'CROSS-ENTITY' in domains
        assert 'UI' in domains

    def test_checks_count_minimum(self):
        """Should have at least 14 heuristic checks across all domains."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        assert len(HEURISTIC_CHECKS) >= 14

    def test_each_check_has_required_fields(self):
        """Each check should have id, domain, name, check_fn."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        for check in HEURISTIC_CHECKS:
            assert 'id' in check, f"Check missing 'id': {check}"
            assert 'domain' in check, f"Check missing 'domain': {check}"
            assert 'name' in check, f"Check missing 'name': {check}"
            assert 'check_fn' in check, f"Check missing 'check_fn': {check}"
            assert callable(check['check_fn']), f"check_fn not callable: {check['id']}"


class TestHeuristicRunner:
    """Tests for heuristic runner execution."""

    def test_run_heuristic_checks_returns_results(self):
        """run_heuristic_checks should return structured results."""
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        results = run_heuristic_checks(api_base_url="http://localhost:8082")
        assert isinstance(results, dict)
        assert "checks" in results
        assert "summary" in results

    def test_results_have_status_per_check(self):
        """Each result should have status (PASS, FAIL, SKIP, ERROR)."""
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        results = run_heuristic_checks(api_base_url="http://localhost:8082")
        for check in results["checks"]:
            assert check["status"] in ("PASS", "FAIL", "SKIP", "ERROR")


class TestHeuristicEndpoint:
    """Tests for heuristic run API endpoint."""

    def test_endpoint_exists(self):
        """POST /api/tests/heuristic/run should exist."""
        from governance.routes.tests.runner import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)
        response = client.post("/api/tests/heuristic/run")
        assert response.status_code in (200, 201, 422)
