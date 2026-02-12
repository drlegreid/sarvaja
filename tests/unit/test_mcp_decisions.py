"""
Unit tests for Decision MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/decisions.py module.
Tests: governance_get_decision_impacts, governance_health, _detect_document_entropy.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.decisions import (
    register_decision_tools,
    _detect_document_entropy,
)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _json_format():
    with patch("governance.mcp_tools.decisions.format_mcp_result",
               side_effect=lambda x: json.dumps(x)):
        yield


class TestDecisionImpacts:
    def test_success(self):
        mcp = _CaptureMCP()
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_decision_impacts.return_value = ["RULE-001", "RULE-002"]

        with patch("governance.mcp_tools.decisions.get_typedb_client",
                   return_value=mock_client):
            register_decision_tools(mcp)
            result = json.loads(mcp.tools["governance_get_decision_impacts"]("DEC-001"))
            assert "RULE-001" in result

    def test_connection_failure(self):
        mcp = _CaptureMCP()
        mock_client = MagicMock()
        mock_client.connect.return_value = False

        with patch("governance.mcp_tools.decisions.get_typedb_client",
                   return_value=mock_client):
            register_decision_tools(mcp)
            result = json.loads(mcp.tools["governance_get_decision_impacts"]("DEC-001"))
            assert "error" in result


class TestGovernanceHealth:
    def test_all_healthy(self):
        mcp = _CaptureMCP()
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = [
            MagicMock(status="ACTIVE"),
            MagicMock(status="ACTIVE"),
        ]

        with patch("governance.mcp_tools.decisions.get_typedb_client",
                   return_value=mock_client), \
             patch("governance.mcp_tools.decisions._detect_document_entropy",
                   return_value=[]), \
             patch("socket.socket") as mock_sock:
            sock_inst = MagicMock()
            sock_inst.connect_ex.return_value = 0
            mock_sock.return_value = sock_inst
            with patch("urllib.request.urlopen") as mock_url:
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.__enter__ = lambda s: s
                mock_resp.__exit__ = MagicMock(return_value=False)
                mock_url.return_value = mock_resp

                register_decision_tools(mcp)
                result = json.loads(mcp.tools["governance_health"]())
                assert result["status"] == "healthy"
                assert result["action_required"] is None

    def test_typedb_down(self):
        mcp = _CaptureMCP()
        mock_client = MagicMock()
        mock_client.connect.return_value = False

        with patch("governance.mcp_tools.decisions.get_typedb_client",
                   return_value=mock_client), \
             patch("socket.socket") as mock_sock:
            sock_inst = MagicMock()
            sock_inst.connect_ex.return_value = 1  # ChromaDB also down
            mock_sock.return_value = sock_inst

            register_decision_tools(mcp)
            result = json.loads(mcp.tools["governance_health"]())
            assert result["status"] == "unhealthy"
            assert result["action_required"] == "START_SERVICES"
            assert "typedb" in result["services"]


class TestDetectDocumentEntropy:
    def test_returns_list(self):
        result = _detect_document_entropy()
        assert isinstance(result, list)

    def test_alerts_are_strings(self):
        result = _detect_document_entropy()
        for alert in result:
            assert isinstance(alert, str)


class TestAliases:
    def test_aliases_registered(self):
        mcp = _CaptureMCP()
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch("governance.mcp_tools.decisions.get_typedb_client",
                   return_value=mock_client):
            register_decision_tools(mcp)
            assert "decision_impacts" in mcp.tools
            assert "health_check" in mcp.tools
