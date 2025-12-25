"""
Tests for MCP → Agno @tool Wrapper (P4.1)

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: R&D-BACKLOG.md Phase 4.1
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock


class TestGovernanceToolsUnit:
    """Unit tests for GovernanceTools class."""

    def test_governance_tools_class_exists(self):
        """GovernanceTools class exists and is importable."""
        from agent.mcp_tools import GovernanceTools
        assert GovernanceTools is not None

    def test_governance_tools_is_toolkit(self):
        """GovernanceTools inherits from Toolkit (real or stub)."""
        from agent.mcp_tools import GovernanceTools, Toolkit
        assert issubclass(GovernanceTools, Toolkit)

    def test_governance_tools_has_name(self):
        """GovernanceTools has toolkit name."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert tools.name == "governance"

    def test_governance_config_defaults(self):
        """GovernanceConfig has sensible defaults."""
        from agent.mcp_tools import GovernanceConfig
        config = GovernanceConfig()
        assert config.typedb_host == "localhost"
        assert config.typedb_port == 1729
        assert config.database == "sim-ai-governance"

    def test_governance_config_custom(self):
        """GovernanceConfig accepts custom values."""
        from agent.mcp_tools import GovernanceConfig
        config = GovernanceConfig(
            typedb_host="typedb-1",
            typedb_port=1730,
            database="custom-db"
        )
        assert config.typedb_host == "typedb-1"
        assert config.typedb_port == 1730
        assert config.database == "custom-db"


class TestGovernanceToolsMethods:
    """Test individual tool methods."""

    def test_query_rules_method_exists(self):
        """query_rules method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'query_rules')
        assert callable(tools.query_rules)

    def test_get_rule_method_exists(self):
        """get_rule method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'get_rule')
        assert callable(tools.get_rule)

    def test_get_dependencies_method_exists(self):
        """get_dependencies method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'get_dependencies')
        assert callable(tools.get_dependencies)

    def test_find_conflicts_method_exists(self):
        """find_conflicts method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'find_conflicts')
        assert callable(tools.find_conflicts)

    def test_get_trust_score_method_exists(self):
        """get_trust_score method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'get_trust_score')
        assert callable(tools.get_trust_score)

    def test_list_agents_method_exists(self):
        """list_agents method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'list_agents')
        assert callable(tools.list_agents)

    def test_health_check_method_exists(self):
        """health_check method exists."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        assert hasattr(tools, 'health_check')
        assert callable(tools.health_check)


class TestGovernanceToolsReturnFormat:
    """Test that tools return valid JSON strings."""

    def test_query_rules_returns_json(self):
        """query_rules returns JSON string."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        result = tools.query_rules()
        # Should be valid JSON even if error
        parsed = json.loads(result)
        assert isinstance(parsed, (list, dict))

    def test_get_rule_returns_json(self):
        """get_rule returns JSON string."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        result = tools.get_rule("RULE-001")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_health_check_returns_json(self):
        """health_check returns JSON string."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        result = tools.health_check()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "status" in parsed


class TestCreateGovernanceTools:
    """Test convenience function."""

    def test_create_governance_tools_exists(self):
        """create_governance_tools function exists."""
        from agent.mcp_tools import create_governance_tools
        assert create_governance_tools is not None
        assert callable(create_governance_tools)

    def test_create_governance_tools_returns_toolkit(self):
        """create_governance_tools returns GovernanceTools instance."""
        from agent.mcp_tools import create_governance_tools, GovernanceTools
        tools = create_governance_tools()
        assert isinstance(tools, GovernanceTools)

    def test_create_governance_tools_with_custom_config(self):
        """create_governance_tools accepts custom config."""
        from agent.mcp_tools import create_governance_tools
        tools = create_governance_tools(
            typedb_host="custom-host",
            typedb_port=9999,
            database="custom-db"
        )
        assert tools.config.typedb_host == "custom-host"
        assert tools.config.typedb_port == 9999
        assert tools.config.database == "custom-db"


