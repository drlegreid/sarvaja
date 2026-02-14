"""Tests for governance/stores/audit.py — Audit trail module.

Covers: AuditEntry dataclass, generate_correlation_id, record_audit,
_apply_retention, query_audit_trail, get_audit_summary, _load_audit_store.
"""

import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, MagicMock

from governance.stores.audit import (
    AuditEntry,
    generate_correlation_id,
    record_audit,
    _apply_retention,
    query_audit_trail,
    get_audit_summary,
    _load_audit_store,
    _save_audit_store,
    _audit_store,
)


class TestAuditEntry(unittest.TestCase):
    """Tests for AuditEntry dataclass."""

    def test_create_minimal(self):
        entry = AuditEntry(
            audit_id="AUDIT-ABC",
            correlation_id="CORR-123",
            timestamp="2026-02-13T10:00:00",
            actor_id="system",
            action_type="CREATE",
            entity_type="task",
            entity_id="TASK-001",
        )
        self.assertEqual(entry.audit_id, "AUDIT-ABC")
        self.assertEqual(entry.action_type, "CREATE")
        self.assertIsNone(entry.old_value)
        self.assertIsNone(entry.new_value)
        self.assertEqual(entry.applied_rules, [])
        self.assertEqual(entry.metadata, {})

    def test_create_full(self):
        entry = AuditEntry(
            audit_id="AUDIT-DEF",
            correlation_id="CORR-456",
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
        self.assertEqual(entry.new_value, "IN_PROGRESS")
        self.assertEqual(entry.applied_rules, ["RULE-001"])

    def test_to_dict(self):
        entry = AuditEntry(
            audit_id="AUDIT-X",
            correlation_id="CORR-X",
            timestamp="2026-01-01",
            actor_id="test",
            action_type="DELETE",
            entity_type="rule",
            entity_id="RULE-X",
        )
        d = entry.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["audit_id"], "AUDIT-X")
        self.assertEqual(d["entity_type"], "rule")
        self.assertIsNone(d["old_value"])


class TestGenerateCorrelationId(unittest.TestCase):
    """Tests for generate_correlation_id."""

    def test_format(self):
        cid = generate_correlation_id()
        self.assertTrue(cid.startswith("CORR-"))
        # CORR-YYYYMMDD-HHMMSS-XXXXXX
        parts = cid.split("-")
        self.assertGreaterEqual(len(parts), 3)

    def test_unique(self):
        ids = {generate_correlation_id() for _ in range(20)}
        self.assertEqual(len(ids), 20)


