"""
External MCP → Agno @tool Wrappers Package
==========================================
Wraps external MCP tools (Playwright, PowerShell, Desktop Commander, OctoCode)
as Agno @tool functions for direct agent use.

**Refactored: 2024-12-28 per GAP-FILE-011**
Original: 791 lines -> Package with 6 modules (~600 lines total)

Pattern per RULE-017 (Cross-Workspace Pattern Reuse).
Per RULE-007 (MCP Tool Matrix).

Usage:
    from agent.external_mcp import (
        PlaywrightTools,
        PowerShellTools,
        DesktopCommanderTools,
        OctoCodeTools
    )

    agent = Agent(tools=[PlaywrightTools(), PowerShellTools()], ...)

Created: 2024-12-24 (Phase 5)
Refactored: 2024-12-28 (GAP-FILE-011)
Per: R&D-BACKLOG.md, CROSS-WORKSPACE-WISDOM.md
"""

# Common utilities
from .common import tool, Toolkit, AGNO_AVAILABLE

# Tool configs
from .playwright import PlaywrightConfig, PlaywrightTools
from .powershell import PowerShellConfig, PowerShellTools
from .desktop_commander import DesktopCommanderConfig, DesktopCommanderTools
from .octocode import OctoCodeConfig, OctoCodeTools

# Combined toolkit and factory functions
from .combined import (
    ExternalMCPTools,
    get_all_external_tools,
    get_web_automation_tools,
    get_devops_tools,
    get_file_tools,
    get_code_research_tools,
)

__all__ = [
    # Common
    "tool",
    "Toolkit",
    "AGNO_AVAILABLE",
    # Configs
    "PlaywrightConfig",
    "PowerShellConfig",
    "DesktopCommanderConfig",
    "OctoCodeConfig",
    # Tool classes
    "PlaywrightTools",
    "PowerShellTools",
    "DesktopCommanderTools",
    "OctoCodeTools",
    # Combined
    "ExternalMCPTools",
    # Factory functions
    "get_all_external_tools",
    "get_web_automation_tools",
    "get_devops_tools",
    "get_file_tools",
    "get_code_research_tools",
]
