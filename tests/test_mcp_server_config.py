"""
MCP Server Configuration Tests
Created: 2024-12-26
Updated: 2026-01-04 - Migrated to split server architecture
Per RULE-023: Test Before Ship

TDD tests to validate MCP server configuration BEFORE integration.
Tests the 4-server split architecture (governance-core, agents, sessions, tasks).
"""
import pytest
import json
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MCP_CONFIG = PROJECT_ROOT / ".mcp.json"


class TestMCPServerConfig:
    """Validate MCP server configuration."""

    @pytest.mark.unit
    def test_mcp_json_exists(self):
        """MCP config file must exist."""
        assert MCP_CONFIG.exists(), f".mcp.json not found at {MCP_CONFIG}"

    @pytest.mark.unit
    def test_mcp_json_valid_json(self):
        """MCP config must be valid JSON."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)
        assert "mcpServers" in config, "mcpServers key missing"

    @pytest.mark.unit
    def test_split_servers_defined(self):
        """All 4 split servers must be defined in config."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)

        expected = ["governance-core", "governance-agents",
                    "governance-sessions", "governance-tasks"]
        for server in expected:
            assert server in config["mcpServers"], f"{server} not defined"

    @pytest.mark.unit
    def test_monolith_removed(self):
        """Monolith 'governance' server must NOT be in config."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)
        assert "governance" not in config["mcpServers"], \
            "Deprecated 'governance' monolith should be removed"

    @pytest.mark.unit
    def test_each_server_has_required_fields(self):
        """Each governance server config must have required fields."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)

        governance_servers = ["governance-core", "governance-agents",
                              "governance-sessions", "governance-tasks"]

        for name in governance_servers:
            server = config.get("mcpServers", {}).get(name)
            assert server is not None, f"{name} not defined"
            assert "type" in server, f"{name} missing 'type'"
            assert server["type"] == "stdio", f"{name} type should be stdio"
            assert "command" in server, f"{name} missing 'command'"
            assert "args" in server, f"{name} missing 'args'"
            assert "env" in server, f"{name} missing 'env'"
            assert "TYPEDB_HOST" in server["env"], f"{name} missing TYPEDB_HOST"
            assert "TYPEDB_PORT" in server["env"], f"{name} missing TYPEDB_PORT"


class TestMCPServerStartup:
    """Validate MCP split servers can start."""

    @pytest.mark.integration
    def test_core_server_imports(self):
        """Core server module must import without errors."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.mcp_server_core import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    @pytest.mark.integration
    def test_core_server_starts(self):
        """Core server must start with python -m."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        env["TYPEDB_HOST"] = "localhost"
        env["TYPEDB_PORT"] = "1729"

        result = subprocess.run(
            [sys.executable, "-m", "governance.mcp_server_core"],
            cwd=str(PROJECT_ROOT),
            env=env,
            input="",  # EOF
            capture_output=True,
            text=True,
            timeout=5
        )
        assert "ModuleNotFoundError" not in result.stderr
        assert "ImportError" not in result.stderr


class TestMCPToolsAvailable:
    """Validate MCP tools are callable via compat package."""

    @pytest.mark.integration
    def test_governance_query_rules_callable(self):
        """governance_query_rules must be callable."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from governance.compat import governance_query_rules

        result = governance_query_rules()
        assert result is not None, "governance_query_rules returned None"

        data = json.loads(result)
        # Accept either list of rules or error dict (if TypeDB not available)
        if isinstance(data, dict) and "error" in data:
            pytest.skip(f"TypeDB not available: {data['error']}")
        assert isinstance(data, list), "Expected list of rules"

    @pytest.mark.integration
    def test_rules_have_directive_content(self):
        """Rules must have full directive content, not just descriptions."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from governance.compat import governance_query_rules

        result = governance_query_rules()
        rules = json.loads(result)

        # Skip if TypeDB not available
        if isinstance(rules, dict) and "error" in rules:
            pytest.skip(f"TypeDB not available: {rules['error']}")

        assert len(rules) > 0, "No rules found"

        for rule in rules[:5]:  # Check first 5
            assert "directive" in rule, f"Rule {rule.get('id')} missing directive"
            assert rule["directive"], f"Rule {rule.get('id')} has empty directive"
            assert len(rule["directive"]) > 10, f"Rule {rule.get('id')} directive too short"

    @pytest.mark.integration
    def test_governance_list_tasks_callable(self):
        """governance_list_tasks must be callable."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from governance.compat import governance_list_tasks

        result = governance_list_tasks()
        assert result is not None, "governance_list_tasks returned None"

        data = json.loads(result)
        # Response can be {"tasks": [...], "count": N} or a raw list
        if isinstance(data, dict):
            assert "tasks" in data, "Expected 'tasks' key in response"
            tasks = data["tasks"]
        else:
            tasks = data
        assert isinstance(tasks, list), "Expected list of tasks"
