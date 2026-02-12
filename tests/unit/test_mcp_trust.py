"""
Unit tests for Trust Score MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/trust.py module.
Tests: register_trust_tools (governance_get_trust_score, agent_trust_score).
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.trust import register_trust_tools


def _json_format(data, **kwargs):
    """Force JSON output for test assertions."""
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    """Captures tools registered via @mcp.tool()."""

    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_trust_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json():
    with patch(
        "governance.mcp_tools.trust.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    """Tests for tool registration."""

    def test_registers_governance_get_trust_score(self):
        mcp = _register()
        assert "governance_get_trust_score" in mcp.tools

    def test_registers_agent_trust_score_alias(self):
        mcp = _register()
        assert "agent_trust_score" in mcp.tools

    def test_total_tools(self):
        mcp = _register()
        assert len(mcp.tools) == 2


# ---------------------------------------------------------------------------
# governance_get_trust_score
# ---------------------------------------------------------------------------
class TestGetTrustScore:
    """Tests for governance_get_trust_score tool."""

    def test_connection_failure(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            mcp = _register()
            result = json.loads(mcp.tools["governance_get_trust_score"]("AGENT-001"))
            assert "error" in result
            assert "connect" in result["error"].lower()

    def test_agent_not_found(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = []
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            mcp = _register()
            result = json.loads(mcp.tools["governance_get_trust_score"]("AGENT-999"))
            assert "error" in result
            assert "not found" in result["error"]

    def test_returns_trust_score(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = [{
            "name": "Test Agent",
            "trust": 0.85,
            "compliance": 0.90,
            "accuracy": 0.80,
            "tenure": 30,
        }]
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            with patch("governance.mcp_tools.trust.log_monitor_event"):
                mcp = _register()
                result = json.loads(mcp.tools["governance_get_trust_score"]("AGENT-001"))
                assert result["agent_id"] == "AGENT-001"
                assert result["trust_score"] == 0.85
                assert result["compliance_rate"] == 0.90

    def test_client_closed_after_query(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = [{
            "name": "A", "trust": 0.5, "compliance": 0.5,
            "accuracy": 0.5, "tenure": 10,
        }]
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            with patch("governance.mcp_tools.trust.log_monitor_event"):
                mcp = _register()
                mcp.tools["governance_get_trust_score"]("AGENT-001")
                mock_client.close.assert_called_once()

    def test_client_closed_on_failure(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            mcp = _register()
            mcp.tools["governance_get_trust_score"]("AGENT-001")
            mock_client.close.assert_called_once()

    def test_alias_delegates(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = [{
            "name": "A", "trust": 0.7, "compliance": 0.7,
            "accuracy": 0.7, "tenure": 5,
        }]
        with patch("governance.mcp_tools.trust.get_typedb_client", return_value=mock_client):
            with patch("governance.mcp_tools.trust.log_monitor_event"):
                mcp = _register()
                r1 = mcp.tools["governance_get_trust_score"]("AGENT-001")
                r2 = mcp.tools["agent_trust_score"]("AGENT-001")
                # Both should succeed (alias calls the same function)
                assert json.loads(r1)["agent_id"] == "AGENT-001"
