"""
Robot Framework library for Portable Configuration tests.

Per RULE-040: Portable Configuration Patterns
Migrated from tests/test_portable_config.py
"""

from pathlib import Path
from robot.api.deco import keyword


class PortableConfigLibrary:
    """Library for testing portable configuration patterns."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Shell Script Tests
    # =========================================================================

    @keyword("Scripts Have LF Line Endings")
    def scripts_have_lf_line_endings(self):
        """All shell scripts must have LF (Unix) line endings."""
        scripts_dir = self.project_root / "scripts"
        if not scripts_dir.exists():
            return {"skipped": True, "reason": "No scripts directory"}

        crlf_files = []
        for script in scripts_dir.glob("*.sh"):
            content = script.read_bytes()
            if b"\r\n" in content:
                crlf_files.append(script.name)

        return {
            "no_crlf": len(crlf_files) == 0,
            "crlf_files": crlf_files
        }

    # =========================================================================
    # MCP Config Tests
    # =========================================================================

    @keyword("MCP Config No Absolute Home Paths")
    def mcp_config_no_absolute_home_paths(self):
        """MCP config must not contain hardcoded home paths."""
        mcp_json = self.project_root / ".mcp.json"
        if not mcp_json.exists():
            return {"skipped": True, "reason": "No .mcp.json found"}

        content = mcp_json.read_text()

        no_hardcoded_linux = "/home/" not in content or "${" in content
        no_hardcoded_windows = "C:\\Users" not in content

        return {
            "no_linux_paths": no_hardcoded_linux,
            "no_windows_paths": no_hardcoded_windows
        }

    @keyword("MCP Runner Script Exists")
    def mcp_runner_script_exists(self):
        """MCP runner wrapper script must exist."""
        runner = self.project_root / "scripts" / "mcp-runner.sh"
        return {"exists": runner.exists()}

    @keyword("MCP Runner Uses Home Variable")
    def mcp_runner_uses_home_variable(self):
        """MCP runner must use $HOME not hardcoded path."""
        runner = self.project_root / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            return {"skipped": True, "reason": "No mcp-runner.sh"}

        content = runner.read_text()
        return {"uses_home": "$HOME" in content}

    @keyword("MCP Runner Sets PYTHONPATH")
    def mcp_runner_sets_pythonpath(self):
        """MCP runner must set PYTHONPATH."""
        runner = self.project_root / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            return {"skipped": True, "reason": "No mcp-runner.sh"}

        content = runner.read_text()
        return {"sets_pythonpath": "PYTHONPATH" in content}

    @keyword("MCP Config Uses Workspace Folder")
    def mcp_config_uses_workspace_folder(self):
        """MCP config should use ${workspaceFolder} for portability."""
        mcp_json = self.project_root / ".mcp.json"
        if not mcp_json.exists():
            return {"skipped": True, "reason": "No .mcp.json found"}

        content = mcp_json.read_text()
        return {"uses_workspace_folder": "${workspaceFolder}" in content}

    # =========================================================================
    # Venv Portability Tests
    # =========================================================================

    @keyword("Venv Activation Conditional")
    def venv_activation_conditional(self):
        """Wrapper scripts should conditionally activate venv."""
        runner = self.project_root / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            return {"skipped": True, "reason": "No mcp-runner.sh"}

        content = runner.read_text()
        return {
            "conditional": "if" in content or "&&" in content
        }
