"""MCP Rules Integration Tests — Gov-Core tools against real TypeDB.

Tests rule query, get, dependencies, and conflict detection MCP tools
with a live TypeDB instance. No mocking.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_rules_integration.py -v
Requires: TypeDB on localhost:1729
"""

import json
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixture: register gov-core rule query tools
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rule_tools(typedb_available):
    """Register and return rule query MCP tool functions."""
    from governance.mcp_tools.rules_query import register_rule_query_tools
    mcp = MockMCP()
    register_rule_query_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def rule_crud_tools(typedb_available):
    """Register and return rule CRUD MCP tool functions."""
    from governance.mcp_tools.rules_crud import register_rule_crud_tools
    mcp = MockMCP()
    register_rule_crud_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def rule_archive_tools(typedb_available):
    """Register and return rule archive MCP tool functions."""
    from governance.mcp_tools.rules_archive import register_rule_archive_tools
    mcp = MockMCP()
    register_rule_archive_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Query tests
# ---------------------------------------------------------------------------

class TestRulesQuery:
    """Test rules_query with real TypeDB data."""

    def test_query_all_rules(self, rule_tools):
        """rules_query() with no filters returns rules from TypeDB."""
        result = parse_mcp_result(rule_tools["rules_query"]())
        assert "rules" in result
        assert isinstance(result["rules"], list)
        assert result.get("source") == "typedb"

    def test_query_returns_count(self, rule_tools):
        """rules_query() includes count field (may differ from len if paginated)."""
        result = parse_mcp_result(rule_tools["rules_query"]())
        assert "count" in result
        assert isinstance(result["count"], int)
        assert result["count"] >= len(result["rules"])

    def test_query_active_rules(self, rule_tools):
        """rules_query(status='ACTIVE') filters to active rules only."""
        result = parse_mcp_result(rule_tools["rules_query"](status="ACTIVE"))
        assert "rules" in result
        for rule in result["rules"]:
            assert rule["status"] == "ACTIVE"

    def test_query_by_category(self, rule_tools):
        """rules_query(category=X) filters by category."""
        # First get all rules to find a valid category
        all_result = parse_mcp_result(rule_tools["rules_query"]())
        if not all_result["rules"]:
            pytest.skip("No rules in TypeDB")

        category = all_result["rules"][0]["category"]
        filtered = parse_mcp_result(rule_tools["rules_query"](category=category))
        assert all(r["category"] == category for r in filtered["rules"])

    def test_query_by_priority(self, rule_tools):
        """rules_query(priority=X) filters by priority."""
        all_result = parse_mcp_result(rule_tools["rules_query"]())
        if not all_result["rules"]:
            pytest.skip("No rules in TypeDB")

        priority = all_result["rules"][0]["priority"]
        filtered = parse_mcp_result(rule_tools["rules_query"](priority=priority))
        assert all(r["priority"] == priority for r in filtered["rules"])

    def test_query_nonexistent_category_returns_empty(self, rule_tools):
        """rules_query with bogus category returns empty list."""
        result = parse_mcp_result(
            rule_tools["rules_query"](category="NONEXISTENT-CATEGORY-XYZ")
        )
        assert result["rules"] == []
        assert result["count"] == 0


class TestRulesQueryByTags:
    """Test rules_query_by_tags with real TypeDB data."""

    def test_query_by_tags_returns_structure(self, rule_tools):
        """rules_query_by_tags() returns rules and filter info."""
        result = parse_mcp_result(rule_tools["rules_query_by_tags"]())
        assert "rules" in result
        assert "count" in result
        assert "filter" in result

    def test_query_by_nonexistent_tag(self, rule_tools):
        """rules_query_by_tags with bogus tag returns empty."""
        result = parse_mcp_result(
            rule_tools["rules_query_by_tags"](tags="nonexistent-tag-xyz")
        )
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Single rule get tests
# ---------------------------------------------------------------------------

