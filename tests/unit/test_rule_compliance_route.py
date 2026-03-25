"""
Tests for Rule Compliance Route (GET /api/rules/enforcement/summary).

Per EPIC-GOV-RULES-V3 P4: TDD RED phase.

Created: 2026-03-25
"""

import pytest
from unittest.mock import patch, MagicMock


def _make_rule(rule_id="TEST-RULE-01", applicability="MANDATORY",
               status="ACTIVE", **kwargs):
    return {
        "id": rule_id,
        "semantic_id": rule_id,
        "name": f"Test Rule {rule_id}",
        "applicability": applicability,
        "status": status,
        **kwargs,
    }


class TestEnforcementSummaryRoute:
    """Tests for GET /api/rules/enforcement/summary."""

    @patch("governance.routes.rules.compliance.ComplianceChecker")
    def test_enforcement_summary_returns_200(self, mock_checker_cls):
        from fastapi.testclient import TestClient
        from governance.routes.rules.compliance import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_instance = MagicMock()
        mock_instance.get_enforcement_summary.return_value = {
            "mandatory": 5,
            "recommended": 10,
            "forbidden": 2,
            "conditional": 3,
            "unspecified": 1,
            "total": 21,
            "unimplemented_mandatory": [],
        }
        mock_checker_cls.return_value = mock_instance

        client = TestClient(app)
        response = client.get("/api/rules/enforcement/summary")
        assert response.status_code == 200

    @patch("governance.routes.rules.compliance.ComplianceChecker")
    def test_enforcement_summary_returns_counts_by_level(self, mock_checker_cls):
        from fastapi.testclient import TestClient
        from governance.routes.rules.compliance import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_instance = MagicMock()
        mock_instance.get_enforcement_summary.return_value = {
            "mandatory": 5,
            "recommended": 10,
            "forbidden": 2,
            "conditional": 3,
            "unspecified": 1,
            "total": 21,
            "unimplemented_mandatory": [],
        }
        mock_checker_cls.return_value = mock_instance

        client = TestClient(app)
        response = client.get("/api/rules/enforcement/summary")
        data = response.json()
        assert "mandatory" in data
        assert "recommended" in data
        assert "forbidden" in data
        assert "conditional" in data
        assert "total" in data
        assert data["mandatory"] == 5
        assert data["recommended"] == 10

    @patch("governance.routes.rules.compliance.ComplianceChecker")
    def test_enforcement_summary_lists_unimplemented_mandatory(self, mock_checker_cls):
        from fastapi.testclient import TestClient
        from governance.routes.rules.compliance import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_instance = MagicMock()
        mock_instance.get_enforcement_summary.return_value = {
            "mandatory": 2,
            "recommended": 0,
            "forbidden": 0,
            "conditional": 0,
            "unspecified": 0,
            "total": 2,
            "unimplemented_mandatory": [
                {"rule_id": "DOC-SIZE-01-v1", "name": "File Size Limit"},
                {"rule_id": "TEST-GUARD-01-v1", "name": "Test Guard"},
            ],
        }
        mock_checker_cls.return_value = mock_instance

        client = TestClient(app)
        response = client.get("/api/rules/enforcement/summary")
        data = response.json()
        assert "unimplemented_mandatory" in data
        assert len(data["unimplemented_mandatory"]) == 2
        ids = [r["rule_id"] for r in data["unimplemented_mandatory"]]
        assert "DOC-SIZE-01-v1" in ids

    @patch("governance.routes.rules.compliance.ComplianceChecker")
    def test_enforcement_summary_handles_api_error(self, mock_checker_cls):
        from fastapi.testclient import TestClient
        from governance.routes.rules.compliance import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_instance = MagicMock()
        mock_instance.get_enforcement_summary.side_effect = ConnectionError("TypeDB down")
        mock_checker_cls.return_value = mock_instance

        client = TestClient(app)
        response = client.get("/api/rules/enforcement/summary")
        assert response.status_code == 503

    @patch("governance.routes.rules.compliance.ComplianceChecker")
    def test_enforcement_summary_handles_unexpected_error(self, mock_checker_cls):
        from fastapi.testclient import TestClient
        from governance.routes.rules.compliance import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_instance = MagicMock()
        mock_instance.get_enforcement_summary.side_effect = RuntimeError("Unexpected")
        mock_checker_cls.return_value = mock_instance

        client = TestClient(app)
        response = client.get("/api/rules/enforcement/summary")
        assert response.status_code == 500
