"""
External MCP Common Utilities
=============================
Shared imports and stubs for external MCP tools.

Per RULE-007: MCP Tool Matrix
Per GAP-FILE-011: Extracted from external_mcp_tools.py

Created: 2024-12-28
"""

# Import Agno tools (available in container, may not be locally)
try:
    from agno.tools import tool, Toolkit
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

    # Create stubs for local testing
    def tool(func):
        """Stub @tool decorator when agno not available."""
        func._is_tool = True
        return func

    class Toolkit:
        """Stub Toolkit class when agno not available."""
        def __init__(self, name: str = ""):
            self.name = name
            self.functions = {}

        def register(self, func):
            """Register a function as a tool."""
            self.functions[func.__name__] = func


__all__ = ["tool", "Toolkit", "AGNO_AVAILABLE"]
