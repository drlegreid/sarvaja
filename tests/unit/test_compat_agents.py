"""
Unit tests for Compat - Agent CRUD Exports.

Per DOC-SIZE-01-v1: Tests for compat/agents.py module.
Tests: governance_create_agent, governance_get_agent,
       governance_list_agents, governance_update_agent_trust.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestGovernanceCreateAgent:
    """Tests for governance_create_agent()."""

    @patch("governance.compat.agents.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.insert_agent.return_value = True
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_create_agent
        result = json.loads(governance_create_agent("A-1", "Test", "claude-code"))
        assert result["agent_id"] == "A-1"
        assert result["trust_score"] == 0.8  # default
        mock_client.close.assert_called_once()

    @patch("governance.compat.agents.get_typedb_client")
    def test_connect_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_create_agent
        result = json.loads(governance_create_agent("A-1", "Test", "t"))
        assert "error" in result

    @patch("governance.compat.agents.get_typedb_client")
    def test_insert_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.insert_agent.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_create_agent
        result = json.loads(governance_create_agent("A-1", "Test", "t"))
        assert "error" in result

    @patch("governance.compat.agents.get_typedb_client")
    def test_custom_trust(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.insert_agent.return_value = True
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_create_agent
        result = json.loads(governance_create_agent("A-1", "Test", "t", trust_score=0.95))
        assert result["trust_score"] == 0.95


class TestGovernanceGetAgent:
    """Tests for governance_get_agent()."""

    @patch("governance.compat.agents.get_typedb_client")
    def test_found(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_agent = MagicMock()
        mock_client.get_agent.return_value = mock_agent
        mock_get.return_value = mock_client

        with patch("governance.compat.agents.asdict", return_value={"agent_id": "A-1"}):
            from governance.compat.agents import governance_get_agent
            result = json.loads(governance_get_agent("A-1"))
            assert result["agent_id"] == "A-1"

    @patch("governance.compat.agents.get_typedb_client")
    def test_not_found(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_agent.return_value = None
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_get_agent
        result = json.loads(governance_get_agent("MISSING"))
        assert "error" in result


class TestGovernanceListAgents:
    """Tests for governance_list_agents()."""

    @patch("governance.compat.agents.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_agent = MagicMock()
        mock_client.get_all_agents.return_value = [mock_agent]
        mock_get.return_value = mock_client

        with patch("governance.compat.agents.asdict", return_value={"agent_id": "A-1"}):
            from governance.compat.agents import governance_list_agents
            result = json.loads(governance_list_agents())
            assert result["count"] == 1
            assert result["source"] == "typedb"

    @patch("governance.compat.agents.get_typedb_client")
    def test_connect_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_list_agents
        result = json.loads(governance_list_agents())
        assert "error" in result


class TestGovernanceUpdateAgentTrust:
    """Tests for governance_update_agent_trust()."""

    def test_invalid_score_too_high(self):
        from governance.compat.agents import governance_update_agent_trust
        result = json.loads(governance_update_agent_trust("A-1", 1.5))
        assert "error" in result

    def test_invalid_score_negative(self):
        from governance.compat.agents import governance_update_agent_trust
        result = json.loads(governance_update_agent_trust("A-1", -0.1))
        assert "error" in result

    @patch("governance.compat.agents.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.update_agent_trust.return_value = True
        mock_client.get_agent.return_value = None  # agent lookup after
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_update_agent_trust
        result = json.loads(governance_update_agent_trust("A-1", 0.9))
        assert "message" in result

    @patch("governance.compat.agents.get_typedb_client")
    def test_update_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.update_agent_trust.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.agents import governance_update_agent_trust
        result = json.loads(governance_update_agent_trust("A-1", 0.5))
        assert "error" in result
