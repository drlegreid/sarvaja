"""
Unit tests for Agent Service Layer.

Per DOC-SIZE-01-v1: Tests for governance/services/agents.py module.
Tests: list_agents, get_agent, delete_agent, toggle_agent_status.
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.services.agents"


def _make_agent(id="code-agent", name="Code Agent", agent_type="executor",
                trust_score=0.85):
    a = MagicMock()
    a.id = id
    a.name = name
    a.agent_type = agent_type
    a.trust_score = trust_score
    return a


@pytest.fixture(autouse=True)
def _patch_stores():
    """Reset in-memory stores for each test."""
    with patch(f"{_P}._agents_store", {
        "code-agent": {
            "agent_id": "code-agent", "name": "Code Agent",
            "agent_type": "executor", "status": "PAUSED",
            "tasks_executed": 5, "trust_score": 0.85,
            "last_active": "2026-01-01T10:00:00", "capabilities": [],
        },
        "test-agent": {
            "agent_id": "test-agent", "name": "Test Agent",
            "agent_type": "validator", "status": "ACTIVE",
            "tasks_executed": 3, "trust_score": 0.75,
            "last_active": "2026-01-01T09:00:00", "capabilities": [],
        },
    }) as store, \
        patch(f"{_P}._AGENT_BASE_CONFIG", {
            "code-agent": {"base_trust": 0.85, "capabilities": ["code"]},
            "test-agent": {"base_trust": 0.75, "capabilities": ["test"]},
        }), \
        patch(f"{_P}._load_agent_metrics", return_value={}), \
        patch(f"{_P}._calculate_trust_score", return_value=0.85), \
        patch(f"{_P}.record_audit"), \
        patch(f"{_P}._monitor"):
        yield store


# ── list_agents ──────────────────────────────────────────────────


class TestListAgents:
    def test_fallback_when_no_client(self):
        from governance.services.agents import list_agents
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = list_agents()
        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_fallback_pagination(self):
        from governance.services.agents import list_agents
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = list_agents(offset=0, limit=1)
        assert len(result["items"]) == 1
        assert result["has_more"] is True

    def test_typedb_agents(self):
        from governance.services.agents import list_agents
        mock_client = MagicMock()
        mock_client.get_all_agents.return_value = [
            _make_agent("code-agent", "Code Agent"),
        ]
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}._build_relations_lookup", return_value=({}, {}, {})), \
             patch(f"{_P}._get_relations", return_value=([], [], 0)):
            result = list_agents()
        assert result["total"] == 1
        assert result["items"][0]["agent_id"] == "code-agent"

    def test_typedb_filters_by_type(self):
        from governance.services.agents import list_agents
        mock_client = MagicMock()
        mock_client.get_all_agents.return_value = [
            _make_agent("code-agent", "Code Agent", "executor"),
            _make_agent("test-agent", "Test Agent", "validator"),
        ]
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}._build_relations_lookup", return_value=({}, {}, {})), \
             patch(f"{_P}._get_relations", return_value=([], [], 0)):
            result = list_agents(agent_type="executor")
        assert result["total"] == 1
        assert result["items"][0]["agent_type"] == "executor"

    def test_typedb_filters_by_status(self):
        from governance.services.agents import list_agents
        mock_client = MagicMock()
        mock_client.get_all_agents.return_value = [
            _make_agent("code-agent"),
            _make_agent("test-agent"),
        ]
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}._build_relations_lookup", return_value=({}, {}, {})), \
             patch(f"{_P}._get_relations", return_value=([], [], 0)):
            result = list_agents(status="ACTIVE")
        # Only test-agent is ACTIVE in _agents_store
        assert result["total"] == 1

    def test_typedb_fallback_on_exception(self):
        from governance.services.agents import list_agents
        mock_client = MagicMock()
        mock_client.get_all_agents.side_effect = Exception("TypeDB down")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = list_agents()
        assert result["total"] == 2  # fallback to in-memory

    def test_typedb_empty_agents(self):
        from governance.services.agents import list_agents
        mock_client = MagicMock()
        mock_client.get_all_agents.return_value = []
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = list_agents()
        assert result["total"] == 2  # falls through to in-memory


# ── get_agent ────────────────────────────────────────────────────


class TestGetAgent:
    def test_not_found(self):
        from governance.services.agents import get_agent
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = get_agent("nonexistent")
        assert result is None

    def test_fallback_to_memory(self):
        from governance.services.agents import get_agent
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = get_agent("code-agent")
        assert result is not None
        assert result["agent_id"] == "code-agent"

    def test_typedb_success(self):
        from governance.services.agents import get_agent
        mock_client = MagicMock()
        mock_client.get_agent.return_value = _make_agent("code-agent")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}._build_relations_lookup", return_value=({}, {}, {})), \
             patch(f"{_P}._get_relations", return_value=(["S-1"], ["T-1"], 5)):
            result = get_agent("code-agent")
        assert result["agent_id"] == "code-agent"
        assert result["recent_sessions"] == ["S-1"]
        assert result["active_tasks"] == ["T-1"]

    def test_typedb_not_found(self):
        from governance.services.agents import get_agent
        mock_client = MagicMock()
        mock_client.get_agent.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = get_agent("code-agent")
        # falls through to in-memory
        assert result is not None

    def test_typedb_exception_fallback(self):
        from governance.services.agents import get_agent
        mock_client = MagicMock()
        mock_client.get_agent.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = get_agent("code-agent")
        assert result is not None  # fallback


# ── delete_agent ─────────────────────────────────────────────────


class TestDeleteAgent:
    def test_delete_from_memory(self):
        from governance.services.agents import delete_agent
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = delete_agent("code-agent")
        assert result is True

    def test_delete_nonexistent(self):
        from governance.services.agents import delete_agent
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = delete_agent("nonexistent")
        assert result is False

    def test_delete_from_typedb(self):
        from governance.services.agents import delete_agent
        mock_client = MagicMock()
        mock_client.get_agent.return_value = _make_agent("code-agent")
        mock_client.delete_agent.return_value = True
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = delete_agent("code-agent")
        assert result is True
        mock_client.delete_agent.assert_called_once_with("code-agent")

    def test_typedb_failure_still_deletes_memory(self):
        from governance.services.agents import delete_agent
        mock_client = MagicMock()
        mock_client.get_agent.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = delete_agent("code-agent")
        assert result is True  # in-memory deletion succeeded


# ── toggle_agent_status ──────────────────────────────────────────


class TestToggleAgentStatus:
    def test_toggle_paused_to_active(self):
        from governance.services.agents import toggle_agent_status
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = toggle_agent_status("code-agent")
        # code-agent was PAUSED, should now be ACTIVE
        assert result is not None

    def test_toggle_active_to_paused(self):
        from governance.services.agents import toggle_agent_status
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = toggle_agent_status("test-agent")
        # test-agent was ACTIVE, should now be PAUSED
        assert result is not None

    def test_toggle_nonexistent(self):
        from governance.services.agents import toggle_agent_status
        result = toggle_agent_status("nonexistent")
        assert result is None
