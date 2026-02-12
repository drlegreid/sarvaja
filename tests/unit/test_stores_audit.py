"""
Unit tests for Governance Stores - Audit Trail.

Per DOC-SIZE-01-v1: Tests for stores/audit.py module.
Tests: AuditEntry, record_audit, query_audit_trail, get_audit_summary.
"""

import pytest
from unittest.mock import patch

import governance.stores.audit as _audit_mod
from governance.stores.audit import (
    AuditEntry,
    generate_correlation_id,
    record_audit,
    query_audit_trail,
    get_audit_summary,
)


@pytest.fixture(autouse=True)
def _clean_audit():
    """Clear audit store before/after each test.

    Access via module reference because _apply_retention() rebinds the
    global _audit_store list, which would break a direct import reference.
    """
    _audit_mod._audit_store = []
    yield
    _audit_mod._audit_store = []


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_basic(self):
        e = AuditEntry(
            audit_id="AUDIT-001", correlation_id="CORR-001",
            timestamp="2026-02-11T10:00:00", actor_id="code-agent",
            action_type="CREATE", entity_type="task", entity_id="T-1",
        )
        assert e.audit_id == "AUDIT-001"
        assert e.action_type == "CREATE"

    def test_defaults(self):
        e = AuditEntry(
            audit_id="A", correlation_id="C", timestamp="T",
            actor_id="a", action_type="X", entity_type="Y", entity_id="Z",
        )
        assert e.old_value is None
        assert e.new_value is None
        assert e.applied_rules == []
        assert e.metadata == {}

    def test_to_dict(self):
        e = AuditEntry(
            audit_id="A", correlation_id="C", timestamp="T",
            actor_id="a", action_type="CREATE", entity_type="task",
            entity_id="T-1", applied_rules=["RULE-001"],
        )
        d = e.to_dict()
        assert isinstance(d, dict)
        assert d["applied_rules"] == ["RULE-001"]


class TestGenerateCorrelationId:
    """Tests for generate_correlation_id()."""

    def test_format(self):
        cid = generate_correlation_id()
        assert cid.startswith("CORR-")
        assert len(cid) > 10

    def test_unique(self):
        ids = {generate_correlation_id() for _ in range(10)}
        assert len(ids) == 10


class TestRecordAudit:
    """Tests for record_audit()."""

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_basic(self, mock_retention, mock_save):
        entry = record_audit(
            action_type="CREATE", entity_type="task", entity_id="T-1",
        )
        assert entry.audit_id.startswith("AUDIT-")
        assert entry.action_type == "CREATE"
        assert entry.actor_id == "system"  # default
        assert len(_audit_mod._audit_store) == 1

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_with_all_params(self, mock_retention, mock_save):
        entry = record_audit(
            action_type="UPDATE", entity_type="task", entity_id="T-1",
            actor_id="code-agent", correlation_id="CORR-001",
            old_value="TODO", new_value="DONE",
            applied_rules=["RULE-001"],
            metadata={"reason": "completed"},
        )
        assert entry.actor_id == "code-agent"
        assert entry.old_value == "TODO"
        assert entry.new_value == "DONE"
        assert entry.applied_rules == ["RULE-001"]

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_auto_correlation_id(self, mock_retention, mock_save):
        entry = record_audit(
            action_type="CREATE", entity_type="task", entity_id="T-1",
        )
        assert entry.correlation_id.startswith("CORR-")


class TestQueryAuditTrail:
    """Tests for query_audit_trail()."""

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def _add_entries(self, mock_retention, mock_save):
        record_audit("CREATE", "task", "T-1", actor_id="code-agent")
        record_audit("UPDATE", "task", "T-1", actor_id="code-agent")
        record_audit("CREATE", "session", "S-1", actor_id="system")

    def test_no_filter(self):
        self._add_entries()
        results = query_audit_trail()
        assert len(results) == 3

    def test_filter_by_entity_id(self):
        self._add_entries()
        results = query_audit_trail(entity_id="T-1")
        assert len(results) == 2

    def test_filter_by_entity_type(self):
        self._add_entries()
        results = query_audit_trail(entity_type="session")
        assert len(results) == 1

    def test_filter_by_action_type(self):
        self._add_entries()
        results = query_audit_trail(action_type="CREATE")
        assert len(results) == 2

    def test_filter_by_actor(self):
        self._add_entries()
        results = query_audit_trail(actor_id="system")
        assert len(results) == 1

    def test_limit(self):
        self._add_entries()
        results = query_audit_trail(limit=2)
        assert len(results) == 2

    def test_offset(self):
        self._add_entries()
        results = query_audit_trail(offset=1, limit=10)
        assert len(results) == 2


class TestGetAuditSummary:
    """Tests for get_audit_summary()."""

    def test_empty(self):
        summary = get_audit_summary()
        assert summary["total_entries"] == 0
        assert summary["by_action_type"] == {}

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_with_data(self, mock_retention, mock_save):
        record_audit("CREATE", "task", "T-1")
        record_audit("UPDATE", "task", "T-1")
        summary = get_audit_summary()
        assert summary["total_entries"] == 2
        assert summary["by_action_type"]["CREATE"] == 1
        assert summary["by_action_type"]["UPDATE"] == 1
        assert summary["retention_days"] == 7


class TestApplyRetention:
    """Tests for _apply_retention()."""

    def test_keeps_recent(self):
        _audit_mod._audit_store.append({"timestamp": "2099-01-01T00:00:00"})
        _audit_mod._apply_retention(days=7)
        assert len(_audit_mod._audit_store) == 1

    def test_removes_old(self):
        _audit_mod._audit_store.append({"timestamp": "2020-01-01T00:00:00"})
        _audit_mod._apply_retention(days=7)
        assert len(_audit_mod._audit_store) == 0
