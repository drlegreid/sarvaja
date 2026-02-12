"""
Unit tests for Kanren Rule Conflict Detection.

Per DOC-SIZE-01-v1: Tests for kanren/conflicts.py module.
Tests: conflicting_priorities(), find_rule_conflicts().
"""

from governance.kanren.conflicts import conflicting_priorities, find_rule_conflicts
from governance.kanren.models import RuleContext


def _rule(rule_id, priority, category, status="ACTIVE"):
    return RuleContext(rule_id=rule_id, priority=priority,
                       status=status, category=category)


class TestConflictingPriorities:
    def test_same_category_different_priority(self):
        r1 = _rule("R-1", "HIGH", "SESSION")
        r2 = _rule("R-2", "LOW", "SESSION")
        assert conflicting_priorities(r1, r2) is True

    def test_same_category_same_priority(self):
        r1 = _rule("R-1", "HIGH", "SESSION")
        r2 = _rule("R-2", "HIGH", "SESSION")
        assert conflicting_priorities(r1, r2) is False

    def test_different_category(self):
        r1 = _rule("R-1", "HIGH", "SESSION")
        r2 = _rule("R-2", "LOW", "ARCH")
        assert conflicting_priorities(r1, r2) is False

    def test_different_category_same_priority(self):
        r1 = _rule("R-1", "HIGH", "SESSION")
        r2 = _rule("R-2", "HIGH", "ARCH")
        assert conflicting_priorities(r1, r2) is False


class TestFindRuleConflicts:
    def test_no_conflicts(self):
        rules = [_rule("R-1", "HIGH", "SESSION"), _rule("R-2", "HIGH", "SESSION")]
        assert find_rule_conflicts(rules) == []

    def test_one_conflict(self):
        rules = [_rule("R-1", "HIGH", "SESSION"), _rule("R-2", "LOW", "SESSION")]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 1
        assert conflicts[0][0] == "R-1"
        assert conflicts[0][1] == "R-2"
        assert "Priority conflict" in conflicts[0][2]
        assert "SESSION" in conflicts[0][2]

    def test_multiple_conflicts(self):
        rules = [
            _rule("R-1", "HIGH", "SESSION"),
            _rule("R-2", "LOW", "SESSION"),
            _rule("R-3", "MEDIUM", "SESSION"),
        ]
        conflicts = find_rule_conflicts(rules)
        # R1-R2, R1-R3, R2-R3 all conflict (same cat, different prio)
        assert len(conflicts) == 3

    def test_cross_category_no_conflict(self):
        rules = [
            _rule("R-1", "HIGH", "SESSION"),
            _rule("R-2", "LOW", "ARCH"),
        ]
        assert find_rule_conflicts(rules) == []

    def test_empty_list(self):
        assert find_rule_conflicts([]) == []

    def test_single_rule(self):
        assert find_rule_conflicts([_rule("R-1", "HIGH", "SESSION")]) == []
