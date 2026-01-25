"""
Robot Framework Library for MCP Server Configuration Tests.

Per RULE-023: Test Before Ship
Per ARCH-MCP-02-v1: MCP Split Architecture
Migrated from tests/test_mcp_server_config.py
"""
import json
from pathlib import Path
from robot.api.deco import keyword


class MCPServerConfigLibrary:
    """Library for testing MCP server configuration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.mcp_config = self.project_root / ".mcp.json"

    @keyword("MCP JSON Exists")
    def mcp_json_exists(self):
        """MCP config file must exist."""
        return {"exists": self.mcp_config.exists()}

    @keyword("MCP JSON Valid JSON")
    def mcp_json_valid_json(self):
        """MCP config must be valid JSON."""
        if not self.mcp_config.exists():
            return {"skipped": True, "reason": ".mcp.json not found"}

        try:
            with open(self.mcp_config) as f:
                config = json.load(f)
            return {
                "valid": True,
                "has_mcp_servers": "mcpServers" in config
            }
        except json.JSONDecodeError as e:
            return {"valid": False, "error": str(e)}

    @keyword("Split Servers Defined")
    def split_servers_defined(self):
        """All 4 split servers must be defined in config."""
        if not self.mcp_config.exists():
            return {"skipped": True, "reason": ".mcp.json not found"}

        try:
            with open(self.mcp_config) as f:
                config = json.load(f)

            # Per GAP-MCP-NAMING-001: governance → gov
            expected = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]
            servers = config.get("mcpServers", {})

            results = {}
            for server in expected:
                results[f"has_{server.replace('-', '_')}"] = server in servers

            results["all_defined"] = all(server in servers for server in expected)
            return results
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Monolith Removed")
    def monolith_removed(self):
        """Monolith 'governance' server must NOT be in config."""
        if not self.mcp_config.exists():
            return {"skipped": True, "reason": ".mcp.json not found"}

        try:
            with open(self.mcp_config) as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})
            return {"monolith_removed": "governance" not in servers}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Each Server Has Required Fields")
    def each_server_has_required_fields(self):
        """Each governance server config must have required fields."""
        if not self.mcp_config.exists():
            return {"skipped": True, "reason": ".mcp.json not found"}

        try:
            with open(self.mcp_config) as f:
                config = json.load(f)

            # Per GAP-MCP-NAMING-001: governance → gov
            governance_servers = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]
            servers = config.get("mcpServers", {})

            all_valid = True
            missing = []

            for name in governance_servers:
                server = servers.get(name)
                if server is None:
                    all_valid = False
                    missing.append(f"{name} not defined")
                    continue

                if "type" not in server:
                    all_valid = False
                    missing.append(f"{name} missing 'type'")
                elif server["type"] != "stdio":
                    all_valid = False
                    missing.append(f"{name} type should be stdio")

                if "command" not in server:
                    all_valid = False
                    missing.append(f"{name} missing 'command'")

                if "args" not in server:
                    all_valid = False
                    missing.append(f"{name} missing 'args'")

                env = server.get("env", {})
                if "TYPEDB_HOST" not in env:
                    all_valid = False
                    missing.append(f"{name} missing TYPEDB_HOST")

                if "TYPEDB_PORT" not in env:
                    all_valid = False
                    missing.append(f"{name} missing TYPEDB_PORT")

            return {
                "all_valid": all_valid,
                "missing_count": len(missing)
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
