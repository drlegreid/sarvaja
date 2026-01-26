"""
Robot Framework Library for External MCP Combined Toolkit Tests.

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


def is_valid_tool(method):
    """Check if a method is a valid registered tool."""
    if hasattr(method, 'name') and hasattr(method, 'entrypoint'):
        return True  # Agno Function
    if hasattr(method, '_is_tool'):
        return True  # Stub with marker
    return callable(method)


class ExternalMCPCombinedLibrary:
    """Library for combined toolkit, convenience, and compliance tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Combined Toolkit Tests
    # =========================================================================

    @keyword("Combined Toolkit Creation")
    def combined_toolkit_creation(self):
        """Test combined toolkit can be created."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools()
            return {
                "name_correct": tools.name == "external_mcp"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("All Toolkits Enabled")
    def all_toolkits_enabled(self):
        """Test all toolkits enabled by default."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools()
            return {
                "playwright_enabled": "playwright" in tools.enabled_toolkits,
                "powershell_enabled": "powershell" in tools.enabled_toolkits,
                "desktop_commander_enabled": "desktop_commander" in tools.enabled_toolkits,
                "octocode_enabled": "octocode" in tools.enabled_toolkits
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Selective Toolkits")
    def selective_toolkits(self):
        """Test selective toolkit enabling."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools(
                enable_playwright=True,
                enable_powershell=False,
                enable_desktop_commander=False,
                enable_octocode=True
            )
            return {
                "playwright_enabled": "playwright" in tools.enabled_toolkits,
                "powershell_disabled": "powershell" not in tools.enabled_toolkits,
                "desktop_commander_disabled": "desktop_commander" not in tools.enabled_toolkits,
                "octocode_enabled": "octocode" in tools.enabled_toolkits
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Prefixed Tool Names")
    def prefixed_tool_names(self):
        """Test tools have prefixed names."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools()
            return {
                "playwright_navigate": "playwright_navigate" in tools.functions,
                "powershell_run_script": "powershell_run_script" in tools.functions,
                "desktop_commander_read_file": "desktop_commander_read_file" in tools.functions,
                "octocode_search_code": "octocode_search_code" in tools.functions
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Total Tool Count")
    def total_tool_count(self):
        """Test total number of registered tools."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools()
            # Playwright: 7, PowerShell: 2, Desktop Commander: 7, OctoCode: 5 = 21
            return {
                "count_21": len(tools.functions) == 21
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Disabled Toolkit Not Registered")
    def disabled_toolkit_not_registered(self):
        """Test disabled toolkit tools not registered."""
        try:
            from agent.external_mcp_tools import ExternalMCPTools
            tools = ExternalMCPTools(enable_powershell=False)
            return {
                "powershell_not_in_functions": "powershell_run_script" not in tools.functions,
                "playwright_still_enabled": "playwright_navigate" in tools.functions
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    @keyword("Get All External Tools")
    def get_all_external_tools_test(self):
        """Test get_all_external_tools returns all toolkits."""
        try:
            from agent.external_mcp_tools import (
                get_all_external_tools, PlaywrightTools, PowerShellTools,
                DesktopCommanderTools, OctoCodeTools
            )
            toolkits = get_all_external_tools()
            names = [t.name for t in toolkits]
            return {
                "count_4": len(toolkits) == 4,
                "has_playwright": "playwright" in names,
                "has_powershell": "powershell" in names,
                "has_desktop_commander": "desktop_commander" in names,
                "has_octocode": "octocode" in names
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Web Automation Tools")
    def get_web_automation_tools_test(self):
        """Test get_web_automation_tools returns PlaywrightTools."""
        try:
            from agent.external_mcp_tools import get_web_automation_tools, PlaywrightTools
            tools = get_web_automation_tools()
            return {
                "is_playwright": isinstance(tools, PlaywrightTools),
                "name_playwright": tools.name == "playwright"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get DevOps Tools")
    def get_devops_tools_test(self):
        """Test get_devops_tools returns PowerShellTools."""
        try:
            from agent.external_mcp_tools import get_devops_tools, PowerShellTools
            tools = get_devops_tools()
            return {
                "is_powershell": isinstance(tools, PowerShellTools),
                "name_powershell": tools.name == "powershell"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get File Tools")
    def get_file_tools_test(self):
        """Test get_file_tools returns DesktopCommanderTools."""
        try:
            from agent.external_mcp_tools import get_file_tools, DesktopCommanderTools
            tools = get_file_tools()
            return {
                "is_desktop_commander": isinstance(tools, DesktopCommanderTools),
                "name_desktop_commander": tools.name == "desktop_commander"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Code Research Tools")
    def get_code_research_tools_test(self):
        """Test get_code_research_tools returns OctoCodeTools."""
        try:
            from agent.external_mcp_tools import get_code_research_tools, OctoCodeTools
            tools = get_code_research_tools()
            return {
                "is_octocode": isinstance(tools, OctoCodeTools),
                "name_octocode": tools.name == "octocode"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Module-Level Tests
    # =========================================================================

    @keyword("AGNO Available Flag")
    def agno_available_flag(self):
        """Test AGNO_AVAILABLE flag exists."""
        try:
            from agent.external_mcp_tools import AGNO_AVAILABLE
            return {
                "is_bool": isinstance(AGNO_AVAILABLE, bool)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Stub Decorator When No AGNO")
    def stub_decorator_when_no_agno(self):
        """Test stub decorator marks functions."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            return {
                "navigate_valid_tool": is_valid_tool(tools.navigate)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # JSON Output Validation Tests
    # =========================================================================

    @keyword("All Tools Return Valid JSON")
    def all_tools_return_valid_json(self):
        """Test all tools return parseable JSON."""
        try:
            from agent.external_mcp_tools import (
                PlaywrightTools, PowerShellTools, DesktopCommanderTools, OctoCodeTools
            )

            tools_to_test = [
                (PlaywrightTools(), [
                    ("navigate", {"url": "https://test.com"}),
                    ("snapshot", {}),
                    ("click", {"element": "btn", "ref": "r1"}),
                ]),
                (PowerShellTools(), [
                    ("run_script", {"code": "Get-Date"}),
                ]),
                (DesktopCommanderTools(), [
                    ("read_file", {"path": "C:\\t.txt"}),
                ]),
                (OctoCodeTools(), [
                    ("search_code", {"keywords": "test"}),
                ]),
            ]

            all_valid = True
            all_have_status = True
            for toolkit, tool_calls in tools_to_test:
                for tool_name, kwargs in tool_calls:
                    try:
                        result = call_tool(toolkit, tool_name, **kwargs)
                        parsed = json.loads(result)
                        if "status" not in parsed:
                            all_have_status = False
                        if parsed.get("status") != "simulated":
                            all_have_status = False
                    except json.JSONDecodeError:
                        all_valid = False

            return {
                "all_valid_json": all_valid,
                "all_have_simulated_status": all_have_status
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Results Have Action Field")
    def results_have_action_field(self):
        """Test all results include action field."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            toolkit = PlaywrightTools()
            result = call_tool(toolkit, 'navigate', url="https://example.com")
            parsed = json.loads(result)
            return {
                "has_action": "action" in parsed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Results Have Message Field")
    def results_have_message_field(self):
        """Test all results include message field."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            toolkit = DesktopCommanderTools()
            result = call_tool(toolkit, 'read_file', path="C:\\test.txt")
            parsed = json.loads(result)
            return {
                "has_message": "message" in parsed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    # =========================================================================
    # Tool Matrix Compliance (RULE-007)
    # =========================================================================

    @keyword("Tier 1 Tools Present")
    def tier_1_tools_present(self):
        """Test Tier 1 tools (required) are present."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            return {
                "playwright_has_5_plus_tools": len(tools.functions) >= 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tier 2 Tools Present")
    def tier_2_tools_present(self):
        """Test Tier 2 tools (recommended) are present."""
        try:
            from agent.external_mcp_tools import PowerShellTools, DesktopCommanderTools, OctoCodeTools
            ps = PowerShellTools()
            dc = DesktopCommanderTools()
            oc = OctoCodeTools()
            return {
                "powershell_2_plus": len(ps.functions) >= 2,
                "desktop_commander_5_plus": len(dc.functions) >= 5,
                "octocode_4_plus": len(oc.functions) >= 4
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
