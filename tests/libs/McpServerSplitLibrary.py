"""
RF-004: Robot Framework Library for MCP Server Split Tests.

Wraps tests/test_mcp_server_split.py for Robot Framework tests.
Per 4-Server Split Architecture (2026-01-03).
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MCP_TOOLS_DIR = PROJECT_ROOT / "governance" / "mcp_tools"


class McpServerSplitLibrary:
    """Robot Framework library for MCP Server Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def test_server_imports(self, server_module: str) -> Dict[str, Any]:
        """Test a specific server module imports without errors."""
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '.'); "
             f"from governance.{server_module} import mcp"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "stderr": result.stderr if result.returncode != 0 else None
        }

    def test_core_server_imports(self) -> Dict[str, Any]:
        """Test core server module imports."""
        return self.test_server_imports("mcp_server_core")

    def test_agents_server_imports(self) -> Dict[str, Any]:
        """Test agents server module imports."""
        return self.test_server_imports("mcp_server_agents")

    def test_sessions_server_imports(self) -> Dict[str, Any]:
        """Test sessions server module imports."""
        return self.test_server_imports("mcp_server_sessions")

    def test_tasks_server_imports(self) -> Dict[str, Any]:
        """Test tasks server module imports."""
        return self.test_server_imports("mcp_server_tasks")

    def test_compat_package_imports(self) -> Dict[str, Any]:
        """Test compat package exports legacy functions."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from governance.compat import governance_query_rules, dsm_start, session_start"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "stderr": result.stderr if result.returncode != 0 else None
        }

    def mcp_config_has_4_servers(self) -> Dict[str, Any]:
        """Check MCP config has 4 split servers."""
        mcp_config = PROJECT_ROOT / ".mcp.json"
        with open(mcp_config) as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})
        expected = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]

        results = {
            "has_all": all(s in servers for s in expected),
            "missing": [s for s in expected if s not in servers],
            "has_deprecated_monolith": "governance" in servers
        }
        return results

    def each_server_has_required_fields(self) -> Dict[str, Any]:
        """Check each server config has required fields."""
        mcp_config = PROJECT_ROOT / ".mcp.json"
        with open(mcp_config) as f:
            config = json.load(f)

        governance_servers = ["gov-core", "gov-agents", "gov-sessions", "gov-tasks"]
        results = {"all_valid": True, "issues": []}

        required_fields = ["type", "command", "args", "env"]
        required_env = ["TYPEDB_HOST", "TYPEDB_PORT"]

        for name in governance_servers:
            server = config.get("mcpServers", {}).get(name)
            if server is None:
                results["issues"].append(f"{name} not defined")
                results["all_valid"] = False
                continue

            for field in required_fields:
                if field not in server:
                    results["issues"].append(f"{name} missing '{field}'")
                    results["all_valid"] = False

            if "env" in server:
                for env_var in required_env:
                    if env_var not in server["env"]:
                        results["issues"].append(f"{name} missing {env_var}")
                        results["all_valid"] = False

        return results

    def orchestrator_file_under_limit(self, filename: str, limit: int = 50) -> Dict[str, Any]:
        """Check orchestrator file is under line limit."""
        filepath = MCP_TOOLS_DIR / filename
        if not filepath.exists():
            return {"exists": False, "lines": -1}
        content = filepath.read_text()
        lines = len(content.splitlines())
        return {
            "exists": True,
            "lines": lines,
            "under_limit": lines < limit
        }

    def split_modules_exist(self) -> Dict[str, Any]:
        """Check split module files exist."""
        expected_files = [
            "rules_query.py", "rules_crud.py", "rules_archive.py",
            "sessions_core.py", "sessions_linking.py",
            "tasks_crud.py", "tasks_linking.py"
        ]
        results = {"all_exist": True, "missing": []}

        for filename in expected_files:
            if not (MCP_TOOLS_DIR / filename).exists():
                results["missing"].append(filename)
                results["all_exist"] = False

        return results

    def split_modules_under_315_lines(self) -> Dict[str, Any]:
        """Check split modules are under 315 lines."""
        modules = [
            "rules_query.py", "rules_crud.py", "rules_archive.py",
            "sessions_core.py", "sessions_linking.py",
            "tasks_crud.py", "tasks_linking.py"
        ]
        results = {"all_under_limit": True, "over_limit": []}

        for filename in modules:
            filepath = MCP_TOOLS_DIR / filename
            if filepath.exists():
                content = filepath.read_text()
                lines = len(content.splitlines())
                if lines > 315:
                    results["over_limit"].append({"file": filename, "lines": lines})
                    results["all_under_limit"] = False

        return results
