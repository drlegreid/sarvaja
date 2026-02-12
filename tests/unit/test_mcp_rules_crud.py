"""
Unit tests for Rule CRUD MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/rules_crud.py module.
Tests: rule_create, rule_update, rule_deprecate, rule_delete.
"""

import json
from dataclasses import dataclass, asdict
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.rules_crud import register_rule_crud_tools

_P_CLIENT = "governance.mcp_tools.rules_crud.get_typedb_client"
_P_FMT = "governance.mcp_tools.rules_crud.format_mcp_result"
_P_LOG = "governance.mcp_tools.rules_crud.log_monitor_event"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@dataclass
class _MockRule:
    id: str = "RULE-999"
    name: str = "Test Rule"
    category: str = "TEST"
    priority: str = "HIGH"
    directive: str = "Do the thing"
    status: str = "ACTIVE"
    rule_type: str = None
    applicability: str = None


@pytest.fixture(autouse=True)
def _json_format():
    with patch(_P_FMT, side_effect=lambda x: json.dumps(x)), \
         patch(_P_LOG):
        yield


@pytest.fixture()
def mcp():
    m = _CaptureMCP()
    register_rule_crud_tools(m)
    return m


def _mock_client(connect=True, rule=None, delete_result=True):
    c = MagicMock()
    c.connect.return_value = connect
    c.create_rule.return_value = rule or _MockRule()
    c.update_rule.return_value = rule or _MockRule()
    c.deprecate_rule.return_value = rule or _MockRule()
    c.delete_rule.return_value = delete_result
    return c


class TestRuleCreate:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_create"](
                "R-1", "Test", "CAT", "HIGH", "Do it",
            ))
            assert result["success"] is True

    def test_with_applicability(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_create"](
                "R-1", "Test", "CAT", "HIGH", "Do it",
                applicability="MANDATORY",
            ))
            assert result["success"] is True

    def test_invalid_applicability(self, mcp):
        result = json.loads(mcp.tools["rule_create"](
            "R-1", "Test", "CAT", "HIGH", "Do it",
            applicability="INVALID",
        ))
        assert "error" in result

    def test_no_connect(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client(connect=False)):
            result = json.loads(mcp.tools["rule_create"](
                "R-1", "Test", "CAT", "HIGH", "Do it",
            ))
            assert "error" in result

    def test_create_fails(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client(rule=None)) as p:
            p.return_value.create_rule.return_value = None
            result = json.loads(mcp.tools["rule_create"](
                "R-1", "Test", "CAT", "HIGH", "Do it",
            ))
            assert "error" in result


class TestRuleUpdate:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_update"]("R-1", name="New"))
            assert result["success"] is True

    def test_no_connect(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client(connect=False)):
            result = json.loads(mcp.tools["rule_update"]("R-1", name="New"))
            assert "error" in result

    def test_update_fails(self, mcp):
        c = _mock_client()
        c.update_rule.return_value = None
        with patch(_P_CLIENT, return_value=c):
            result = json.loads(mcp.tools["rule_update"]("R-1", name="New"))
            assert "error" in result


class TestRuleDeprecate:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_deprecate"]("R-1"))
            assert result["success"] is True
            assert result["new_status"] == "DEPRECATED"

    def test_with_reason(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_deprecate"]("R-1", reason="Replaced"))
            assert result["reason"] == "Replaced"

    def test_not_found(self, mcp):
        c = _mock_client()
        c.deprecate_rule.return_value = None
        with patch(_P_CLIENT, return_value=c):
            result = json.loads(mcp.tools["rule_deprecate"]("R-NONE"))
            assert "error" in result


class TestRuleDelete:
    def test_requires_confirm(self, mcp):
        result = json.loads(mcp.tools["rule_delete"]("R-1"))
        assert "error" in result
        assert "confirm" in result["error"].lower()

    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client()):
            result = json.loads(mcp.tools["rule_delete"]("R-1", confirm=True))
            assert result["success"] is True
            assert result["archived"] is True

    def test_not_found(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client(delete_result=False)):
            result = json.loads(mcp.tools["rule_delete"]("R-NONE", confirm=True))
            assert "error" in result

    def test_no_connect(self, mcp):
        with patch(_P_CLIENT, return_value=_mock_client(connect=False)):
            result = json.loads(mcp.tools["rule_delete"]("R-1", confirm=True))
            assert "error" in result
