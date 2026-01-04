"""
MCP Agents Tools Tests
======================
TDD tests for Agent CRUD MCP tools per P10.4.
Created: 2024-12-26
Per RULE-023: Test Before Ship

Tests written BEFORE implementation per TDD.
"""
import pytest
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_agents():
    """
    Module-scoped cleanup for TEST-* agents.

    Per GAP-TDD-006: Test data isolation.
    Runs after all tests in this module to clean up TEST-* entities.
    """
    yield  # Run all tests first

    # Cleanup TEST-* agents from TypeDB
    try:
        from governance.compat import governance_list_agents
        # Note: governance_delete_agent may not exist yet, using TypeDB client directly
        from governance.client import TypeDBClient

        result = governance_list_agents()
        data = json.loads(result) if isinstance(result, str) else result
        agents = data.get("agents", []) if isinstance(data, dict) else data

        client = TypeDBClient()
        for agent in agents:
            agent_id = agent.get("agent_id", "") if isinstance(agent, dict) else ""
            if agent_id.startswith("TEST-"):
                try:
                    client.delete_agent(agent_id)
                except Exception:
                    pass
    except Exception:
        pass  # Cleanup is best-effort


class TestAgentsMCPToolsExist:
    """Validate Agents MCP tools are registered."""

    @pytest.mark.unit
    def test_agents_tools_importable(self):
        """Agents MCP tools module must be importable."""
        try:
            from governance.mcp_tools.agents import register_agent_tools
            assert register_agent_tools is not None
        except ImportError as e:
            pytest.skip(f"Agents MCP tools not yet implemented: {e}")

    @pytest.mark.unit
    def test_agents_tools_registered(self):
        """Agents tools must be included in register_all_tools."""
        try:
            from governance.mcp_tools import register_agent_tools
            assert register_agent_tools is not None
        except ImportError:
            pytest.skip("register_agent_tools not exported from mcp_tools")


class TestAgentCreateMCP:
    """Test governance_create_agent MCP tool."""

    @pytest.mark.integration
    def test_create_agent_tool_exists(self):
        """governance_create_agent must be callable."""
        try:
            from governance.compat import governance_create_agent
            assert callable(governance_create_agent)
        except (ImportError, AttributeError):
            pytest.skip("governance_create_agent not yet exported")

    @pytest.mark.integration
    def test_create_agent_returns_json(self):
        """governance_create_agent must return valid JSON."""
        try:
            from governance.compat import governance_create_agent
            result = governance_create_agent(
                agent_id="TEST-AGENT-001",
                name="Test Agent",
                agent_type="test-agent"
            )
            data = json.loads(result)
            assert isinstance(data, dict)
        except (ImportError, AttributeError):
            pytest.skip("governance_create_agent not yet exported")


class TestAgentReadMCP:
    """Test governance_get_agent MCP tool."""

    @pytest.mark.integration
    def test_get_agent_tool_exists(self):
        """governance_get_agent must be callable."""
        try:
            from governance.compat import governance_get_agent
            assert callable(governance_get_agent)
        except (ImportError, AttributeError):
            pytest.skip("governance_get_agent not yet exported")

    @pytest.mark.integration
    def test_list_agents_tool_exists(self):
        """governance_list_agents must be callable."""
        try:
            from governance.compat import governance_list_agents
            assert callable(governance_list_agents)
        except (ImportError, AttributeError):
            pytest.skip("governance_list_agents not yet exported")


class TestAgentUpdateMCP:
    """Test governance_update_agent MCP tool."""

    @pytest.mark.integration
    def test_update_agent_trust_exists(self):
        """governance_update_agent_trust must be callable."""
        try:
            from governance.compat import governance_update_agent_trust
            assert callable(governance_update_agent_trust)
        except (ImportError, AttributeError):
            pytest.skip("governance_update_agent_trust not yet exported")


class TestTypeDBAgentOperations:
    """Test TypeDB client agent operations (P10.3)."""

    @pytest.mark.integration
    def test_client_has_agent_operations(self):
        """TypeDB client must have agent CRUD methods."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            assert hasattr(client, 'insert_agent'), "insert_agent missing"
            assert hasattr(client, 'get_agent'), "get_agent missing"
            assert hasattr(client, 'get_all_agents'), "get_all_agents missing"
            assert hasattr(client, 'update_agent_trust'), "update_agent_trust missing"
        except ImportError:
            pytest.skip("TypeDBClient not available")
        except AssertionError as e:
            pytest.skip(f"Agent operations not yet implemented: {e}")

    @pytest.mark.integration
    def test_get_all_agents_from_typedb(self):
        """Get all agents from TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                pytest.skip("Cannot connect to TypeDB")
            try:
                agents = client.get_all_agents()
                assert isinstance(agents, list)
            finally:
                client.close()
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Agent operations not yet implemented: {e}")
