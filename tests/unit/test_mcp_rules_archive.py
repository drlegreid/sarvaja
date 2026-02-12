"""
Unit tests for Rule Archive MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/rules_archive.py module.
Tests: rules_list_archived(), rule_get_archived(), rule_restore().
"""

import json
from unittest.mock import patch, MagicMock

from governance.mcp_tools.rules_archive import register_rule_archive_tools


def _json_format(data, **kwargs):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
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
    with patch("governance.mcp_tools.rules_archive.format_mcp_result",
               side_effect=_json_format):
        register_rule_archive_tools(mcp)
    return mcp


class TestRegistration:
    def test_registers_three_tools(self):
        mcp = _register()
        assert "rules_list_archived" in mcp.tools
        assert "rule_get_archived" in mcp.tools
        assert "rule_restore" in mcp.tools


class TestRulesListArchived:
    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_success(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_archived_rules.return_value = [
            {"rule": {"id": "R-1", "name": "Test"}, "archived_at": "2026-01-01",
             "reason": "deprecated", "dependencies": [], "dependents": []},
        ]
        mock_get.return_value = mock_client

        mcp = _register()
        result = json.loads(mcp.tools["rules_list_archived"]())
        assert result["count"] == 1
        assert result["archives"][0]["rule_id"] == "R-1"
        mock_client.close.assert_called()

    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_connect_fail(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_get.return_value = mock_client

        mcp = _register()
        result = json.loads(mcp.tools["rules_list_archived"]())
        assert "error" in result


class TestRuleGetArchived:
    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_found(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_archived_rule.return_value = {"rule_id": "R-1", "data": "ok"}
        mock_get.return_value = mock_client

        mcp = _register()
        result = json.loads(mcp.tools["rule_get_archived"](rule_id="R-1"))
        assert result["rule_id"] == "R-1"

    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_not_found(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_archived_rule.return_value = None
        mock_get.return_value = mock_client

        mcp = _register()
        result = json.loads(mcp.tools["rule_get_archived"](rule_id="R-99"))
        assert "error" in result


class TestRuleRestore:
    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_success(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_rule = MagicMock()
        mock_rule.__dataclass_fields__ = {}
        mock_client.restore_rule.return_value = mock_rule
        mock_get.return_value = mock_client

        with patch("governance.mcp_tools.rules_archive.asdict",
                    return_value={"id": "R-1", "status": "DRAFT"}):
            mcp = _register()
            result = json.loads(mcp.tools["rule_restore"](rule_id="R-1"))
            assert result["success"] is True
            assert "DRAFT" in result["message"]

    @patch("governance.mcp_tools.rules_archive.format_mcp_result", side_effect=_json_format)
    @patch("governance.mcp_tools.rules_archive.get_typedb_client")
    def test_not_found(self, mock_get, mock_fmt):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.restore_rule.return_value = None
        mock_get.return_value = mock_client

        mcp = _register()
        result = json.loads(mcp.tools["rule_restore"](rule_id="R-99"))
        assert "error" in result
