"""
MCP Server Configuration Tests
Created: 2024-12-26
Per RULE-023: Test Before Ship

TDD tests to validate MCP server configuration BEFORE integration.
These tests should have been written BEFORE creating .mcp.json.
"""
import pytest
import json
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MCP_CONFIG = PROJECT_ROOT / ".mcp.json"
MCP_SERVER = PROJECT_ROOT / "governance" / "mcp_server.py"


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
    def test_governance_server_defined(self):
        """Governance server must be defined in config."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)
        assert "governance" in config["mcpServers"], "governance server not defined"

    @pytest.mark.unit
    def test_governance_server_has_required_fields(self):
        """Governance server config must have required fields."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)
        gov = config["mcpServers"]["governance"]

        assert "type" in gov, "type field missing"
        assert gov["type"] == "stdio", f"Expected stdio, got {gov['type']}"
        assert "command" in gov, "command field missing"
        assert "args" in gov, "args field missing"

    @pytest.mark.unit
    def test_governance_server_env_has_typedb(self):
        """Governance server must have TypeDB env vars."""
        with open(MCP_CONFIG) as f:
            config = json.load(f)
        gov = config["mcpServers"]["governance"]

        assert "env" in gov, "env field missing"
        assert "TYPEDB_HOST" in gov["env"], "TYPEDB_HOST missing"
        assert "TYPEDB_PORT" in gov["env"], "TYPEDB_PORT missing"


class TestMCPServerStartup:
    """Validate MCP server can actually start."""

    @pytest.mark.integration
    def test_mcp_server_module_imports(self):
        """MCP server module must import without errors."""
        # This was the bug - module import failed due to path issues
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); from governance.mcp_server import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    @pytest.mark.integration
    def test_mcp_server_starts_with_module_flag(self):
        """MCP server must start with python -m."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        env["TYPEDB_HOST"] = "localhost"
        env["TYPEDB_PORT"] = "1729"

        # Start server and immediately send EOF to stop it
        result = subprocess.run(
            [sys.executable, "-m", "governance.mcp_server"],
            cwd=str(PROJECT_ROOT),
            env=env,
            input="",  # EOF
            capture_output=True,
            text=True,
            timeout=5
        )
        # Server should exit cleanly (0) or with expected code
        # The important thing is no import errors
        assert "ModuleNotFoundError" not in result.stderr, f"Module import failed: {result.stderr}"
        assert "ImportError" not in result.stderr, f"Import failed: {result.stderr}"


class TestMCPToolsAvailable:
    """Validate MCP tools are callable."""

    @pytest.mark.integration
    def test_governance_query_rules_callable(self):
        """governance_query_rules must be callable."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from governance.mcp_server import governance_query_rules

        result = governance_query_rules()
        assert result is not None, "governance_query_rules returned None"

        data = json.loads(result)
        assert isinstance(data, list), "Expected list of rules"

    @pytest.mark.integration
    def test_rules_have_directive_content(self):
        """Rules must have full directive content, not just descriptions."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from governance.mcp_server import governance_query_rules

        result = governance_query_rules()
        rules = json.loads(result)

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
        from governance.mcp_server import governance_list_tasks

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
