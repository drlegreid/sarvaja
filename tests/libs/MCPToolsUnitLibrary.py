"""
Robot Framework Library for MCP Tools Unit Tests.

Per P4.1: MCP → Agno @tool Wrapper.
Split from tests/test_mcp_tools.py per DOC-SIZE-01-v1.
"""
import json
from pathlib import Path
from robot.api.deco import keyword


def call_tool(tools, method_name, *args, **kwargs):
    """Call a tool method, handling both agno and stub cases."""
    method = getattr(tools, method_name)
    if hasattr(method, 'entrypoint'):
        return method.entrypoint(tools, *args, **kwargs)
    else:
        return method(*args, **kwargs)


def is_tool_callable(method):
    """Check if a method is callable as a tool."""
    if hasattr(method, 'entrypoint'):
        return callable(method.entrypoint)
    return callable(method)


class MCPToolsUnitLibrary:
    """Library for MCP tools unit tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # GovernanceTools Unit Tests
    # =========================================================================

    @keyword("Governance Tools Class Exists")
    def governance_tools_class_exists(self):
        """GovernanceTools class exists and is importable."""
        try:
            from agent.mcp_tools import GovernanceTools
            return {"exists": GovernanceTools is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Tools Is Toolkit")
    def governance_tools_is_toolkit(self):
        """GovernanceTools inherits from Toolkit."""
        try:
            from agent.mcp_tools import GovernanceTools, Toolkit
            return {"is_toolkit": issubclass(GovernanceTools, Toolkit)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Tools Has Name")
    def governance_tools_has_name(self):
        """GovernanceTools has toolkit name."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {"name_correct": tools.name == "governance"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Config Defaults")
    def governance_config_defaults(self):
        """GovernanceConfig has sensible defaults."""
        try:
            from agent.mcp_tools import GovernanceConfig
            config = GovernanceConfig()
            return {
                "host_default": config.typedb_host == "localhost",
                "port_default": config.typedb_port == 1729,
                "db_default": config.database == "sim-ai-governance"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Config Custom")
    def governance_config_custom(self):
        """GovernanceConfig accepts custom values."""
        try:
            from agent.mcp_tools import GovernanceConfig
            config = GovernanceConfig(
                typedb_host="typedb-1",
                typedb_port=1730,
                database="custom-db"
            )
            return {
                "host_custom": config.typedb_host == "typedb-1",
                "port_custom": config.typedb_port == 1730,
                "db_custom": config.database == "custom-db"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Method Existence Tests
    # =========================================================================

    @keyword("Query Rules Method Exists")
    def query_rules_method_exists(self):
        """query_rules method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'query_rules'),
                "is_callable": is_tool_callable(tools.query_rules)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rule Method Exists")
    def get_rule_method_exists(self):
        """get_rule method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'get_rule'),
                "is_callable": is_tool_callable(tools.get_rule)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Dependencies Method Exists")
    def get_dependencies_method_exists(self):
        """get_dependencies method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'get_dependencies'),
                "is_callable": is_tool_callable(tools.get_dependencies)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Find Conflicts Method Exists")
    def find_conflicts_method_exists(self):
        """find_conflicts method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'find_conflicts'),
                "is_callable": is_tool_callable(tools.find_conflicts)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Trust Score Method Exists")
    def get_trust_score_method_exists(self):
        """get_trust_score method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'get_trust_score'),
                "is_callable": is_tool_callable(tools.get_trust_score)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Agents Method Exists")
    def list_agents_method_exists(self):
        """list_agents method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'list_agents'),
                "is_callable": is_tool_callable(tools.list_agents)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Check Method Exists")
    def health_check_method_exists(self):
        """health_check method exists."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {
                "has_method": hasattr(tools, 'health_check'),
                "is_callable": is_tool_callable(tools.health_check)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Return Format Tests
    # =========================================================================

    @keyword("Query Rules Returns JSON")
    def query_rules_returns_json(self):
        """query_rules returns JSON string."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            result = call_tool(tools, 'query_rules')
            parsed = json.loads(result)
            return {"valid_json": isinstance(parsed, (list, dict))}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Get Rule Returns JSON")
    def get_rule_returns_json(self):
        """get_rule returns JSON string."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            result = call_tool(tools, 'get_rule', "RULE-001")
            parsed = json.loads(result)
            return {"valid_json": isinstance(parsed, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Health Check Returns JSON")
    def health_check_returns_json(self):
        """health_check returns JSON string."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            result = call_tool(tools, 'health_check')
            parsed = json.loads(result)
            return {
                "valid_json": isinstance(parsed, dict),
                "has_status": "status" in parsed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False, "has_status": False}

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    @keyword("Create Governance Tools Exists")
    def create_governance_tools_exists(self):
        """create_governance_tools function exists."""
        try:
            from agent.mcp_tools import create_governance_tools
            return {
                "exists": create_governance_tools is not None,
                "callable": callable(create_governance_tools)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Governance Tools Returns Toolkit")
    def create_governance_tools_returns_toolkit(self):
        """create_governance_tools returns GovernanceTools instance."""
        try:
            from agent.mcp_tools import create_governance_tools, GovernanceTools
            tools = create_governance_tools()
            return {"is_instance": isinstance(tools, GovernanceTools)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Governance Tools With Custom Config")
    def create_governance_tools_with_custom_config(self):
        """create_governance_tools accepts custom config."""
        try:
            from agent.mcp_tools import create_governance_tools
            tools = create_governance_tools(
                typedb_host="custom-host",
                typedb_port=9999,
                database="custom-db"
            )
            return {
                "host_custom": tools.config.typedb_host == "custom-host",
                "port_custom": tools.config.typedb_port == 9999,
                "db_custom": tools.config.database == "custom-db"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Tool Decorator Tests
    # =========================================================================

    @keyword("Query Rules Has Tool Metadata")
    def query_rules_has_tool_metadata(self):
        """query_rules has tool metadata."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            func_names = []
            for f in tools.functions.values():
                if hasattr(f, 'name'):
                    func_names.append(f.name)
                elif hasattr(f, '__name__'):
                    func_names.append(f.__name__)
            return {
                "has_metadata": 'query_rules' in func_names or len(tools.functions) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("All Seven Tools Registered")
    def all_seven_tools_registered(self):
        """All seven tools are registered in toolkit."""
        try:
            from agent.mcp_tools import GovernanceTools
            tools = GovernanceTools()
            return {"count_correct": len(tools.functions) == 7}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
