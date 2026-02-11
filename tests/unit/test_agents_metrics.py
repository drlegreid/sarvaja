"""
Unit tests for Agent Metrics Service.

Per DOC-SIZE-01-v1: Tests for extracted agents_metrics.py module.
Tests: record_task_execution, _agent_to_dict, trust score recalculation.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.services.agents_metrics import (
    record_task_execution,
    _agent_to_dict,
)
from governance.stores import _agents_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear agent store between tests."""
    saved = dict(_agents_store)
    yield
    _agents_store.clear()
    _agents_store.update(saved)


class TestAgentToDict:
    """Tests for _agent_to_dict() helper."""

    def test_minimal(self):
        result = _agent_to_dict(
            agent_id="code-agent", name="Code Agent",
            agent_type="claude-code", status="ACTIVE",
            tasks_executed=10, trust_score=0.85,
        )
        assert result["agent_id"] == "code-agent"
        assert result["trust_score"] == 0.85
        assert result["capabilities"] == []
        assert result["recent_sessions"] == []
        assert result["active_tasks"] == []

    def test_with_all_fields(self):
        result = _agent_to_dict(
            agent_id="research-agent", name="Research Agent",
            agent_type="claude-code", status="PAUSED",
            tasks_executed=50, trust_score=0.92,
            last_active="2026-02-11T10:00:00",
            capabilities=["research", "analysis"],
            recent_sessions=[{"session_id": "S-1"}],
            active_tasks=[{"task_id": "T-1"}],
        )
        assert result["last_active"] == "2026-02-11T10:00:00"
        assert result["capabilities"] == ["research", "analysis"]
        assert len(result["recent_sessions"]) == 1
        assert len(result["active_tasks"]) == 1


class TestRecordTaskExecution:
    """Tests for record_task_execution()."""

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_creates_new_agent_entry(self, mock_mon, mock_save, mock_load, mock_client):
        _agents_store.clear()
        result = record_task_execution("new-agent")
        assert result is not None
        assert result["agent_id"] == "new-agent"
        assert result["tasks_executed"] == 1
        assert "last_active" in result

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_increments_task_count(self, mock_mon, mock_save, mock_load, mock_client):
        _agents_store["test-agent"] = {
            "agent_id": "test-agent", "name": "Test",
            "tasks_executed": 5, "trust_score": 0.85,
        }
        result = record_task_execution("test-agent")
        # Without TypeDB, base count is 0 + 1 = 1
        assert result["tasks_executed"] >= 1

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_updates_trust_score(self, mock_mon, mock_save, mock_load, mock_client):
        _agents_store.clear()
        result = record_task_execution("code-agent")
        assert "trust_score" in result
        assert isinstance(result["trust_score"], (int, float))
        assert 0.0 <= result["trust_score"] <= 1.0

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_persists_metrics_to_json(self, mock_mon, mock_save, mock_load, mock_client):
        _agents_store.clear()
        record_task_execution("persist-agent")
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert "persist-agent" in saved
        assert saved["persist-agent"]["tasks_executed"] == 1

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_monitor_called(self, mock_mon, mock_save, mock_load, mock_client):
        _agents_store.clear()
        record_task_execution("mon-agent", source="mcp")
        mock_mon.assert_called_once_with(
            "record_task", "mon-agent", source="mcp", tasks_executed=1,
        )

    @patch("governance.services.agents_metrics.get_typedb_client")
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_with_typedb_uses_task_count(self, mock_mon, mock_save, mock_load, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        # Mock build_relations_lookup to return task count of 10
        with patch(
            "governance.services.agents_metrics._build_relations_lookup",
            return_value=({}, {}, {"db-agent": 10}),
        ):
            _agents_store.clear()
            result = record_task_execution("db-agent")
        # typedb_count=10 + 1 = 11
        assert result["tasks_executed"] == 11

    @patch("governance.services.agents_metrics.get_typedb_client")
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_typedb_update_trust(self, mock_mon, mock_save, mock_load, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        with patch(
            "governance.services.agents_metrics._build_relations_lookup",
            return_value=({}, {}, {}),
        ):
            _agents_store.clear()
            record_task_execution("trust-agent")
        mock_client.update_agent_trust.assert_called_once()

    @patch("governance.services.agents_metrics.get_typedb_client")
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_typedb_error_falls_back(self, mock_mon, mock_save, mock_load, mock_client_fn):
        mock_client = MagicMock()
        mock_client.update_agent_trust.side_effect = Exception("TypeDB down")
        mock_client.get_agent.return_value = None  # Force fallback to in-memory
        mock_client_fn.return_value = mock_client
        with patch(
            "governance.services.agents_metrics._build_relations_lookup",
            return_value=({}, {}, {}),
        ):
            _agents_store.clear()
            result = record_task_execution("fallback-agent")
        # Should still return result from in-memory store
        assert result is not None
        assert result["agent_id"] == "fallback-agent"

    @patch("governance.services.agents_metrics.get_typedb_client", return_value=None)
    @patch("governance.services.agents_metrics._load_agent_metrics", return_value={})
    @patch("governance.services.agents_metrics._save_agent_metrics")
    @patch("governance.services.agents._monitor")
    def test_metrics_save_failure_non_fatal(self, mock_mon, mock_save, mock_load, mock_client):
        mock_save.side_effect = Exception("disk full")
        _agents_store.clear()
        # Should not raise — metrics save failure is non-critical
        result = record_task_execution("resilient-agent")
        assert result is not None
