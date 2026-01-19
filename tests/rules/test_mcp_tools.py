"""
MCP Rule Tools Tests
====================
Tests for MCP rule CRUD tool wrappers.
Per DOC-SIZE-01-v1: Split from test_rules_crud.py (838 lines)
"""

import pytest
import json
from unittest.mock import Mock, patch

from governance.client import Rule


class TestMCPRuleTools:
    """Tests for MCP rule CRUD tools."""

    def test_governance_create_rule_success(self, mock_client, sample_rule):
        """Test rule_create returns success JSON."""
        mock_client.create_rule.return_value = sample_rule

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            with patch('governance.mcp_tools.common.get_typedb_client', return_value=mock_client):
                from governance.mcp_tools.rules import register_rule_tools

                mock_mcp = Mock()
                registered_funcs = {}

                def tool_decorator():
                    def inner(func):
                        registered_funcs[func.__name__] = func
                        return func
                    return inner

                mock_mcp.tool = tool_decorator
                register_rule_tools(mock_mcp)

                result = registered_funcs['rule_create'](
                    rule_id=sample_rule.id,
                    name=sample_rule.name,
                    category=sample_rule.category,
                    priority=sample_rule.priority,
                    directive=sample_rule.directive
                )

                data = json.loads(result)
                assert data["success"] is True
                assert sample_rule.id in data["message"]

    def test_governance_create_rule_connection_failure(self, mock_client):
        """Test rule_create handles connection failure."""
        mock_client.connect.return_value = False

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_create'](
                rule_id="RULE-TEST",
                name="Test",
                category="governance",
                priority="HIGH",
                directive="Test"
            )

            data = json.loads(result)
            assert "error" in data
            assert "connect" in data["error"].lower()

    def test_governance_create_rule_validation_error(self, mock_client):
        """Test rule_create handles validation errors."""
        mock_client.create_rule.side_effect = ValueError("Invalid category")

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_create'](
                rule_id="RULE-TEST",
                name="Test",
                category="invalid",
                priority="HIGH",
                directive="Test"
            )

            data = json.loads(result)
            assert "error" in data
            assert "Invalid" in data["error"]

    def test_governance_update_rule_success(self, mock_client, sample_rule):
        """Test rule_update returns success JSON."""
        updated_rule = Rule(
            id=sample_rule.id,
            name="Updated Name",
            category=sample_rule.category,
            priority=sample_rule.priority,
            status=sample_rule.status,
            directive=sample_rule.directive
        )
        mock_client.update_rule.return_value = updated_rule

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_update'](
                rule_id=sample_rule.id,
                name="Updated Name"
            )

            data = json.loads(result)
            assert data["success"] is True
            assert "updated" in data["message"].lower()

    def test_governance_deprecate_rule_success(self, mock_client, sample_rule):
        """Test rule_deprecate returns success JSON."""
        deprecated_rule = Rule(
            id=sample_rule.id,
            name=sample_rule.name,
            category=sample_rule.category,
            priority=sample_rule.priority,
            status="DEPRECATED",
            directive=sample_rule.directive
        )
        mock_client.deprecate_rule.return_value = deprecated_rule

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_deprecate'](
                rule_id=sample_rule.id,
                reason="No longer needed"
            )

            data = json.loads(result)
            assert data["success"] is True
            assert data["new_status"] == "DEPRECATED"
            assert data["reason"] == "No longer needed"

    def test_governance_delete_rule_requires_confirmation(self, mock_client):
        """Test rule_delete requires explicit confirmation."""
        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_delete'](
                rule_id="RULE-TEST",
                confirm=False
            )

            data = json.loads(result)
            assert "error" in data
            assert "confirm" in data["error"].lower()
            assert "warning" in data

    def test_governance_delete_rule_success(self, mock_client):
        """Test rule_delete with confirmation."""
        mock_client.delete_rule.return_value = True

        with patch('governance.mcp_tools.rules_crud.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_delete'](
                rule_id="RULE-TEST",
                confirm=True
            )

            data = json.loads(result)
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
