"""
Unit tests for PowerShell MCP Tools.

Per DOC-SIZE-01-v1: Tests for agent/external_mcp/powershell.py module.
Tests: PowerShellConfig, PowerShellTools — run_script, run_command.
"""

import json

from agent.external_mcp.powershell import PowerShellConfig, PowerShellTools


def _call(tools, method_name, *args, **kwargs):
    """Call an agno-wrapped tool method via its entrypoint."""
    fn = getattr(tools, method_name)
    if hasattr(fn, "entrypoint"):
        return fn.entrypoint(tools, *args, **kwargs)
    return fn(*args, **kwargs)


# ── PowerShellConfig ───────────────────────────────────────


class TestPowerShellConfig:
    def test_defaults(self):
        cfg = PowerShellConfig()
        assert cfg.timeout == 300
        assert cfg.working_directory is None

    def test_custom(self):
        cfg = PowerShellConfig(timeout=60, working_directory="/tmp")
        assert cfg.timeout == 60
        assert cfg.working_directory == "/tmp"


# ── PowerShellTools init ──────────────────────────────────


class TestPowerShellToolsInit:
    def test_default_config(self):
        tools = PowerShellTools()
        assert tools.name == "powershell"
        assert tools.config.timeout == 300

    def test_custom_config(self):
        cfg = PowerShellConfig(timeout=120)
        tools = PowerShellTools(config=cfg)
        assert tools.config.timeout == 120

    def test_registers_two_tools(self):
        tools = PowerShellTools()
        assert len(tools.functions) == 2
        assert set(tools.functions.keys()) == {"run_script", "run_command"}


# ── run_script ─────────────────────────────────────────────


class TestRunScript:
    def test_basic(self):
        tools = PowerShellTools()
        result = json.loads(_call(tools, "run_script", "Get-Process"))
        assert result["action"] == "run_script"
        assert result["code_length"] == len("Get-Process")
        assert result["status"] == "simulated"

    def test_default_timeout(self):
        tools = PowerShellTools()
        result = json.loads(_call(tools, "run_script", "cmd"))
        assert result["timeout"] == 300

    def test_custom_timeout(self):
        tools = PowerShellTools()
        result = json.loads(_call(tools, "run_script", "cmd", timeout=60))
        assert result["timeout"] == 60

    def test_config_timeout_used(self):
        cfg = PowerShellConfig(timeout=120)
        tools = PowerShellTools(config=cfg)
        result = json.loads(_call(tools, "run_script", "cmd"))
        assert result["timeout"] == 120


# ── run_command ────────────────────────────────────────────


class TestRunCommand:
    def test_basic(self):
        tools = PowerShellTools()
        result = json.loads(_call(tools, "run_command", "dir"))
        assert result["action"] == "run_script"
        assert result["code_length"] == 3
        assert result["status"] == "simulated"

    def test_uses_config_timeout(self):
        cfg = PowerShellConfig(timeout=45)
        tools = PowerShellTools(config=cfg)
        result = json.loads(_call(tools, "run_command", "ls"))
        assert result["timeout"] == 45