class TestRecordAudit(unittest.TestCase):
    """Tests for record_audit."""

    def setUp(self):
        import governance.stores.audit as mod
        self._orig = mod._audit_store[:]
        mod._audit_store.clear()

    def tearDown(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        mod._audit_store.extend(self._orig)

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_basic(self, mock_retention, mock_save):
        entry = record_audit("CREATE", "task", "TASK-100")
        self.assertIsInstance(entry, AuditEntry)
        self.assertEqual(entry.action_type, "CREATE")
        self.assertEqual(entry.entity_type, "task")
        self.assertEqual(entry.entity_id, "TASK-100")
        self.assertEqual(entry.actor_id, "system")
        mock_retention.assert_called_once()
        mock_save.assert_called_once()

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_with_actor(self, mock_retention, mock_save):
        entry = record_audit("UPDATE", "session", "S-1", actor_id="code-agent")
        self.assertEqual(entry.actor_id, "code-agent")

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_with_correlation_id(self, mock_retention, mock_save):
        entry = record_audit("DELETE", "rule", "R-1", correlation_id="CORR-CUSTOM")
        self.assertEqual(entry.correlation_id, "CORR-CUSTOM")

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_with_metadata(self, mock_retention, mock_save):
        entry = record_audit(
            "CLAIM", "task", "T-1",
            metadata={"source": "rest", "priority": "HIGH"},
        )
        self.assertEqual(entry.metadata["source"], "rest")

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_appends_to_store(self, mock_retention, mock_save):
        import governance.stores.audit as mod
        self.assertEqual(len(mod._audit_store), 0)
        record_audit("CREATE", "task", "T-1")
        record_audit("UPDATE", "task", "T-1")
        self.assertEqual(len(mod._audit_store), 2)

    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_record_auto_generates_correlation_id(self, mock_retention, mock_save):
        entry = record_audit("CREATE", "task", "T-1")
        self.assertTrue(entry.correlation_id.startswith("CORR-"))


class TestApplyRetention(unittest.TestCase):
    """Tests for _apply_retention."""

    def setUp(self):
        import governance.stores.audit as mod
        self._orig = mod._audit_store[:]
        mod._audit_store.clear()

    def tearDown(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        mod._audit_store.extend(self._orig)

    def test_removes_old_entries(self):
        import governance.stores.audit as mod
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        recent_date = datetime.now().isoformat()
        mod._audit_store.extend([
            {"timestamp": old_date, "entity_id": "old"},
            {"timestamp": recent_date, "entity_id": "new"},
        ])
        _apply_retention(days=7)
        self.assertEqual(len(mod._audit_store), 1)
        self.assertEqual(mod._audit_store[0]["entity_id"], "new")

    def test_keeps_all_recent(self):
        import governance.stores.audit as mod
        recent = datetime.now().isoformat()
        mod._audit_store.extend([
            {"timestamp": recent, "entity_id": "a"},
            {"timestamp": recent, "entity_id": "b"},
        ])
        _apply_retention(days=7)
        self.assertEqual(len(mod._audit_store), 2)

    def test_custom_retention_days(self):
        import governance.stores.audit as mod
        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
        mod._audit_store.append({"timestamp": three_days_ago, "entity_id": "x"})
        _apply_retention(days=2)
        self.assertEqual(len(mod._audit_store), 0)

    def test_empty_store(self):
        import governance.stores.audit as mod
        _apply_retention(days=7)
        self.assertEqual(len(mod._audit_store), 0)


class TestQueryAuditTrail(unittest.TestCase):
    """Tests for query_audit_trail."""

    def setUp(self):
        import governance.stores.audit as mod
        self._orig = mod._audit_store[:]
        mod._audit_store.clear()
        mod._audit_store.extend([
            {"entity_id": "T-1", "entity_type": "task", "action_type": "CREATE",
             "actor_id": "system", "correlation_id": "C-1", "timestamp": "2026-02-13T10:00:00"},
            {"entity_id": "T-1", "entity_type": "task", "action_type": "UPDATE",
             "actor_id": "code-agent", "correlation_id": "C-2", "timestamp": "2026-02-13T11:00:00"},
            {"entity_id": "R-1", "entity_type": "rule", "action_type": "CREATE",
             "actor_id": "system", "correlation_id": "C-3", "timestamp": "2026-02-13T09:00:00"},
        ])

    def tearDown(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        mod._audit_store.extend(self._orig)

    def test_no_filters(self):
        result = query_audit_trail()
        self.assertEqual(len(result), 3)
        # Most recent first
        self.assertEqual(result[0]["timestamp"], "2026-02-13T11:00:00")

    def test_filter_entity_id(self):
        result = query_audit_trail(entity_id="T-1")
        self.assertEqual(len(result), 2)

    def test_filter_entity_type(self):
        result = query_audit_trail(entity_type="rule")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["entity_id"], "R-1")

    def test_filter_action_type(self):
        result = query_audit_trail(action_type="UPDATE")
        self.assertEqual(len(result), 1)

    def test_filter_actor_id(self):
        result = query_audit_trail(actor_id="code-agent")
        self.assertEqual(len(result), 1)

    def test_filter_correlation_id(self):
        result = query_audit_trail(correlation_id="C-3")
        self.assertEqual(len(result), 1)

    def test_pagination_limit(self):
        result = query_audit_trail(limit=2)
        self.assertEqual(len(result), 2)

    def test_pagination_offset(self):
        result = query_audit_trail(offset=1, limit=10)
        self.assertEqual(len(result), 2)

    def test_combined_filters(self):
        result = query_audit_trail(entity_id="T-1", action_type="CREATE")
        self.assertEqual(len(result), 1)


class TestGetAuditSummary(unittest.TestCase):
    """Tests for get_audit_summary."""

    def setUp(self):
        import governance.stores.audit as mod
        self._orig = mod._audit_store[:]
        mod._audit_store.clear()
        mod._audit_store.extend([
            {"action_type": "CREATE", "entity_type": "task", "actor_id": "system"},
            {"action_type": "CREATE", "entity_type": "rule", "actor_id": "system"},
            {"action_type": "UPDATE", "entity_type": "task", "actor_id": "code-agent"},
        ])

    def tearDown(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        mod._audit_store.extend(self._orig)

    def test_summary_structure(self):
        summary = get_audit_summary()
        self.assertEqual(summary["total_entries"], 3)
        self.assertIn("by_action_type", summary)
        self.assertIn("by_entity_type", summary)
        self.assertIn("by_actor", summary)
        self.assertEqual(summary["retention_days"], 7)

    def test_summary_counts(self):
        summary = get_audit_summary()
        self.assertEqual(summary["by_action_type"]["CREATE"], 2)
        self.assertEqual(summary["by_action_type"]["UPDATE"], 1)
        self.assertEqual(summary["by_entity_type"]["task"], 2)
        self.assertEqual(summary["by_entity_type"]["rule"], 1)
        self.assertEqual(summary["by_actor"]["system"], 2)
        self.assertEqual(summary["by_actor"]["code-agent"], 1)

    def test_empty_summary(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        summary = get_audit_summary()
        self.assertEqual(summary["total_entries"], 0)
        self.assertEqual(summary["by_action_type"], {})


class TestLoadSaveAuditStore(unittest.TestCase):
    """Tests for _load_audit_store and _save_audit_store."""

    def setUp(self):
        import governance.stores.audit as mod
        self._orig = mod._audit_store[:]

    def tearDown(self):
        import governance.stores.audit as mod
        mod._audit_store.clear()
        mod._audit_store.extend(self._orig)

    @patch("governance.stores.audit.AUDIT_STORE_PATH")
    def test_load_existing_file(self, mock_path):
        import governance.stores.audit as mod
        mock_path.exists.return_value = True
        data = [{"entity_id": "loaded"}]
        m = mock_open(read_data=json.dumps(data))
        with patch("builtins.open", m):
            _load_audit_store()
        self.assertEqual(len(mod._audit_store), 1)
        self.assertEqual(mod._audit_store[0]["entity_id"], "loaded")

    @patch("governance.stores.audit.AUDIT_STORE_PATH")
    def test_load_missing_file(self, mock_path):
        import governance.stores.audit as mod
        mock_path.exists.return_value = False
        mod._audit_store.clear()
        mod._audit_store.append({"before": True})
        _load_audit_store()
        # Should not change store if file doesn't exist
        self.assertEqual(len(mod._audit_store), 1)

    @patch("governance.stores.audit.AUDIT_STORE_PATH")
    def test_load_corrupt_file(self, mock_path):
        import governance.stores.audit as mod
        mock_path.exists.return_value = True
        m = mock_open(read_data="NOT JSON")
        with patch("builtins.open", m):
            _load_audit_store()
        self.assertEqual(mod._audit_store, [])

    @patch("governance.stores.audit.AUDIT_STORE_PATH")
    def test_save_creates_dir(self, mock_path):
        mock_parent = MagicMock()
        mock_path.parent = mock_parent
        m = mock_open()
        with patch("builtins.open", m):
            _save_audit_store()
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


if __name__ == "__main__":
    unittest.main()
