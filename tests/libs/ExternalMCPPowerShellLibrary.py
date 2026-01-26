"""
Robot Framework Library for External MCP PowerShell Tools Tests.

Per: RULE-007 (MCP Tool Matrix), DOC-SIZE-01-v1.
Split from tests/test_external_mcp_tools.py
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


class ExternalMCPPowerShellLibrary:
    """Library for PowerShell tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # PowerShellConfig Tests
    # =========================================================================

    @keyword("PowerShell Default Config")
    def powershell_default_config(self):
        """Test default configuration values."""
        try:
            from agent.external_mcp_tools import PowerShellConfig
            config = PowerShellConfig()
            return {
                "timeout_300": config.timeout == 300,
                "working_directory_none": config.working_directory is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("PowerShell Custom Config")
    def powershell_custom_config(self):
        """Test custom configuration."""
        try:
            from agent.external_mcp_tools import PowerShellConfig
            config = PowerShellConfig(timeout=600, working_directory="C:\\Scripts")
            return {
                "timeout_600": config.timeout == 600,
                "working_directory_correct": config.working_directory == "C:\\Scripts"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # PowerShellTools Tests
    # =========================================================================

    @keyword("PowerShell Toolkit Creation")
    def powershell_toolkit_creation(self):
        """Test toolkit can be created."""
        try:
            from agent.external_mcp_tools import PowerShellTools
            tools = PowerShellTools()
            return {
                "name_correct": tools.name == "powershell"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("PowerShell Tool Registration")
    def powershell_tool_registration(self):
        """Test all tools are registered."""
        try:
            from agent.external_mcp_tools import PowerShellTools
            tools = PowerShellTools()
            return {
                "run_script_registered": "run_script" in tools.functions,
                "run_command_registered": "run_command" in tools.functions
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("PowerShell Run Script Tool")
    def powershell_run_script_tool(self):
        """Test run_script tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PowerShellTools
            tools = PowerShellTools()
            code = "Get-Process | Select-Object -First 5"
            result = call_tool(tools, 'run_script', code=code)
            parsed = json.loads(result)
            return {
                "action_run_script": parsed["action"] == "run_script",
                "code_length_correct": parsed["code_length"] == len(code),
                "timeout_default": parsed["timeout"] == 300
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("PowerShell Run Script With Timeout")
    def powershell_run_script_with_timeout(self):
        """Test run_script with custom timeout."""
        try:
            from agent.external_mcp_tools import PowerShellTools
            tools = PowerShellTools()
            result = call_tool(tools, 'run_script', code="Get-Date", timeout=60)
            parsed = json.loads(result)
            return {
                "timeout_custom": parsed["timeout"] == 60
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("PowerShell Run Command Tool")
    def powershell_run_command_tool(self):
        """Test run_command wraps run_script."""
        try:
            from agent.external_mcp_tools import PowerShellTools
            tools = PowerShellTools()
            result = call_tool(tools, 'run_command', command="Get-Location")
            parsed = json.loads(result)
            return {
                "action_run_script": parsed["action"] == "run_script"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
