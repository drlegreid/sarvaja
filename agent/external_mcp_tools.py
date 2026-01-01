"""
External MCP → Agno @tool Wrappers - Phase 5 Integration
=========================================================
Wraps external MCP tools (Playwright, PowerShell, Desktop Commander, OctoCode)
as Agno @tool functions for direct agent use.

**Refactored: 2024-12-28 per GAP-FILE-011**
Original: 791 lines -> Package with 6 modules (~600 lines total)

Pattern per RULE-017 (Cross-Workspace Pattern Reuse).
Per RULE-007 (MCP Tool Matrix).

Usage:
    from agent.external_mcp_tools import (
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

# =============================================================================
# RE-EXPORTS FROM PACKAGE (Backward Compatibility)
# =============================================================================

from agent.external_mcp import (
    # Common utilities
    tool,
    Toolkit,
    AGNO_AVAILABLE,
    # Configs
    PlaywrightConfig,
    PowerShellConfig,
    DesktopCommanderConfig,
    OctoCodeConfig,
    # Tool classes
    PlaywrightTools,
    PowerShellTools,
    DesktopCommanderTools,
    OctoCodeTools,
    # Combined toolkit
    ExternalMCPTools,
    # Factory functions
    get_all_external_tools,
    get_web_automation_tools,
    get_devops_tools,
    get_file_tools,
    get_code_research_tools,
)

# =============================================================================
# PUBLIC API
# =============================================================================

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

# =============================================================================
# CLI / TESTING
# =============================================================================

if __name__ == "__main__":
    print("External MCP Tools Package (Refactored)")
    print("=" * 50)
    print(f"AGNO_AVAILABLE: {AGNO_AVAILABLE}")
    print()

    # Validate all toolkits
    toolkits = [
        ("Playwright", PlaywrightTools),
        ("PowerShell", PowerShellTools),
        ("Desktop Commander", DesktopCommanderTools),
        ("OctoCode", OctoCodeTools),
    ]

    for name, cls in toolkits:
        toolkit = cls()
        print(f"{name}: {len(toolkit.functions)} tools")
        for tool_name in toolkit.functions:
            print(f"  - {tool_name}")

    print()
    print("Combined toolkit:")
    combined = ExternalMCPTools()
    print(f"  Enabled: {combined.enabled_toolkits}")
    print(f"  Total tools: {len(combined.functions)}")
