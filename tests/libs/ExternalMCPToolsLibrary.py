"""
Robot Framework Library for External MCP Tools Tests.

Per: RULE-007 (MCP Tool Matrix), DOC-SIZE-01-v1.
Migrated from tests/test_external_mcp_tools.py

REFACTORED per DOC-SIZE-01-v1: This file is a facade that imports from:
- ExternalMCPPlaywrightLibrary.py (Playwright config + tools tests)
- ExternalMCPPowerShellLibrary.py (PowerShell config + tools tests)
- ExternalMCPDesktopCommanderLibrary.py (Desktop Commander config + tools tests)
- ExternalMCPOctoCodeLibrary.py (OctoCode config + tools tests)
- ExternalMCPCombinedLibrary.py (Combined toolkit, convenience, JSON, compliance)
"""

from ExternalMCPPlaywrightLibrary import ExternalMCPPlaywrightLibrary
from ExternalMCPPowerShellLibrary import ExternalMCPPowerShellLibrary
from ExternalMCPDesktopCommanderLibrary import ExternalMCPDesktopCommanderLibrary
from ExternalMCPOctoCodeLibrary import ExternalMCPOctoCodeLibrary
from ExternalMCPCombinedLibrary import ExternalMCPCombinedLibrary


class ExternalMCPToolsLibrary(
    ExternalMCPPlaywrightLibrary,
    ExternalMCPPowerShellLibrary,
    ExternalMCPDesktopCommanderLibrary,
    ExternalMCPOctoCodeLibrary,
    ExternalMCPCombinedLibrary
):
    """
    Facade library combining all External MCP Tools test modules.

    Inherits from:
    - ExternalMCPPlaywrightLibrary: Playwright web automation tools
    - ExternalMCPPowerShellLibrary: PowerShell DevOps tools
    - ExternalMCPDesktopCommanderLibrary: Desktop Commander file tools
    - ExternalMCPOctoCodeLibrary: OctoCode GitHub research tools
    - ExternalMCPCombinedLibrary: Combined toolkit + compliance tests

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
