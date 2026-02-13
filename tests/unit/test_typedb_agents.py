"""
Unit tests for TypeDB Agent Queries.

Batch 155: Tests for governance/typedb/queries/agents.py
- AgentQueries mixin: get_all_agents, get_agent, insert_agent, delete_agent, update_agent_trust
"""

from unittest.mock import MagicMock, patch

import pytest

from governance.typedb.queries.agents import AgentQueries
from governance.typedb.entities import Agent


class _TestableAgentQueries(AgentQueries):
    """Concrete class for testing the AgentQueries mixin."""
    def __init__(self):
        self._execute_query = MagicMock()
        self._execute_write = MagicMock()
        self.database = "test-db"


# ── get_all_agents ───────────────────────────────────────

class TestGetAllAgents:
    def test_returns_agents(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"id": "agent-1", "name": "Code Agent", "type": "code", "trust": 0.9},
        ]
        result = q.get_all_agents()
        assert len(result) == 1
        assert result[0].id == "agent-1"
        assert result[0].name == "Code Agent"
        assert result[0].trust_score == 0.9

    def test_empty_results(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []
        assert q.get_all_agents() == []

    def test_default_trust_score(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"id": "a1", "name": "N", "type": "T"},  # no trust key
        ]
        result = q.get_all_agents()
        assert result[0].trust_score == 0.8

    def test_multiple_agents(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"id": "a1", "name": "A", "type": "t", "trust": 0.7},
            {"id": "a2", "name": "B", "type": "t", "trust": 0.5},
        ]
        result = q.get_all_agents()
        assert len(result) == 2


# ── get_agent ────────────────────────────────────────────

class TestGetAgent:
    def test_found(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"name": "Test", "type": "code", "trust": 0.85},
        ]
        agent = q.get_agent("agent-1")
        assert agent is not None
        assert agent.id == "agent-1"
        assert agent.trust_score == 0.85

    def test_not_found(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []
        assert q.get_agent("nonexistent") is None


# ── insert_agent ─────────────────────────────────────────

class TestInsertAgent:
    def test_insert_new(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []  # get_agent returns None
        q._execute_write.return_value = None
        result = q.insert_agent("a1", "Agent 1", "code", 0.9)
        assert result is True
        q._execute_write.assert_called_once()

    def test_insert_replaces_existing(self):
        q = _TestableAgentQueries()
        # First call (get_agent in insert_agent) returns existing
        q._execute_query.return_value = [
            {"name": "Old", "type": "code", "trust": 0.5},
        ]
        q._execute_write.return_value = None
        result = q.insert_agent("a1", "Agent 1", "code", 0.9)
        assert result is True
        # Should call delete + insert
        assert q._execute_write.call_count >= 2

    def test_insert_failure(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []
        q._execute_write.side_effect = Exception("write error")
        result = q.insert_agent("a1", "Agent", "code")
        assert result is False

    def test_escapes_quotes(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []
        q._execute_write.return_value = None
        q.insert_agent("a1", 'Agent "special"', "code")
        query = q._execute_write.call_args[0][0]
        assert '\\"special\\"' in query


# ── delete_agent ─────────────────────────────────────────

class TestDeleteAgent:
    def test_success(self):
        q = _TestableAgentQueries()
        q._execute_write.return_value = None
        assert q.delete_agent("a1") is True
        q._execute_write.assert_called_once()

    def test_failure(self):
        q = _TestableAgentQueries()
        q._execute_write.side_effect = Exception("error")
        assert q.delete_agent("a1") is False


# ── update_agent_trust ───────────────────────────────────

class TestUpdateAgentTrust:
    def test_updates_trust(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"name": "Agent", "type": "code", "trust": 0.5},
        ]
        q._execute_write.return_value = None
        result = q.update_agent_trust("a1", 0.95)
        assert result is True
        # Should delete + re-insert
        assert q._execute_write.call_count == 2

    def test_agent_not_found(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = []
        result = q.update_agent_trust("nonexistent", 0.95)
        assert result is False
        q._execute_write.assert_not_called()

    def test_write_error(self):
        q = _TestableAgentQueries()
        q._execute_query.return_value = [
            {"name": "Agent", "type": "code", "trust": 0.5},
        ]
        q._execute_write.side_effect = Exception("db error")
        result = q.update_agent_trust("a1", 0.95)
        assert result is False
