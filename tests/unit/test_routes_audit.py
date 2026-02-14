"""Tests for governance/routes/audit.py — Audit trail routes.

Covers: AuditEntryResponse, AuditSummaryResponse, list_audit_entries,
audit_summary, get_entity_audit_trail.
"""

import asyncio
import unittest
from unittest.mock import patch

from governance.routes.audit import (
    AuditEntryResponse,
    AuditSummaryResponse,
    list_audit_entries,
    audit_summary,
    get_entity_audit_trail,
)


class TestAuditModels(unittest.TestCase):
    """Tests for Pydantic response models."""

    def test_audit_entry_response(self):
        entry = AuditEntryResponse(
            audit_id="AUDIT-001",
            correlation_id="CORR-001",
            timestamp="2026-02-13T10:00:00",
            actor_id="system",
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-001",
        )
        self.assertEqual(entry.audit_id, "AUDIT-001")
        self.assertIsNone(entry.old_value)
        self.assertEqual(entry.applied_rules, [])
        self.assertEqual(entry.metadata, {})

    def test_audit_entry_full(self):
        entry = AuditEntryResponse(
            audit_id="AUDIT-002",
            correlation_id="CORR-002",
            timestamp="2026-02-13T10:00:00",
            actor_id="code-agent",
            action_type="UPDATE",
            entity_type="task",
            entity_id="TASK-002",
            old_value="OPEN",
            new_value="IN_PROGRESS",
            applied_rules=["RULE-001"],
            metadata={"source": "mcp"},
        )
        self.assertEqual(entry.old_value, "OPEN")
        self.assertEqual(entry.applied_rules, ["RULE-001"])

    def test_audit_summary_response(self):
        summary = AuditSummaryResponse(
            total_entries=10,
            by_action_type={"CREATE": 5, "UPDATE": 5},
            by_entity_type={"task": 8, "rule": 2},
            by_actor={"system": 10},
            retention_days=7,
        )
        self.assertEqual(summary.total_entries, 10)
        self.assertEqual(summary.retention_days, 7)


class TestListAuditEntries(unittest.TestCase):
    """Tests for list_audit_entries endpoint."""

    @patch("governance.routes.audit.query_audit_trail")
    def test_no_filters(self, mock_query):
        mock_query.return_value = [
            {"audit_id": "A-1", "entity_id": "T-1", "entity_type": "task",
             "action_type": "CREATE", "actor_id": "system",
             "correlation_id": "C-1", "timestamp": "2026-02-13T10:00:00"},
        ]
        result = asyncio.get_event_loop().run_until_complete(
            list_audit_entries()
        )
        self.assertEqual(len(result), 1)
        mock_query.assert_called_once()

    @patch("governance.routes.audit.query_audit_trail")
    def test_with_filters(self, mock_query):
        mock_query.return_value = []
        asyncio.get_event_loop().run_until_complete(
            list_audit_entries(
                entity_id="T-1",
                entity_type="task",
                action_type="UPDATE",
                actor_id="code-agent",
                limit=10,
                offset=5,
            )
        )
        mock_query.assert_called_once()


class TestAuditSummary(unittest.TestCase):
    """Tests for audit_summary endpoint."""

    @patch("governance.routes.audit.get_audit_summary")
    def test_returns_summary(self, mock_summary):
        mock_summary.return_value = {
            "total_entries": 100,
            "by_action_type": {"CREATE": 60, "UPDATE": 40},
            "by_entity_type": {"task": 80, "rule": 20},
            "by_actor": {"system": 100},
            "retention_days": 7,
        }
        result = asyncio.get_event_loop().run_until_complete(audit_summary())
        self.assertEqual(result["total_entries"], 100)


class TestGetEntityAuditTrail(unittest.TestCase):
    """Tests for get_entity_audit_trail endpoint."""

    @patch("governance.routes.audit.query_audit_trail")
    def test_entity_trail(self, mock_query):
        mock_query.return_value = [{"audit_id": "A-1", "entity_id": "TASK-X"}]
        result = asyncio.get_event_loop().run_until_complete(
            get_entity_audit_trail("TASK-X")
        )
        self.assertEqual(len(result), 1)
        mock_query.assert_called_once()
        # Verify entity_id was passed (Query wrappers for defaults)
        call_kwargs = mock_query.call_args[1]
        self.assertEqual(call_kwargs["entity_id"], "TASK-X")

    @patch("governance.routes.audit.query_audit_trail")
    def test_with_pagination(self, mock_query):
        mock_query.return_value = []
        asyncio.get_event_loop().run_until_complete(
            get_entity_audit_trail("R-1", limit=10, offset=20)
        )
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args[1]
        self.assertEqual(call_kwargs["entity_id"], "R-1")


if __name__ == "__main__":
    unittest.main()
