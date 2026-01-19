"""Test Data Factories for Enterprise-Grade Testing.

Per DOC-SIZE-01-v1: Modular test data factories.
Per DRY principles: Reusable test object builders.

Usage:
    from tests.factories import MCPTestDataFactory, TOONOutputFactory

    # Create test data
    data = MCPTestDataFactory.rules_query_result()

    # Create expected TOON output
    expected = TOONOutputFactory.format_expected(data)
"""

from tests.factories.mcp_data import MCPTestDataFactory
from tests.factories.toon_output import TOONOutputFactory

__all__ = ["MCPTestDataFactory", "TOONOutputFactory"]
