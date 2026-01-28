"""
Rules Test Fixtures
===================
Shared fixtures for rules tests.
Per DOC-SIZE-01-v1: Split from test_rules_crud.py (838 lines)
"""

import os
import pytest
from unittest.mock import Mock

from governance.client import TypeDBClient, Rule


@pytest.fixture(autouse=True)
def mcp_json_format():
    """Force JSON output format for MCP tools during tests.

    Per GAP-DATA-001: MCP_OUTPUT_FORMAT controls output format.
    Tests expect JSON, so we set this explicitly.
    """
    old_value = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old_value is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old_value


@pytest.fixture
def sample_rule():
    """Sample rule for testing."""
    return Rule(
        id="RULE-TEST-001",
        name="Test Rule",
        category="testing",
        priority="MEDIUM",
        status="DRAFT",
        directive="This is a test rule directive."
    )


@pytest.fixture
def sample_rule_data():
    """Sample rule data dict for testing."""
    return {
        "rule_id": "RULE-TEST-002",
        "name": "Another Test Rule",
        "category": "governance",
        "priority": "HIGH",
        "directive": "Another test directive.",
        "status": "DRAFT"
    }


@pytest.fixture
def mock_client():
    """Create a mock TypeDBClient for testing."""
    client = Mock(spec=TypeDBClient)
    client.connect.return_value = True
    client.close.return_value = None
    client.is_connected.return_value = True
    return client
