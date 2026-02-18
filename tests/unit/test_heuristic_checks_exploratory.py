"""Tests for exploratory heuristic checks (H-EXPLR-001 through H-EXPLR-006)."""
import pytest
from unittest.mock import patch, MagicMock

from governance.routes.tests.heuristic_checks_exploratory import (
    check_chat_session_count_accuracy,
    check_monitor_event_count_consistency,
    check_decision_rule_linking,
    check_audit_trail_populated,
    check_rule_document_paths_populated,
    check_mcp_readiness_consistency,
    EXPLORATORY_CHECKS,
)


@pytest.fixture
def mock_api():
    """Helper to mock httpx.get responses."""
    def _mock(responses: dict):
        def side_effect(url, **kwargs):
            m = MagicMock()
            for pattern, (status, body) in responses.items():
                if pattern in url:
                    m.status_code = status
                    m.json.return_value = body
                    return m
            m.status_code = 404
            m.json.return_value = {"detail": "Not Found"}
            return m
        return side_effect
    return _mock


class TestRegistryIntegrity:
    def test_exploratory_checks_count(self):
        assert len(EXPLORATORY_CHECKS) == 6

    def test_all_checks_have_required_fields(self):
        for check in EXPLORATORY_CHECKS:
            assert "id" in check
            assert "domain" in check
            assert "name" in check
            assert "check_fn" in check
            assert callable(check["check_fn"])

    def test_all_check_ids_unique(self):
        ids = [c["id"] for c in EXPLORATORY_CHECKS]
        assert len(ids) == len(set(ids))

    def test_all_ids_start_with_h_explr(self):
        for check in EXPLORATORY_CHECKS:
            assert check["id"].startswith("H-EXPLR-")


class TestDecisionRuleLinking:
    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_all_linked_passes(self, mock_api_get, mock_get):
        mock_api_get.return_value = [
            {"id": "D-001", "linked_rules": ["RULE-001"]},
            {"id": "D-002", "linked_rules": ["RULE-002"]},
        ]
        result = check_decision_rule_linking("http://external:9999")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_unlinked_fails(self, mock_api_get, mock_get):
        mock_api_get.return_value = [
            {"id": "D-001", "linked_rules": []},
            {"id": "D-002", "linked_rules": ["RULE-001"]},
        ]
        result = check_decision_rule_linking("http://external:9999")
        assert result["status"] == "FAIL"
        assert "D-001" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_no_decisions_skips(self, mock_api_get):
        mock_api_get.return_value = []
        result = check_decision_rule_linking("http://external:9999")
        assert result["status"] == "SKIP"

    def test_self_referential_skips(self):
        result = check_decision_rule_linking("http://localhost:8082")
        assert result["status"] == "SKIP"


class TestAuditTrailPopulated:
    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    def test_populated_passes(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "items": [{"id": "1"}],
                "pagination": {"total": 5}
            })
        )
        result = check_audit_trail_populated("http://external:9999")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    def test_empty_fails(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "items": [],
                "pagination": {"total": 0}
            })
        )
        result = check_audit_trail_populated("http://external:9999")
        assert result["status"] == "FAIL"
        assert "AUDIT_EMPTY" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    def test_404_fails(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)
        result = check_audit_trail_populated("http://external:9999")
        assert result["status"] == "FAIL"
        assert "NO_ENDPOINT" in result["violations"]

    def test_self_referential_skips(self):
        result = check_audit_trail_populated("http://localhost:8082")
        assert result["status"] == "SKIP"


class TestRuleDocumentPaths:
    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_all_have_paths_passes(self, mock_api_get):
        mock_api_get.return_value = [
            {"rule_id": "R-001", "status": "ACTIVE", "document_path": "/docs/r1.md"},
            {"rule_id": "R-002", "status": "ACTIVE", "document_path": "/docs/r2.md"},
        ]
        result = check_rule_document_paths_populated("http://external:9999")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_majority_missing_fails(self, mock_api_get):
        mock_api_get.return_value = [
            {"rule_id": "R-001", "status": "ACTIVE", "document_path": None},
            {"rule_id": "R-002", "status": "ACTIVE", "document_path": None},
            {"rule_id": "R-003", "status": "ACTIVE", "document_path": "/docs/r3.md"},
        ]
        result = check_rule_document_paths_populated("http://external:9999")
        assert result["status"] == "FAIL"
        assert "R-001" in result["violations"]
        assert "R-002" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_exploratory._api_get")
    def test_no_active_rules_skips(self, mock_api_get):
        mock_api_get.return_value = [
            {"rule_id": "R-001", "status": "DRAFT"},
        ]
        result = check_rule_document_paths_populated("http://external:9999")
        assert result["status"] == "SKIP"


class TestMcpReadinessConsistency:
    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    def test_consistent_passes(self, mock_get):
        def side_effect(url, **kwargs):
            m = MagicMock()
            if "health" in url and "mcp" not in url:
                m.status_code = 200
                m.json.return_value = {"typedb_connected": True}
            elif "readiness" in url:
                m.status_code = 200
                m.json.return_value = {"backends": {"typedb": True}}
            return m
        mock_get.side_effect = side_effect
        result = check_mcp_readiness_consistency("http://external:9999")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx.get")
    def test_mismatch_fails(self, mock_get):
        def side_effect(url, **kwargs):
            m = MagicMock()
            if "health" in url and "mcp" not in url:
                m.status_code = 200
                m.json.return_value = {"typedb_connected": True}
            elif "readiness" in url:
                m.status_code = 200
                m.json.return_value = {"backends": {"typedb": False}}
            return m
        mock_get.side_effect = side_effect
        result = check_mcp_readiness_consistency("http://external:9999")
        assert result["status"] == "FAIL"
        assert any("typedb" in v for v in result["violations"])

    def test_self_referential_skips(self):
        result = check_mcp_readiness_consistency("http://localhost:8082")
        assert result["status"] == "SKIP"
