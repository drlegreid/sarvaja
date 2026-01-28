"""
Robot Framework Library for Rules Archive MCP Tools Tests.
Split from RulesArchiveLibrary.py per DOC-SIZE-01-v1

Tests for MCP-level archive tool operations.
Per: RF-007 Robot Framework Migration
"""
import json
from unittest.mock import Mock, patch
from dataclasses import asdict
from robot.api.deco import keyword


class RulesArchiveAdvancedLibrary:
    """Robot Framework keywords for rules archive MCP tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_sample_rule(self):
        """Create a sample rule for testing."""
        try:
            from governance.client import Rule
            return Rule(
                id="RULE-TEST-001",
                name="Test Rule",
                category="testing",
                priority="MEDIUM",
                status="DRAFT",
                directive="This is a test rule directive."
            )
        except ImportError:
            return None

    # =========================================================================
    # MCP Archive Tools Tests
    # =========================================================================

    @keyword("MCP List Archived Rules")
    def mcp_list_archived_rules(self):
        """Test rules_list_archived returns JSON array."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
            mock_client.get_archived_rules.return_value = [
                {
                    "rule": {"id": "RULE-001", "name": "Test"},
                    "archived_at": "2024-01-01T12:00:00",
                    "reason": "deleted",
                    "dependencies": [],
                    "dependents": []
                }
            ]

            with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
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

                result = registered_funcs['rules_list_archived']()
                data = json.loads(result)

                return {
                    "has_archives": "archives" in data,
                    "count_correct": data.get("count") == 1,
                    "has_rule_id": data["archives"][0]["rule_id"] == "RULE-001" if data.get("archives") else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Get Archived Rule Success")
    def mcp_get_archived_rule_success(self):
        """Test rule_get_archived returns archive data."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            mock_client = Mock(spec=TypeDBClient)
            mock_client.get_archived_rule.return_value = {
                "rule": asdict(sample_rule),
                "archived_at": "2024-01-01T12:00:00",
                "reason": "deleted"
            }

            with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
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

                result = registered_funcs['rule_get_archived'](rule_id=sample_rule.id)
                data = json.loads(result)

                return {
                    "has_rule": "rule" in data,
                    "id_matches": data["rule"]["id"] == sample_rule.id if "rule" in data else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Get Archived Rule Not Found")
    def mcp_get_archived_rule_not_found(self):
        """Test rule_get_archived returns error for missing archive."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
            mock_client.get_archived_rule.return_value = None

            with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
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

                result = registered_funcs['rule_get_archived'](rule_id="RULE-NONEXISTENT")
                data = json.loads(result)

                return {"has_error": "error" in data}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Restore Rule Success")
    def mcp_restore_rule_success(self):
        """Test rule_restore returns restored rule."""
        try:
            from governance.client import TypeDBClient, Rule

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            restored_rule = Rule(
                id=sample_rule.id,
                name=sample_rule.name,
                category=sample_rule.category,
                priority=sample_rule.priority,
                status="DRAFT",
                directive=sample_rule.directive
            )

            mock_client = Mock(spec=TypeDBClient)
            mock_client.restore_rule.return_value = restored_rule

            with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
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

                result = registered_funcs['rule_restore'](rule_id=sample_rule.id)
                data = json.loads(result)

                return {
                    "success": data.get("success", False),
                    "status_draft": data.get("rule", {}).get("status") == "DRAFT"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Restore Rule Not Found")
    def mcp_restore_rule_not_found(self):
        """Test rule_restore returns error for missing archive."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
            mock_client.restore_rule.return_value = None

            with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
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

                result = registered_funcs['rule_restore'](rule_id="RULE-NONEXISTENT")
                data = json.loads(result)

                return {"has_error": "error" in data}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
