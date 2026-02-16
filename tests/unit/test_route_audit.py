"""
Unit tests for Audit Trail Routes.

Per DOC-SIZE-01-v1: Tests for routes/audit.py module.
Tests: list_audit_entries, audit_summary, get_entity_audit_trail endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.audit import router, AuditEntryResponse, AuditSummaryResponse


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TestModels:
    """Tests for response models."""

    def test_audit_entry_defaults(self):
        entry = AuditEntryResponse(
            audit_id="A-1", correlation_id="C-1", timestamp="2026-02-11",
            actor_id="agent-a", action_type="CREATE", entity_type="rule",
            entity_id="RULE-001",
        )
        assert entry.old_value is None
        assert entry.new_value is None
        assert entry.applied_rules == []
        assert entry.metadata == {}

    def test_audit_entry_all_fields(self):
        entry = AuditEntryResponse(
            audit_id="A-1", correlation_id="C-1", timestamp="t",
            actor_id="a", action_type="UPDATE", entity_type="task",
            entity_id="T-1", old_value="OPEN", new_value="DONE",
            applied_rules=["RULE-001"], metadata={"key": "val"},
        )
        assert entry.old_value == "OPEN"
        assert entry.new_value == "DONE"
        assert entry.applied_rules == ["RULE-001"]

    def test_audit_summary_model(self):
        summary = AuditSummaryResponse(
            total_entries=100,
            by_action_type={"CREATE": 50, "UPDATE": 50},
            by_entity_type={"rule": 60, "task": 40},
            by_actor={"agent-a": 100},
            retention_days=7,
        )
        assert summary.total_entries == 100
        assert summary.retention_days == 7


# ---------------------------------------------------------------------------
# list_audit_entries
# ---------------------------------------------------------------------------
class TestListAuditEntries:
    """Tests for GET /api/audit."""

    @patch("governance.routes.audit.query_audit_trail")
    def test_returns_entries(self, mock_query, client):
        mock_query.return_value = [{
            "audit_id": "A-1", "correlation_id": "C-1",
            "timestamp": "2026-02-11", "actor_id": "agent-a",
            "action_type": "CREATE", "entity_type": "rule",
            "entity_id": "RULE-001", "applied_rules": [],
            "metadata": {},
        }]
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["audit_id"] == "A-1"

    @patch("governance.routes.audit.query_audit_trail")
    def test_passes_filters(self, mock_query, client):
        mock_query.return_value = []
        client.get("/api/audit?entity_id=RULE-001&action_type=CREATE&limit=10")
        mock_query.assert_called_once_with(
            entity_id="RULE-001",
            entity_type=None,
            correlation_id=None,
            action_type="CREATE",
            actor_id=None,
            date_from=None,
            date_to=None,
            limit=10,
            offset=0,
        )

    @patch("governance.routes.audit.query_audit_trail")
    def test_empty_results(self, mock_query, client):
        mock_query.return_value = []
        response = client.get("/api/audit")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# audit_summary
# ---------------------------------------------------------------------------
class TestAuditSummary:
    """Tests for GET /api/audit/summary."""

    @patch("governance.routes.audit.get_audit_summary")
    def test_returns_summary(self, mock_summary, client):
        mock_summary.return_value = {
            "total_entries": 50,
            "by_action_type": {"CREATE": 30, "UPDATE": 20},
            "by_entity_type": {"rule": 50},
            "by_actor": {"agent-a": 50},
            "retention_days": 7,
        }
        response = client.get("/api/audit/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_entries"] == 50
        assert data["retention_days"] == 7


# ---------------------------------------------------------------------------
# get_entity_audit_trail
# ---------------------------------------------------------------------------
class TestGetEntityAuditTrail:
    """Tests for GET /api/audit/{entity_id}."""

    @patch("governance.routes.audit.query_audit_trail")
    def test_returns_entity_trail(self, mock_query, client):
        mock_query.return_value = [{
            "audit_id": "A-1", "correlation_id": "C-1",
            "timestamp": "t", "actor_id": "a",
            "action_type": "UPDATE", "entity_type": "task",
            "entity_id": "T-1", "applied_rules": [],
            "metadata": {},
        }]
        response = client.get("/api/audit/T-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_id"] == "T-1"

    @patch("governance.routes.audit.query_audit_trail")
    def test_passes_entity_id(self, mock_query, client):
        mock_query.return_value = []
        client.get("/api/audit/RULE-001?limit=5&offset=10")
        mock_query.assert_called_once_with(
            entity_id="RULE-001", limit=5, offset=10
        )
