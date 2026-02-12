"""
Unit tests for Cross-Entity, API, and UI Heuristic Checks.

Per DOC-SIZE-01-v1: Tests for routes/tests/heuristic_checks_cross.py module.
Tests: _is_self_referential, _api_get, check_service_layer_coverage,
       check_api_endpoint_health, check_pagination_contract,
       check_decisions_link_rules, check_rule_document_paths,
       check_testid_coverage, CROSS_API_UI_CHECKS.
"""

from unittest.mock import patch, MagicMock

import pytest

_P = "governance.routes.tests.heuristic_checks_cross"


# ── _is_self_referential ────────────────────────────────────────


class TestIsSelfReferential:
    def test_localhost_default_port(self):
        from governance.routes.tests.heuristic_checks_cross import _is_self_referential
        with patch.dict("os.environ", {"API_PORT": "8082"}):
            assert _is_self_referential("http://localhost:8082") is True

    def test_127001_default_port(self):
        from governance.routes.tests.heuristic_checks_cross import _is_self_referential
        with patch.dict("os.environ", {"API_PORT": "8082"}):
            assert _is_self_referential("http://127.0.0.1:8082") is True

    def test_different_port(self):
        from governance.routes.tests.heuristic_checks_cross import _is_self_referential
        with patch.dict("os.environ", {"API_PORT": "8082"}):
            assert _is_self_referential("http://localhost:9000") is False

    def test_external_url(self):
        from governance.routes.tests.heuristic_checks_cross import _is_self_referential
        assert _is_self_referential("http://api.example.com:8082") is False

    def test_trailing_slash(self):
        from governance.routes.tests.heuristic_checks_cross import _is_self_referential
        with patch.dict("os.environ", {"API_PORT": "8082"}):
            assert _is_self_referential("http://localhost:8082/") is True


# ── _api_get ────────────────────────────────────────────────────


class TestApiGet:
    def test_success_with_items(self):
        from governance.routes.tests.heuristic_checks_cross import _api_get
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [{"id": 1}]}
        with patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = _api_get("http://api:8082", "/api/tasks")
        assert result == [{"id": 1}]

    def test_success_without_items(self):
        from governance.routes.tests.heuristic_checks_cross import _api_get
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1}]
        with patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = _api_get("http://api:8082", "/api/list")
        assert result == [{"id": 1}]

    def test_non_200_returns_empty(self):
        from governance.routes.tests.heuristic_checks_cross import _api_get
        resp = MagicMock()
        resp.status_code = 500
        with patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = _api_get("http://api:8082", "/api/fail")
        assert result == []

    def test_exception_returns_empty(self):
        from governance.routes.tests.heuristic_checks_cross import _api_get
        with patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.side_effect = Exception("timeout")
            result = _api_get("http://api:8082", "/api/fail")
        assert result == []


# ── check_service_layer_coverage ────────────────────────────────


class TestCheckServiceLayerCoverage:
    def test_skip_self_referential(self):
        from governance.routes.tests.heuristic_checks_cross import check_service_layer_coverage
        with patch(f"{_P}._is_self_referential", return_value=True):
            result = check_service_layer_coverage("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_pass(self):
        from governance.routes.tests.heuristic_checks_cross import check_service_layer_coverage
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value={"service_layer": {"tasks": "SERVICE_LAYER", "sessions": "SERVICE_LAYER"}}):
            result = check_service_layer_coverage("http://api:8082")
        assert result["status"] == "PASS"

    def test_fail(self):
        from governance.routes.tests.heuristic_checks_cross import check_service_layer_coverage
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value={"service_layer": {"tasks": "DIRECT", "sessions": "SERVICE_LAYER"}}):
            result = check_service_layer_coverage("http://api:8082")
        assert result["status"] == "FAIL"
        assert "tasks" in result["violations"]

    def test_skip_no_data(self):
        from governance.routes.tests.heuristic_checks_cross import check_service_layer_coverage
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value=[]):
            result = check_service_layer_coverage("http://api:8082")
        assert result["status"] == "SKIP"


# ── check_api_endpoint_health ───────────────────────────────────


