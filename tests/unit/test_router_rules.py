"""
Unit tests for Rule Routing Mixin.

Per DOC-SIZE-01-v1: Tests for router/rules.py module.
Tests: RuleRoutingMixin.route_rule, _generate_rule_typeql.
"""

import pytest
from unittest.mock import MagicMock

from governance.router.rules import RuleRoutingMixin


class _TestRuleRouter(RuleRoutingMixin):
    """Concrete class for testing the rule routing mixin."""

    def __init__(self, dry_run=True, embed=False):
        self.dry_run = dry_run
        self.embed = embed
        self.embedding_pipeline = MagicMock() if embed else None
        self.pre_route_hook = None
        self.post_route_hook = None

    def _execute_typeql(self, typeql: str) -> bool:
        return True

    def _escape(self, value: str) -> str:
        return value.replace('"', '\\"').replace("\\", "\\\\")


# ---------------------------------------------------------------------------
# route_rule
# ---------------------------------------------------------------------------
class TestRouteRule:
    """Tests for route_rule()."""

    def test_empty_rule_id_fails(self):
        router = _TestRuleRouter()
        result = router.route_rule("", "Test Rule")
        assert result["success"] is False
        assert "required" in result["error"]

    def test_none_rule_id_fails(self):
        router = _TestRuleRouter()
        result = router.route_rule(None, "Test Rule")
        assert result["success"] is False

    def test_valid_rule_succeeds(self):
        router = _TestRuleRouter()
        result = router.route_rule("RULE-001", "Test Rule", directive="Must do X")
        assert result["success"] is True
        assert result["item_type"] == "rule"
        assert result["item_id"] == "RULE-001"

    def test_dry_run_no_execute(self):
        router = _TestRuleRouter(dry_run=True)
        result = router.route_rule("RULE-001", "Test")
        assert result["success"] is True

    def test_dry_run_with_embed_flag(self):
        router = _TestRuleRouter(dry_run=True, embed=True)
        result = router.route_rule("RULE-001", "Test")
        assert result["embedded"] is True

    def test_embed_with_execute(self):
        router = _TestRuleRouter(dry_run=False, embed=True)
        result = router.route_rule("RULE-001", "Test", directive="Do X")
        assert result["embedded"] is True
        router.embedding_pipeline.embed_and_store_rule.assert_called_once()

    def test_pre_hook_called(self):
        router = _TestRuleRouter()
        hook = MagicMock(side_effect=lambda t, d: d)
        router.pre_route_hook = hook
        router.route_rule("RULE-001", "Test")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "rule"

    def test_post_hook_called(self):
        router = _TestRuleRouter()
        hook = MagicMock()
        router.post_route_hook = hook
        router.route_rule("RULE-001", "Test")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "rule"

    def test_destination_is_typedb(self):
        router = _TestRuleRouter()
        result = router.route_rule("RULE-001", "Test")
        assert result["destination"] == "typedb"

    def test_default_priority_and_category(self):
        router = _TestRuleRouter()
        result = router.route_rule("RULE-001", "Test")
        assert result["success"] is True


# ---------------------------------------------------------------------------
# _generate_rule_typeql
# ---------------------------------------------------------------------------
class TestGenerateRuleTypeql:
    """Tests for _generate_rule_typeql()."""

    def test_contains_rule_id(self):
        router = _TestRuleRouter()
        query = router._generate_rule_typeql("RULE-001", "Test Rule")
        assert "RULE-001" in query

    def test_contains_name(self):
        router = _TestRuleRouter()
        query = router._generate_rule_typeql("RULE-001", "My Rule Name")
        assert "My Rule Name" in query

    def test_contains_directive(self):
        router = _TestRuleRouter()
        query = router._generate_rule_typeql(
            "RULE-001", "Test", directive="Must follow protocol"
        )
        assert "Must follow protocol" in query

    def test_contains_insert_keyword(self):
        router = _TestRuleRouter()
        query = router._generate_rule_typeql("RULE-001", "Test")
        assert "insert" in query

    def test_contains_all_fields(self):
        router = _TestRuleRouter()
        query = router._generate_rule_typeql(
            "RULE-001", "Test", directive="D",
            category="security", priority="HIGH", status="ACTIVE",
        )
        assert "security" in query
        assert "HIGH" in query
        assert "ACTIVE" in query
