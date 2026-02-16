"""TDD Tests for Cycle 15-16: Rule Scope Mechanism Prototype.

Gap: GAP-RULE-SCOPE-001
Problem: Rules are global — no way to scope them to specific components.
Solution: Add scope field + rule_applies_to_path() utility function.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestRuleScopeFunction:
    """rule_applies_to_path() checks if a rule applies to a given file path."""

    def test_function_importable(self):
        """rule_applies_to_path can be imported."""
        from governance.services.rule_scope import rule_applies_to_path
        assert callable(rule_applies_to_path)

    def test_global_rule_applies_everywhere(self):
        """Rule with scope=['*'] applies to any path."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(scope=["*"], path="governance/services/tasks.py")
        assert rule_applies_to_path(scope=["*"], path="agent/dashboard.py")

    def test_no_scope_is_global(self):
        """Rule with no scope (None or []) is treated as global."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(scope=None, path="anything.py")
        assert rule_applies_to_path(scope=[], path="anything.py")

    def test_specific_directory_scope(self):
        """Rule scoped to governance/** only applies to governance paths."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(
            scope=["governance/**"], path="governance/services/tasks.py"
        )
        assert not rule_applies_to_path(
            scope=["governance/**"], path="agent/dashboard.py"
        )

    def test_multiple_scopes(self):
        """Rule with multiple scopes matches any of them."""
        from governance.services.rule_scope import rule_applies_to_path
        scope = ["governance/**", "agent/**"]
        assert rule_applies_to_path(scope=scope, path="governance/routes/audit.py")
        assert rule_applies_to_path(scope=scope, path="agent/views/monitor.py")
        assert not rule_applies_to_path(scope=scope, path="scripts/deploy.py")

    def test_exact_file_scope(self):
        """Scope can match an exact file."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(
            scope=["governance/routes/audit.py"], path="governance/routes/audit.py"
        )
        assert not rule_applies_to_path(
            scope=["governance/routes/audit.py"], path="governance/routes/tasks.py"
        )

    def test_subdirectory_scope(self):
        """Scope can target a specific subdirectory."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(
            scope=["tests/unit/**"], path="tests/unit/test_audit.py"
        )
        assert not rule_applies_to_path(
            scope=["tests/unit/**"], path="tests/integration/test_api.py"
        )


class TestGetApplicableRules:
    """get_applicable_rules() returns rules that apply to a given path."""

    def test_function_importable(self):
        """get_applicable_rules can be imported."""
        from governance.services.rule_scope import get_applicable_rules
        assert callable(get_applicable_rules)

    def test_filters_by_path(self):
        """Only returns rules whose scope matches the path."""
        from governance.services.rule_scope import get_applicable_rules

        rules = [
            {"rule_id": "TEST-GUARD-01", "scope": ["tests/**"]},
            {"rule_id": "GOV-RULE-01", "scope": ["governance/**"]},
            {"rule_id": "DOC-SIZE-01", "scope": ["*"]},
        ]
        result = get_applicable_rules(rules, "tests/unit/test_audit.py")
        rule_ids = [r["rule_id"] for r in result]
        assert "TEST-GUARD-01" in rule_ids
        assert "DOC-SIZE-01" in rule_ids
        assert "GOV-RULE-01" not in rule_ids

    def test_rules_without_scope_always_included(self):
        """Rules without scope field are treated as global."""
        from governance.services.rule_scope import get_applicable_rules

        rules = [
            {"rule_id": "NO-SCOPE", "name": "test"},
            {"rule_id": "HAS-SCOPE", "scope": ["agent/**"]},
        ]
        result = get_applicable_rules(rules, "governance/stores/audit.py")
        rule_ids = [r["rule_id"] for r in result]
        assert "NO-SCOPE" in rule_ids
        assert "HAS-SCOPE" not in rule_ids