class TestRuleGet:
    """Test rule_get with real TypeDB data."""

    def test_get_existing_rule(self, rule_tools):
        """rule_get for an existing rule returns rule data."""
        # Find a real rule ID first
        all_result = parse_mcp_result(rule_tools["rules_query"]())
        if not all_result["rules"]:
            pytest.skip("No rules in TypeDB")

        rule_id = all_result["rules"][0]["id"]
        result = parse_mcp_result(rule_tools["rule_get"](rule_id=rule_id))
        assert result.get("id") == rule_id
        assert "name" in result
        assert "directive" in result

    def test_get_nonexistent_rule(self, rule_tools):
        """rule_get for missing ID returns error or fallback."""
        result = parse_mcp_result(
            rule_tools["rule_get"](rule_id="NONEXISTENT-RULE-XYZ-999")
        )
        # Should either be an error or a markdown fallback with warning
        has_error = "error" in result
        has_warning = "warning" in result
        assert has_error or has_warning


class TestRuleDependencies:
    """Test rule_get_deps with real TypeDB data."""

    def test_get_deps_returns_data(self, rule_tools):
        """rule_get_deps returns dependency information."""
        all_result = parse_mcp_result(rule_tools["rules_query"]())
        if not all_result["rules"]:
            pytest.skip("No rules in TypeDB")

        rule_id = all_result["rules"][0]["id"]
        result = parse_mcp_result(rule_tools["rule_get_deps"](rule_id=rule_id))
        # Result may be a list of dependency IDs or a dict with deps
        assert isinstance(result, (dict, list))

    def test_get_deps_nonexistent(self, rule_tools):
        """rule_get_deps for missing rule returns error or empty deps."""
        result = parse_mcp_result(
            rule_tools["rule_get_deps"](rule_id="NONEXISTENT-RULE-XYZ-999")
        )
        assert isinstance(result, (dict, list))


class TestRulesConflicts:
    """Test rules_find_conflicts with real TypeDB data."""

    def test_find_conflicts_returns_data(self, rule_tools):
        """rules_find_conflicts returns conflict analysis."""
        result = parse_mcp_result(rule_tools["rules_find_conflicts"]())
        assert isinstance(result, (dict, list))


# ---------------------------------------------------------------------------
# CRUD lifecycle test
# ---------------------------------------------------------------------------

class TestRuleCRUDLifecycle:
    """Test rule create → get → update → delete lifecycle."""

    RULE_ID = "INTTEST-RULE-LIFECYCLE-001"

    def test_lifecycle(self, rule_crud_tools, rule_tools):
        """Full CRUD lifecycle with real TypeDB."""
        # CREATE
        create_result = parse_mcp_result(rule_crud_tools["rule_create"](
            rule_id=self.RULE_ID,
            name="Integration Test Rule",
            category="testing",
            priority="LOW",
            directive="This rule exists only for integration testing.",
        ))
        assert create_result.get("success") is True or "message" in create_result

        # GET
        get_result = parse_mcp_result(rule_tools["rule_get"](rule_id=self.RULE_ID))
        assert get_result.get("id") == self.RULE_ID or get_result.get("rule_id") == self.RULE_ID

        # UPDATE
        update_result = parse_mcp_result(rule_crud_tools["rule_update"](
            rule_id=self.RULE_ID,
            priority="HIGH",
        ))
        assert "error" not in update_result or update_result.get("success") is True

        # DELETE (with confirm)
        delete_result = parse_mcp_result(rule_crud_tools["rule_delete"](
            rule_id=self.RULE_ID,
            confirm=True,
        ))
        assert delete_result.get("deleted") is True or "error" not in delete_result

        # VERIFY DELETED
        verify = parse_mcp_result(rule_tools["rule_get"](rule_id=self.RULE_ID))
        # Should be gone (error) or only in markdown fallback
        assert "error" in verify or "warning" in verify


class TestRuleDeleteGuard:
    """Test that rule_delete requires confirm=True."""

    def test_delete_without_confirm_rejected(self, rule_crud_tools):
        """rule_delete without confirm=True is rejected."""
        result = parse_mcp_result(rule_crud_tools["rule_delete"](
            rule_id="ANY-RULE-ID",
            confirm=False,
        ))
        assert "error" in result
        assert "confirm" in result["error"].lower() or "confirmation" in result["error"].lower()
