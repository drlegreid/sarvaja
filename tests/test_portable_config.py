"""
Tests for RULE-040: Portable Configuration Patterns
Validates EOL, paths, and wrapper script patterns.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestPortableConfig:
    """Tests for portable configuration patterns per RULE-040."""

    def test_scripts_have_lf_line_endings(self):
        """All shell scripts must have LF (Unix) line endings."""
        scripts_dir = PROJECT_ROOT / "scripts"
        if not scripts_dir.exists():
            pytest.skip("No scripts directory")

        crlf_files = []
        for script in scripts_dir.glob("*.sh"):
            content = script.read_bytes()
            if b"\r\n" in content:
                crlf_files.append(script.name)

        assert not crlf_files, f"Scripts with CRLF line endings: {crlf_files}"

    def test_mcp_config_no_absolute_home_paths(self):
        """MCP config must not contain hardcoded home paths."""
        mcp_json = PROJECT_ROOT / ".mcp.json"
        if not mcp_json.exists():
            pytest.skip("No .mcp.json found")

        content = mcp_json.read_text()

        # Check for hardcoded home paths
        assert "/home/" not in content or "${" in content, \
            "Hardcoded /home/ paths found in .mcp.json"
        assert "C:\\Users" not in content, \
            "Hardcoded Windows paths found in .mcp.json"

    def test_mcp_runner_script_exists(self):
        """MCP runner wrapper script must exist."""
        runner = PROJECT_ROOT / "scripts" / "mcp-runner.sh"
        assert runner.exists(), "scripts/mcp-runner.sh missing"

    def test_mcp_runner_uses_home_variable(self):
        """MCP runner must use $HOME not hardcoded path."""
        runner = PROJECT_ROOT / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            pytest.skip("No mcp-runner.sh")

        content = runner.read_text()
        assert "$HOME" in content, "mcp-runner.sh should use $HOME"

    def test_mcp_runner_sets_pythonpath(self):
        """MCP runner must set PYTHONPATH."""
        runner = PROJECT_ROOT / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            pytest.skip("No mcp-runner.sh")

        content = runner.read_text()
        assert "PYTHONPATH" in content, "mcp-runner.sh should set PYTHONPATH"

    def test_mcp_config_uses_workspace_folder(self):
        """MCP config should use ${workspaceFolder} for portability."""
        mcp_json = PROJECT_ROOT / ".mcp.json"
        if not mcp_json.exists():
            pytest.skip("No .mcp.json found")

        content = mcp_json.read_text()
        assert "${workspaceFolder}" in content, \
            "MCP config should use ${workspaceFolder}"


class TestVenvPortability:
    """Tests for virtual environment portability."""

    def test_venv_activation_conditional(self):
        """Wrapper scripts should conditionally activate venv."""
        runner = PROJECT_ROOT / "scripts" / "mcp-runner.sh"
        if not runner.exists():
            pytest.skip("No mcp-runner.sh")

        content = runner.read_text()
        # Should check if venv exists before activating
        assert "if" in content or "&&" in content, \
            "Script should conditionally activate venv"
