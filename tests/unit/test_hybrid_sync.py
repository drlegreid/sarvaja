"""
Unit tests for Hybrid Memory Sync Bridge.

Per DOC-SIZE-01-v1: Tests for hybrid/sync.py module.
Tests: MemorySyncBridge — sync_rules_to_chromadb, sync_decisions_to_chromadb,
       sync_agents_to_chromadb, sync_all, get_sync_status.
"""

from unittest.mock import MagicMock

import pytest

from governance.hybrid.models import SyncStatus
from governance.hybrid.sync import MemorySyncBridge


def _make_bridge(typedb_client=None, chromadb_client=None):
    router = MagicMock()
    router._typedb_client = typedb_client
    router._chromadb_client = chromadb_client
    return MemorySyncBridge(router)


def _make_rule(rule_id="RULE-001", name="Test", directive="Do X",
               category="GOV", priority="HIGH", status="ACTIVE"):
    r = MagicMock()
    r.id = rule_id
    r.name = name
    r.directive = directive
    r.category = category
    r.priority = priority
    r.status = status
    return r


class TestSyncRulesToChromadb:
    def test_no_typedb(self):
        bridge = _make_bridge(typedb_client=None)
        result = bridge.sync_rules_to_chromadb()
        assert isinstance(result, SyncStatus)
        assert result.synced_count == 0
        assert "TypeDB client not connected" in result.errors

    def test_no_chromadb(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = [_make_rule()]
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=None)
        result = bridge.sync_rules_to_chromadb()
        assert "ChromaDB client not connected" in result.errors

    def test_success(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = [_make_rule(), _make_rule(rule_id="RULE-002")]
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_rules_to_chromadb()
        assert result.synced_count == 2
        assert result.error_count == 0
        coll.upsert.assert_called_once()

    def test_empty_rules(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = []
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_rules_to_chromadb()
        assert result.synced_count == 0
        coll.upsert.assert_not_called()

    def test_get_rules_error(self):
        typedb = MagicMock()
        typedb.get_all_rules.side_effect = Exception("db error")
        bridge = _make_bridge(typedb_client=typedb)
        result = bridge.sync_rules_to_chromadb()
        assert result.error_count == 1
        assert "Failed to get rules" in result.errors[0]

    def test_upsert_error(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = [_make_rule()]
        chromadb = MagicMock()
        coll = MagicMock()
        coll.upsert.side_effect = Exception("upsert failed")
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_rules_to_chromadb()
        assert result.error_count == 1
        assert "Sync error" in result.errors[0]

    def test_custom_collection(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = [_make_rule()]
        chromadb = MagicMock()
        chromadb.get_or_create_collection.return_value = MagicMock()
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        bridge.sync_rules_to_chromadb(collection="custom_rules")
        chromadb.get_or_create_collection.assert_called_with("custom_rules")


class TestSyncDecisionsToChromadb:
    def test_no_typedb(self):
        bridge = _make_bridge(typedb_client=None)
        result = bridge.sync_decisions_to_chromadb()
        assert "TypeDB client not connected" in result.errors

    def test_no_chromadb(self):
        bridge = _make_bridge(typedb_client=MagicMock(), chromadb_client=None)
        result = bridge.sync_decisions_to_chromadb()
        assert "ChromaDB client not connected" in result.errors

    def test_success(self):
        typedb = MagicMock()
        typedb.execute_query.return_value = [
            {"title": "D1", "rationale": "R1", "id": "DEC-001", "status": "APPROVED"},
        ]
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_decisions_to_chromadb()
        assert result.synced_count == 1
        coll.upsert.assert_called_once()

    def test_none_results(self):
        typedb = MagicMock()
        typedb.execute_query.return_value = None
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_decisions_to_chromadb()
        assert result.synced_count == 0

    def test_non_dict_items_skipped(self):
        typedb = MagicMock()
        typedb.execute_query.return_value = ["not-a-dict", 42]
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_decisions_to_chromadb()
        assert result.synced_count == 0


class TestSyncAgentsToChromadb:
    def test_no_typedb(self):
        bridge = _make_bridge(typedb_client=None)
        result = bridge.sync_agents_to_chromadb()
        assert "TypeDB client not connected" in result.errors

    def test_success(self):
        typedb = MagicMock()
        typedb.execute_query.return_value = [
            {"name": "Agent-A", "agent_type": "coding", "id": "A-1", "trust_score": 0.9},
        ]
        chromadb = MagicMock()
        coll = MagicMock()
        chromadb.get_or_create_collection.return_value = coll
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_agents_to_chromadb()
        assert result.synced_count == 1

    def test_sync_error(self):
        typedb = MagicMock()
        typedb.execute_query.side_effect = Exception("query failed")
        chromadb = MagicMock()
        chromadb.get_or_create_collection.return_value = MagicMock()
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        result = bridge.sync_agents_to_chromadb()
        assert result.error_count == 1


class TestSyncAll:
    def test_returns_all_three(self):
        bridge = _make_bridge(typedb_client=None)
        result = bridge.sync_all()
        assert "rules" in result
        assert "decisions" in result
        assert "agents" in result
        assert all(isinstance(v, SyncStatus) for v in result.values())


class TestGetSyncStatus:
    def test_no_clients(self):
        bridge = _make_bridge(typedb_client=None, chromadb_client=None)
        status = bridge.get_sync_status()
        assert status["chromadb_connected"] is False
        assert status["typedb_connected"] is False
        assert status["collections"] == {}

    def test_with_chromadb(self):
        chromadb = MagicMock()
        coll = MagicMock()
        coll.count.return_value = 42
        chromadb.get_collection.return_value = coll
        typedb = MagicMock()
        typedb.is_connected.return_value = True
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        status = bridge.get_sync_status()
        assert status["chromadb_connected"] is True
        assert status["typedb_connected"] is True
        assert status["collections"]["sim_ai_rules"]["exists"] is True
        assert status["collections"]["sim_ai_rules"]["count"] == 42

    def test_collection_not_found(self):
        chromadb = MagicMock()
        chromadb.get_collection.side_effect = Exception("not found")
        bridge = _make_bridge(typedb_client=None, chromadb_client=chromadb)
        status = bridge.get_sync_status()
        for coll_name in ["sim_ai_rules", "sim_ai_decisions", "sim_ai_agents"]:
            assert status["collections"][coll_name]["exists"] is False

    def test_last_sync_tracked(self):
        typedb = MagicMock()
        typedb.get_all_rules.return_value = []
        chromadb = MagicMock()
        chromadb.get_or_create_collection.return_value = MagicMock()
        bridge = _make_bridge(typedb_client=typedb, chromadb_client=chromadb)
        bridge.sync_rules_to_chromadb()
        status = bridge.get_sync_status()
        assert "rules" in status["last_sync"]
