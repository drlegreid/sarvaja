"""
Robot Framework Library for MCP Tools Tests.

Per P4.1: MCP → Agno @tool Wrapper.
Migrated from tests/test_mcp_tools.py

REFACTORED per DOC-SIZE-01-v1: This file is now a facade that imports from:
- MCPToolsUnitLibrary.py (Unit tests, method existence, return format)
- MCPToolsHealthLibrary.py (Health check, vote weight calculation)
"""

from MCPToolsUnitLibrary import MCPToolsUnitLibrary
from MCPToolsHealthLibrary import MCPToolsHealthLibrary


class MCPToolsLibrary(
    MCPToolsUnitLibrary,
    MCPToolsHealthLibrary
):
    """
    Facade library combining all MCP Tools test modules.

    Inherits from:
    - MCPToolsUnitLibrary: GovernanceTools class, methods, return format
    - MCPToolsHealthLibrary: Health check patterns, vote weight calculation

    Use individual libraries for focused tests or this facade for full coverage.
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
