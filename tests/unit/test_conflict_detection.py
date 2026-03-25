"""Tests for Rule Conflict Detection (EPIC-RULES-V3 P5).

TDD RED: Tests for scope_conflict(), lifecycle_conflict(),
and expanded find_rule_conflicts().

Created: 2026-03-25
"""
import pytest
from governance.kanren.models import RuleContext


@pytest.mark.unit
class TestScopeConflict:
    """Tests for scope_conflict() — overlapping directives in same category."""

    def test_scope_conflict_same_category_different_priority(self):
        """Two active rules in same category with different priorities = scope conflict."""
        from governance.kanren.conflicts import scope_conflict

        r1 = RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="architecture")
        assert scope_conflict(r1, r2) is True

    def test_no_scope_conflict_different_categories(self):
        """Different categories = no scope conflict."""
        from governance.kanren.conflicts import scope_conflict

        r1 = RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="quality")
        assert scope_conflict(r1, r2) is False

    def test_no_scope_conflict_same_priority(self):
        """Same category + same priority = no conflict (compatible directives)."""
        from governance.kanren.conflicts import scope_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="architecture")
        assert scope_conflict(r1, r2) is False

    def test_no_scope_conflict_inactive_rule(self):
        """One non-active rule = no scope conflict."""
        from governance.kanren.conflicts import scope_conflict

        r1 = RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="DEPRECATED", category="architecture")
        assert scope_conflict(r1, r2) is False

    def test_no_scope_conflict_same_rule_id(self):
        """Same rule_id = can't conflict with itself."""
        from governance.kanren.conflicts import scope_conflict

        r1 = RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="architecture")
        assert scope_conflict(r1, r2) is False


@pytest.mark.unit
class TestLifecycleConflict:
    """Tests for lifecycle_conflict() — DEPRECATED rule depended by ACTIVE rule."""

    def test_lifecycle_conflict_deprecated_depended_by_active(self):
        """Active rule depends on deprecated rule = lifecycle conflict."""
        from governance.kanren.conflicts import lifecycle_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="DEPRECATED", category="architecture")
        deps = {"R-001": ["R-002"]}
        assert lifecycle_conflict(r1, r2, deps) is True

    def test_no_lifecycle_conflict_all_active(self):
        """Both rules active = no lifecycle conflict."""
        from governance.kanren.conflicts import lifecycle_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="architecture")
        deps = {"R-001": ["R-002"]}
        assert lifecycle_conflict(r1, r2, deps) is False

    def test_no_lifecycle_conflict_no_dependency(self):
        """Deprecated rule exists but no dependency link = no lifecycle conflict."""
        from governance.kanren.conflicts import lifecycle_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="DEPRECATED", category="architecture")
        deps = {}
        assert lifecycle_conflict(r1, r2, deps) is False

    def test_lifecycle_conflict_reverse_direction(self):
        """Active depends on deprecated — detected regardless of arg order."""
        from governance.kanren.conflicts import lifecycle_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="DEPRECATED", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="architecture")
        deps = {"R-002": ["R-001"]}
        assert lifecycle_conflict(r1, r2, deps) is True

    def test_no_lifecycle_conflict_both_deprecated(self):
        """Both deprecated = no lifecycle conflict (neither is active)."""
        from governance.kanren.conflicts import lifecycle_conflict

        r1 = RuleContext(rule_id="R-001", priority="HIGH", status="DEPRECATED", category="architecture")
        r2 = RuleContext(rule_id="R-002", priority="HIGH", status="DEPRECATED", category="architecture")
        deps = {"R-001": ["R-002"]}
        assert lifecycle_conflict(r1, r2, deps) is False


@pytest.mark.unit
class TestFindRuleConflicts:
    """Tests for expanded find_rule_conflicts() — all conflict types."""

    def test_finds_scope_conflicts(self):
        """find_rule_conflicts returns scope conflicts."""
        from governance.kanren.conflicts import find_rule_conflicts

        rules = [
            RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-002", priority="LOW", status="ACTIVE", category="arch"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) >= 1
        assert any("scope" in c[2].lower() for c in conflicts)

    def test_finds_lifecycle_conflicts(self):
        """find_rule_conflicts returns lifecycle conflicts when deps provided."""
        from governance.kanren.conflicts import find_rule_conflicts

        rules = [
            RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-002", priority="HIGH", status="DEPRECATED", category="arch"),
        ]
        deps = {"R-001": ["R-002"]}
        conflicts = find_rule_conflicts(rules, dependencies=deps)
        assert any("lifecycle" in c[2].lower() for c in conflicts)

    def test_no_conflicts_clean_ruleset(self):
        """No conflicts when rules are in different categories with same priority."""
        from governance.kanren.conflicts import find_rule_conflicts

        rules = [
            RuleContext(rule_id="R-001", priority="HIGH", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-002", priority="HIGH", status="ACTIVE", category="quality"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 0

    def test_returns_list_of_tuples(self):
        """Conflicts are (rule1_id, rule2_id, description) tuples."""
        from governance.kanren.conflicts import find_rule_conflicts

        rules = [
            RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-002", priority="LOW", status="ACTIVE", category="arch"),
        ]
        conflicts = find_rule_conflicts(rules)
        for c in conflicts:
            assert len(c) == 3
            assert isinstance(c[0], str)
            assert isinstance(c[1], str)
            assert isinstance(c[2], str)

    def test_mixed_conflict_types(self):
        """Both scope and lifecycle conflicts detected in one pass."""
        from governance.kanren.conflicts import find_rule_conflicts

        rules = [
            RuleContext(rule_id="R-001", priority="CRITICAL", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-002", priority="LOW", status="ACTIVE", category="arch"),
            RuleContext(rule_id="R-003", priority="HIGH", status="DEPRECATED", category="quality"),
            RuleContext(rule_id="R-004", priority="HIGH", status="ACTIVE", category="quality"),
        ]
        deps = {"R-004": ["R-003"]}
        conflicts = find_rule_conflicts(rules, dependencies=deps)
        types = [c[2].lower() for c in conflicts]
        assert any("scope" in t for t in types)
        assert any("lifecycle" in t for t in types)
