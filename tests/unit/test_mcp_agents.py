"""
Unit tests for Agents MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/agents.py module.
Tests: agent_create, agent_get, agents_list, agent_trust_update,
       agents_dashboard, agent_activity.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.agents import register_agent_tools


class _CaptureMCP:
    """Mock MCP server that captures tool registrations."""
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _patch_format():
    with patch(
        "governance.mcp_tools.agents.format_mcp_result",
        side_effect=lambda x: json.dumps(x),
    ):
        yield


@pytest.fixture(autouse=True)
def _patch_monitoring():
    with patch("governance.mcp_tools.agents.MONITORING_AVAILABLE", False):
        yield


@pytest.fixture()
def tools():
    mcp = _CaptureMCP()
    register_agent_tools(mcp)
    return mcp.tools


class TestRegistration:
    def test_registers_six_tools(self, tools):
        assert "agent_create" in tools
        assert "agent_get" in tools
        assert "agents_list" in tools
        assert "agent_trust_update" in tools
        assert "agents_dashboard" in tools
        assert "agent_activity" in tools


class TestAgentCreate:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_success(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.insert_agent.return_value = True
        mock_client.return_value = client
        result = json.loads(tools["agent_create"]("A-1", "Agent One", "coding"))
        assert result["agent_id"] == "A-1"
        assert result["message"]

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_connect_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agent_create"]("A-1", "Agent One", "coding"))
        assert "error" in result

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_insert_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.insert_agent.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agent_create"]("A-1", "Agent One", "coding"))
        assert "error" in result

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_custom_trust_score(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.insert_agent.return_value = True
        mock_client.return_value = client
        result = json.loads(tools["agent_create"]("A-1", "Agent", "coding", trust_score=0.5))
        assert result["trust_score"] == 0.5


class TestAgentGet:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_found(self, mock_client, tools):
        agent = MagicMock()
        agent.id = "A-1"
        agent.name = "Agent"
        client = MagicMock()
        client.connect.return_value = True
        client.get_agent.return_value = agent
        mock_client.return_value = client
        # asdict needs a real dataclass, so mock it
        with patch("governance.mcp_tools.agents.asdict", return_value={"id": "A-1", "name": "Agent"}):
            result = json.loads(tools["agent_get"]("A-1"))
        assert result["id"] == "A-1"

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_not_found(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.get_agent.return_value = None
        mock_client.return_value = client
        result = json.loads(tools["agent_get"]("MISSING"))
        assert "error" in result


class TestAgentsList:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_success(self, mock_client, tools):
        agent = MagicMock()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_agents.return_value = [agent]
        mock_client.return_value = client
        with patch("governance.mcp_tools.agents.asdict", return_value={"id": "A-1"}):
            result = json.loads(tools["agents_list"]())
        assert result["count"] == 1
        assert result["source"] == "typedb"

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_connect_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agents_list"]())
        assert "error" in result


class TestAgentTrustUpdate:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_invalid_score(self, mock_client, tools):
        result = json.loads(tools["agent_trust_update"]("A-1", 1.5))
        assert "error" in result
        assert "0.0 and 1.0" in result["error"]

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_negative_score(self, mock_client, tools):
        result = json.loads(tools["agent_trust_update"]("A-1", -0.1))
        assert "error" in result

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_success_with_agent(self, mock_client, tools):
        agent = MagicMock()
        client = MagicMock()
        client.connect.return_value = True
        client.update_agent_trust.return_value = True
        client.get_agent.return_value = agent
        mock_client.return_value = client
        with patch("governance.mcp_tools.agents.asdict", return_value={"id": "A-1", "trust_score": 0.9}):
            result = json.loads(tools["agent_trust_update"]("A-1", 0.9))
        assert "message" in result

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_success_agent_not_refetched(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.update_agent_trust.return_value = True
        client.get_agent.return_value = None
        mock_client.return_value = client
        result = json.loads(tools["agent_trust_update"]("A-1", 0.5))
        assert result["trust_score"] == 0.5

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_update_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.update_agent_trust.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agent_trust_update"]("A-1", 0.5))
        assert "error" in result


class TestAgentsDashboard:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_success(self, mock_client, tools):
        agent = MagicMock()
        agent.id = "A-1"
        agent.name = "Agent"
        agent.agent_type = "coding"
        agent.trust_score = 0.9
        agent.status = "ACTIVE"
        agent.tasks_executed = 5
        agent.last_active = None
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_agents.return_value = [agent]
        mock_client.return_value = client
        with patch("governance.orchestrator.handoff.get_pending_handoffs", return_value=[]):
            result = json.loads(tools["agents_dashboard"]())
        assert result["summary"]["total_agents"] == 1
        assert result["summary"]["avg_trust_score"] == 0.9
        assert result["trust_distribution"]["high"] == 1

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_handoff_error_handled(self, mock_client, tools):
        agent = MagicMock()
        agent.id = "A-1"
        agent.name = "Agent"
        agent.agent_type = "coding"
        agent.trust_score = 0.8
        agent.status = "ACTIVE"
        agent.tasks_executed = 0
        agent.last_active = "2026-01-01"
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_agents.return_value = [agent]
        mock_client.return_value = client
        with patch("governance.orchestrator.handoff.get_pending_handoffs",
                   side_effect=Exception("no handoffs")):
            result = json.loads(tools["agents_dashboard"]())
        assert result["summary"]["pending_handoffs"] == 0

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_connect_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agents_dashboard"]())
        assert "error" in result


class TestAgentActivity:
    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_with_results(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.execute_fetch.return_value = [
            {"tid": {"value": "T-1"}, "name": {"value": "Task 1"},
             "status": {"value": "DONE"}, "aid": {"value": "A-1"}},
        ]
        mock_client.return_value = client
        result = json.loads(tools["agent_activity"]())
        assert result["count"] == 1
        assert result["filter"] == "all"

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_with_agent_filter(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.execute_fetch.return_value = []
        mock_client.return_value = client
        result = json.loads(tools["agent_activity"](agent_id="A-1"))
        assert result["filter"] == "A-1"

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_no_relations(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = True
        client.execute_fetch.side_effect = Exception("no relation")
        mock_client.return_value = client
        result = json.loads(tools["agent_activity"]())
        assert result["count"] == 0
        assert "note" in result

    @patch("governance.mcp_tools.agents.get_typedb_client")
    def test_connect_failure(self, mock_client, tools):
        client = MagicMock()
        client.connect.return_value = False
        mock_client.return_value = client
        result = json.loads(tools["agent_activity"]())
        assert "error" in result
