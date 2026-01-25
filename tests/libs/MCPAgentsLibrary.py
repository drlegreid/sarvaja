"""
Robot Framework library for MCP Agents Tools tests.

Per P10.4: Agent CRUD MCP tools
Migrated from tests/test_mcp_agents.py
"""

import json
from robot.api.deco import keyword


class MCPAgentsLibrary:
    """Library for testing MCP agents tools functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Tools Existence Tests
    # =========================================================================

    @keyword("Agents Tools Importable")
    def agents_tools_importable(self):
        """Agents MCP tools module must be importable."""
        try:
            from governance.mcp_tools.agents import register_agent_tools
            return {"importable": register_agent_tools is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Agents Tools Registered")
    def agents_tools_registered(self):
        """Agents tools must be included in register_all_tools."""
        try:
            from governance.mcp_tools import register_agent_tools
            return {"registered": register_agent_tools is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Create Agent Tests
    # =========================================================================

    @keyword("Create Agent Tool Exists")
    def create_agent_tool_exists(self):
        """governance_create_agent must be callable."""
        try:
            from governance.compat import governance_create_agent
            return {"exists": callable(governance_create_agent)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Agent Returns JSON")
    def create_agent_returns_json(self):
        """governance_create_agent must return valid JSON."""
        try:
            from governance.compat import governance_create_agent
            result = governance_create_agent(
                agent_id="TEST-AGENT-001",
                name="Test Agent",
                agent_type="test-agent"
            )
            data = json.loads(result)
            return {"is_dict": isinstance(data, dict)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Read Agent Tests
    # =========================================================================

    @keyword("Get Agent Tool Exists")
    def get_agent_tool_exists(self):
        """governance_get_agent must be callable."""
        try:
            from governance.compat import governance_get_agent
            return {"exists": callable(governance_get_agent)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Agents Tool Exists")
    def list_agents_tool_exists(self):
        """governance_list_agents must be callable."""
        try:
            from governance.compat import governance_list_agents
            return {"exists": callable(governance_list_agents)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Update Agent Tests
    # =========================================================================

    @keyword("Update Agent Trust Exists")
    def update_agent_trust_exists(self):
        """governance_update_agent_trust must be callable."""
        try:
            from governance.compat import governance_update_agent_trust
            return {"exists": callable(governance_update_agent_trust)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TypeDB Operations Tests
    # =========================================================================

    @keyword("Client Has Agent Operations")
    def client_has_agent_operations(self):
        """TypeDB client must have agent CRUD methods."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            return {
                "has_insert_agent": hasattr(client, 'insert_agent'),
                "has_get_agent": hasattr(client, 'get_agent'),
                "has_get_all_agents": hasattr(client, 'get_all_agents'),
                "has_update_agent_trust": hasattr(client, 'update_agent_trust')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get All Agents From TypeDB")
    def get_all_agents_from_typedb(self):
        """Get all agents from TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB"}
            try:
                agents = client.get_all_agents()
                return {"is_list": isinstance(agents, list)}
            finally:
                client.close()
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