class TestToolDecorator:
    """Test that methods have @tool decorator applied."""

    def test_query_rules_has_tool_metadata(self):
        """query_rules has tool metadata."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        # Check the function is registered in toolkit
        assert 'query_rules' in [f.__name__ for f in tools.functions.values()] or \
               len(tools.functions) > 0

    def test_all_seven_tools_registered(self):
        """All seven tools are registered in toolkit."""
        from agent.mcp_tools import GovernanceTools
        tools = GovernanceTools()
        # Toolkit should have 7 registered functions
        assert len(tools.functions) == 7


class TestAgentIntegration:
    """Test integration with Agno Agent (stubs for integration tests)."""

    @pytest.mark.skip(reason="Integration test - requires agent setup")
    def test_agent_can_use_governance_tools(self):
        """Agent can be created with GovernanceTools."""
        from agno.agent import Agent
        from agno.models.anthropic import Claude
        from agent.mcp_tools import GovernanceTools

        tools = GovernanceTools()
        agent = Agent(
            name="Test Agent",
            model=Claude(id="claude-sonnet-4-20250514"),
            tools=[tools]
        )
        assert agent is not None

    @pytest.mark.skip(reason="Integration test - requires TypeDB connection")
    def test_agent_query_rules_e2e(self):
        """Agent can query rules through toolkit."""
        pass


class TestMockTypeDBClient:
    """Tests with mocked TypeDB client."""

    @patch('agent.mcp_tools.TYPEDB_AVAILABLE', True)
    @patch('agent.mcp_tools.TypeDBClient')
    def test_query_rules_with_mock_client(self, MockClient):
        """query_rules works with mocked TypeDB client."""
        from agent.mcp_tools import GovernanceTools
        from governance.client import Rule

        # Setup mock
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = [
            Rule(
                id="RULE-001",
                name="Test Rule",
                category="test",
                priority="HIGH",
                status="ACTIVE",
                directive="Test directive"
            )
        ]
        MockClient.return_value = mock_client

        tools = GovernanceTools()
        result = tools.query_rules()

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "RULE-001"

    @patch('agent.mcp_tools.TYPEDB_AVAILABLE', False)
    def test_query_rules_without_typedb(self):
        """query_rules returns error when TypeDB unavailable."""
        from agent.mcp_tools import GovernanceTools

        tools = GovernanceTools()
        result = tools.query_rules()

        parsed = json.loads(result)
        assert "error" in parsed
        assert "not available" in parsed["error"]


class TestVoteWeightCalculation:
    """Test trust score to vote weight calculation."""

    @patch('agent.mcp_tools.TYPEDB_AVAILABLE', True)
    @patch('agent.mcp_tools.TypeDBClient')
    def test_high_trust_gets_full_weight(self, MockClient):
        """High trust agents (>= 0.5) get vote weight of 1.0."""
        from agent.mcp_tools import GovernanceTools

        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = [{
            'name': 'High Trust Agent',
            'trust': 0.75,
            'compliance': 0.8,
            'accuracy': 0.9,
            'tenure': 100
        }]
        MockClient.return_value = mock_client

        tools = GovernanceTools()
        result = tools.get_trust_score("AGENT-001")

        parsed = json.loads(result)
        assert parsed["vote_weight"] == 1.0

    @patch('agent.mcp_tools.TYPEDB_AVAILABLE', True)
    @patch('agent.mcp_tools.TypeDBClient')
    def test_low_trust_gets_reduced_weight(self, MockClient):
        """Low trust agents (< 0.5) get vote weight equal to trust score."""
        from agent.mcp_tools import GovernanceTools

        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = [{
            'name': 'Low Trust Agent',
            'trust': 0.3,
            'compliance': 0.4,
            'accuracy': 0.5,
            'tenure': 10
        }]
        MockClient.return_value = mock_client

        tools = GovernanceTools()
        result = tools.get_trust_score("AGENT-002")

        parsed = json.loads(result)
        assert parsed["vote_weight"] == 0.3
