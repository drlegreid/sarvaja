"""
Unit tests for Kanren Rule Conflict Detection.

Per DOC-SIZE-01-v1: Tests for kanren/conflicts.py module.
Tests: conflicting_priorities, find_rule_conflicts.
"""

import pytest

from governance.kanren.models import RuleContext
from governance.kanren.conflicts import conflicting_priorities, find_rule_conflicts


class TestConflictingPriorities:
    """Tests for conflicting_priorities()."""

    def test_same_category_diff_priority(self):
        r1 = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance")
        r2 = RuleContext(rule_id="R-2", priority="LOW", status="ACTIVE", category="governance")
        assert conflicting_priorities(r1, r2) is True

    def test_same_category_same_priority(self):
        r1 = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance")
        r2 = RuleContext(rule_id="R-2", priority="HIGH", status="ACTIVE", category="governance")
        assert conflicting_priorities(r1, r2) is False

    def test_diff_category_diff_priority(self):
        r1 = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance")
        r2 = RuleContext(rule_id="R-2", priority="LOW", status="ACTIVE", category="testing")
        assert conflicting_priorities(r1, r2) is False

    def test_diff_category_same_priority(self):
        r1 = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance")
        r2 = RuleContext(rule_id="R-2", priority="HIGH", status="ACTIVE", category="testing")
        assert conflicting_priorities(r1, r2) is False


class TestFindRuleConflicts:
    """Tests for find_rule_conflicts()."""

    def test_no_rules(self):
        assert find_rule_conflicts([]) == []

    def test_single_rule(self):
        r = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance")
        assert find_rule_conflicts([r]) == []

    def test_finds_conflict(self):
        rules = [
            RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance"),
            RuleContext(rule_id="R-2", priority="LOW", status="ACTIVE", category="governance"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 1
        assert conflicts[0][0] == "R-1"
        assert conflicts[0][1] == "R-2"
        assert "governance" in conflicts[0][2]

    def test_no_conflict_different_categories(self):
        rules = [
            RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance"),
            RuleContext(rule_id="R-2", priority="LOW", status="ACTIVE", category="testing"),
        ]
        assert find_rule_conflicts(rules) == []

    def test_multiple_conflicts(self):
        rules = [
            RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="governance"),
            RuleContext(rule_id="R-2", priority="LOW", status="ACTIVE", category="governance"),
            RuleContext(rule_id="R-3", priority="CRITICAL", status="ACTIVE", category="governance"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 3  # R-1/R-2, R-1/R-3, R-2/R-3
