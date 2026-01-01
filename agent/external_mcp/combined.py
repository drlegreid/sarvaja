"""
Combined External MCP Toolkit
=============================
Aggregates all external MCP tools into a single toolkit.

Per RULE-007: MCP Tool Matrix
Per GAP-FILE-011: Extracted from external_mcp_tools.py

Created: 2024-12-28
"""

from typing import List

from .common import Toolkit
from .playwright import PlaywrightTools
from .powershell import PowerShellTools
from .desktop_commander import DesktopCommanderTools
from .octocode import OctoCodeTools


class ExternalMCPTools(Toolkit):
    """
    Combined toolkit providing all external MCP tools.

    Aggregates Playwright, PowerShell, Desktop Commander, and OctoCode tools.

    Usage:
        from agent.external_mcp import ExternalMCPTools

        tools = ExternalMCPTools()
        agent = Agent(tools=[tools], ...)
    """

    def __init__(
        self,
        enable_playwright: bool = True,
        enable_powershell: bool = True,
        enable_desktop_commander: bool = True,
        enable_octocode: bool = True
    ):
        super().__init__(name="external_mcp")

        # Initialize enabled toolkits
        self._toolkits = []

        if enable_playwright:
            self._toolkits.append(PlaywrightTools())
        if enable_powershell:
            self._toolkits.append(PowerShellTools())
        if enable_desktop_commander:
            self._toolkits.append(DesktopCommanderTools())
        if enable_octocode:
            self._toolkits.append(OctoCodeTools())

        # Register all tools from sub-toolkits
        for toolkit in self._toolkits:
            for name, func in toolkit.functions.items():
                prefixed_name = f"{toolkit.name}_{name}"
                self.functions[prefixed_name] = func

    @property
    def enabled_toolkits(self) -> List[str]:
        """Get list of enabled toolkit names."""
        return [t.name for t in self._toolkits]


def get_all_external_tools() -> List[Toolkit]:
    """Get all external MCP toolkits as a list."""
    return [
        PlaywrightTools(),
        PowerShellTools(),
        DesktopCommanderTools(),
        OctoCodeTools()
    ]


def get_web_automation_tools() -> PlaywrightTools:
    """Get Playwright tools for web automation."""
    return PlaywrightTools()


def get_devops_tools() -> PowerShellTools:
    """Get PowerShell tools for DevOps."""
    return PowerShellTools()


def get_file_tools() -> DesktopCommanderTools:
    """Get Desktop Commander tools for file operations."""
    return DesktopCommanderTools()


def get_code_research_tools() -> OctoCodeTools:
    """Get OctoCode tools for code research."""
    return OctoCodeTools()
