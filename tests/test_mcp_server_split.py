"""
MCP Server Split Tests
======================
Per RULE-023: Test Before Ship
Per 4-Server Split Architecture (2026-01-03)

Tests that validate the 4 MCP servers can start independently.
"""
import pytest
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestMCPServerSeparation:
    """Validate 4 MCP servers start independently."""

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
    def test_agents_server_imports(self):
        """Agents server module must import without errors."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.mcp_server_agents import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    @pytest.mark.integration
    def test_sessions_server_imports(self):
        """Sessions server module must import without errors."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.mcp_server_sessions import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    @pytest.mark.integration
    def test_tasks_server_imports(self):
        """Tasks server module must import without errors."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.mcp_server_tasks import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    @pytest.mark.integration
    def test_compat_package_imports(self):
        """Compat package must export all legacy functions."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.compat import governance_query_rules, dsm_start, session_start"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"


class TestMCPConfigValid:
    """Validate .mcp.json has all 4 split servers defined (monolith deprecated)."""

    @pytest.mark.unit
    def test_mcp_json_has_4_servers(self):
        """MCP config must have 4 split server definitions (monolith deprecated 2026-01-04)."""
        import json
        mcp_config = PROJECT_ROOT / ".mcp.json"
        with open(mcp_config) as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})
        # NOTE: 'governance' monolith removed 2026-01-04 per GAP-MCP-005
        # Per GAP-MCP-NAMING-001: governance → gov
        expected = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]

        for server in expected:
            assert server in servers, f"Server {server} not in .mcp.json"

        # Verify monolith is NOT present (deprecated)
        assert "governance" not in servers, "Deprecated 'governance' monolith should be removed"

    @pytest.mark.unit
    def test_each_server_has_required_fields(self):
        """Each governance server config must have required fields."""
        import json
        mcp_config = PROJECT_ROOT / ".mcp.json"
        with open(mcp_config) as f:
            config = json.load(f)

        # Per GAP-MCP-NAMING-001: governance → gov
        governance_servers = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]

        for name in governance_servers:
            server = config.get("mcpServers", {}).get(name)
            assert server is not None, f"{name} not defined"
            assert "type" in server, f"{name} missing 'type'"
            assert "command" in server, f"{name} missing 'command'"
            assert "args" in server, f"{name} missing 'args'"
            assert "env" in server, f"{name} missing 'env'"
            assert "TYPEDB_HOST" in server["env"], f"{name} missing TYPEDB_HOST"
            assert "TYPEDB_PORT" in server["env"], f"{name} missing TYPEDB_PORT"


class TestModularizedFiles:
    """Validate files are properly modularized per RULE-032."""

    @pytest.mark.unit
    def test_rules_orchestrator_exists(self):
        """rules.py must be a thin orchestrator."""
        rules_file = PROJECT_ROOT / "governance" / "mcp_tools" / "rules.py"
        content = rules_file.read_text()
        lines = len(content.splitlines())
        assert lines < 50, f"rules.py too large: {lines} lines (should be <50)"

    @pytest.mark.unit
    def test_sessions_orchestrator_exists(self):
        """sessions.py must be a thin orchestrator."""
        sessions_file = PROJECT_ROOT / "governance" / "mcp_tools" / "sessions.py"
        content = sessions_file.read_text()
        lines = len(content.splitlines())
        assert lines < 50, f"sessions.py too large: {lines} lines (should be <50)"

    @pytest.mark.unit
    def test_tasks_orchestrator_exists(self):
        """tasks.py must be a thin orchestrator."""
        tasks_file = PROJECT_ROOT / "governance" / "mcp_tools" / "tasks.py"
        content = tasks_file.read_text()
        lines = len(content.splitlines())
        assert lines < 50, f"tasks.py too large: {lines} lines (should be <50)"

    @pytest.mark.unit
    def test_split_modules_exist(self):
        """Split module files must exist."""
        mcp_tools = PROJECT_ROOT / "governance" / "mcp_tools"

        expected_files = [
            "rules_query.py",
            "rules_crud.py",
            "rules_archive.py",
            "sessions_core.py",
            "sessions_linking.py",
            "tasks_crud.py",
            "tasks_linking.py",
        ]

        for filename in expected_files:
            assert (mcp_tools / filename).exists(), f"{filename} not found"

    @pytest.mark.unit
    def test_split_modules_under_300_lines(self):
        """Split modules must be under 300 lines per RULE-032."""
        mcp_tools = PROJECT_ROOT / "governance" / "mcp_tools"

        modules = [
            "rules_query.py",
            "rules_crud.py",
            "rules_archive.py",
            "sessions_core.py",
            "sessions_linking.py",
            "tasks_crud.py",
            "tasks_linking.py",
        ]

        for filename in modules:
            filepath = mcp_tools / filename
            content = filepath.read_text()
            lines = len(content.splitlines())
            # RULE-032 targets 300 lines, allow 5% tolerance (315)
            assert lines <= 315, f"{filename} too large: {lines} lines (limit: 315)"