class TestCheckApiEndpointHealth:
    def test_skip_self_referential(self):
        from governance.routes.tests.heuristic_checks_cross import check_api_endpoint_health
        with patch(f"{_P}._is_self_referential", return_value=True):
            result = check_api_endpoint_health("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_all_healthy(self):
        from governance.routes.tests.heuristic_checks_cross import check_api_endpoint_health
        resp = MagicMock()
        resp.status_code = 200
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = check_api_endpoint_health("http://api:8082")
        assert result["status"] == "PASS"

    def test_some_unhealthy(self):
        from governance.routes.tests.heuristic_checks_cross import check_api_endpoint_health
        resp = MagicMock()
        resp.status_code = 500
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = check_api_endpoint_health("http://api:8082")
        assert result["status"] == "FAIL"
        assert len(result["violations"]) > 0


# ── check_pagination_contract ───────────────────────────────────


class TestCheckPaginationContract:
    def test_skip_self_referential(self):
        from governance.routes.tests.heuristic_checks_cross import check_pagination_contract
        with patch(f"{_P}._is_self_referential", return_value=True):
            result = check_pagination_contract("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_pass(self):
        from governance.routes.tests.heuristic_checks_cross import check_pagination_contract
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "items": [],
            "pagination": {"total": 0, "offset": 0, "limit": 1, "has_more": False, "returned": 0},
        }
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = check_pagination_contract("http://api:8082")
        assert result["status"] == "PASS"

    def test_missing_pagination(self):
        from governance.routes.tests.heuristic_checks_cross import check_pagination_contract
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": []}
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}.httpx") as mock_httpx:
            mock_httpx.get.return_value = resp
            result = check_pagination_contract("http://api:8082")
        assert result["status"] == "FAIL"


# ── check_decisions_link_rules ──────────────────────────────────


class TestCheckDecisionsLinkRules:
    def test_skip_self_referential(self):
        from governance.routes.tests.heuristic_checks_cross import check_decisions_link_rules
        with patch(f"{_P}._is_self_referential", return_value=True):
            result = check_decisions_link_rules("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_pass(self):
        from governance.routes.tests.heuristic_checks_cross import check_decisions_link_rules
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value=[
                 {"id": "D-1", "rules_applied": ["RULE-1"]},
             ]):
            result = check_decisions_link_rules("http://api:8082")
        assert result["status"] == "PASS"

    def test_fail(self):
        from governance.routes.tests.heuristic_checks_cross import check_decisions_link_rules
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value=[
                 {"id": "D-1", "rules_applied": []},
             ]):
            result = check_decisions_link_rules("http://api:8082")
        assert result["status"] == "FAIL"


# ── check_rule_document_paths ───────────────────────────────────


class TestCheckRuleDocumentPaths:
    def test_skip_self_referential(self):
        from governance.routes.tests.heuristic_checks_cross import check_rule_document_paths
        with patch(f"{_P}._is_self_referential", return_value=True):
            result = check_rule_document_paths("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_pass(self):
        from governance.routes.tests.heuristic_checks_cross import check_rule_document_paths
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value=[
                 {"rule_id": "R-1", "status": "ACTIVE", "document_path": "/docs/r1.md"},
             ]):
            result = check_rule_document_paths("http://api:8082")
        assert result["status"] == "PASS"

    def test_fail_missing_path(self):
        from governance.routes.tests.heuristic_checks_cross import check_rule_document_paths
        with patch(f"{_P}._is_self_referential", return_value=False), \
             patch(f"{_P}._api_get", return_value=[
                 {"rule_id": "R-1", "status": "ACTIVE", "document_path": None},
             ]):
            result = check_rule_document_paths("http://api:8082")
        assert result["status"] == "FAIL"
        assert "R-1" in result["violations"]


# ── check_testid_coverage ───────────────────────────────────────


class TestCheckTestidCoverage:
    def test_pass_with_testids(self, tmp_path):
        from governance.routes.tests.heuristic_checks_cross import check_testid_coverage
        view_file = tmp_path / "test_view.py"
        view_file.write_text('VCard(attrs={"data-testid": "card"})\n')
        with patch(f"{_P}.os.path.join", return_value=str(tmp_path)), \
             patch(f"{_P}.os.path.normpath", return_value=str(tmp_path)), \
             patch("glob.glob", return_value=[str(view_file)]):
            result = check_testid_coverage("http://api:8082")
        assert result["status"] == "PASS"

    def test_fail_missing_testids(self, tmp_path):
        from governance.routes.tests.heuristic_checks_cross import check_testid_coverage
        view_file = tmp_path / "test_view.py"
        view_file.write_text("VCard(title='Test')\n")
        with patch(f"{_P}.os.path.join", return_value=str(tmp_path)), \
             patch(f"{_P}.os.path.normpath", return_value=str(tmp_path)), \
             patch("glob.glob", return_value=[str(view_file)]):
            result = check_testid_coverage("http://api:8082")
        assert result["status"] == "FAIL"


# ── CROSS_API_UI_CHECKS registry ────────────────────────────────


class TestRegistry:
    def test_has_all_checks(self):
        from governance.routes.tests.heuristic_checks_cross import CROSS_API_UI_CHECKS
        assert len(CROSS_API_UI_CHECKS) == 6
        ids = [c["id"] for c in CROSS_API_UI_CHECKS]
        assert "H-CROSS-001" in ids
        assert "H-API-001" in ids
        assert "H-UI-003" in ids

    def test_all_have_check_fn(self):
        from governance.routes.tests.heuristic_checks_cross import CROSS_API_UI_CHECKS
        for check in CROSS_API_UI_CHECKS:
            assert callable(check["check_fn"])
