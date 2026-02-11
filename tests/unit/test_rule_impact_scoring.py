"""
Unit tests for Rule Impact Scoring Mixin.

Per DOC-SIZE-01-v1: Tests for extracted rule_impact_scoring.py.
Tests: simulate_change, get_affected_rules, calculate_impact_score, rank_by_impact.
"""

import pytest

from agent.rule_impact_scoring import RuleImpactScoringMixin


class MockImpactAnalyzer(RuleImpactScoringMixin):
    """Test host for the mixin."""

    def __init__(self, rules, dependents, required):
        self._rules = {r.get("id", r.get("rule_id", "")): r for r in rules}
        self._dependents = dependents  # rule_id -> [dependent_ids]
        self._required = required  # rule_id -> [required_ids]

    def _fetch_rules(self):
        return list(self._rules.values())

    def _get_rule(self, rule_id):
        return self._rules.get(rule_id)

    def get_dependent_rules(self, rule_id):
        return self._dependents.get(rule_id, [])

    def get_required_rules(self, rule_id):
        return self._required.get(rule_id, [])


class TestGetAffectedRules:
    """Tests for get_affected_rules()."""

    def test_no_dependents(self):
        analyzer = MockImpactAnalyzer([], {}, {})
        result = analyzer.get_affected_rules("R-1")
        assert result == []

    def test_direct_dependents(self):
        analyzer = MockImpactAnalyzer([], {"R-1": ["R-2", "R-3"]}, {})
        result = analyzer.get_affected_rules("R-1")
        assert set(result) == {"R-2", "R-3"}

    def test_transitive_dependents(self):
        analyzer = MockImpactAnalyzer(
            [], {"R-1": ["R-2"], "R-2": ["R-3"]}, {},
        )
        result = analyzer.get_affected_rules("R-1")
        assert set(result) == {"R-2", "R-3"}

    def test_no_cycles(self):
        # R-1 -> R-2 -> R-1 (cycle)
        analyzer = MockImpactAnalyzer(
            [], {"R-1": ["R-2"], "R-2": ["R-1"]}, {},
        )
        result = analyzer.get_affected_rules("R-1")
        # Should not loop infinitely
        assert "R-2" in result


class TestSimulateChange:
    """Tests for simulate_change()."""

    def test_modify(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1"}, {"id": "R-2"}],
            {"R-1": ["R-2"]}, {},
        )
        result = analyzer.simulate_change("R-1", "modify")
        assert result["rule_id"] == "R-1"
        assert result["change_type"] == "modify"
        assert result["impact_score"] == 1.0  # 1 affected * 1.0

    def test_delete_higher_score(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1"}, {"id": "R-2"}],
            {"R-1": ["R-2"]}, {},
        )
        result = analyzer.simulate_change("R-1", "delete")
        assert result["impact_score"] == 3.0  # 1 affected * 3.0
        assert len(result["warnings"]) >= 1

    def test_deprecate(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1"}], {"R-1": ["R-2", "R-3"]}, {},
        )
        result = analyzer.simulate_change("R-1", "deprecate")
        assert result["impact_score"] == 4.0  # 2 affected * 2.0

    def test_critical_rule_adds_score(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1"}, {"id": "R-2", "priority": "CRITICAL"}],
            {"R-1": ["R-2"]}, {},
        )
        result = analyzer.simulate_change("R-1", "modify")
        assert result["impact_score"] == 6.0  # 1*1.0 + 5.0 critical bonus


class TestCalculateImpactScore:
    """Tests for calculate_impact_score()."""

    def test_nonexistent_rule(self):
        analyzer = MockImpactAnalyzer([], {}, {})
        assert analyzer.calculate_impact_score("NOPE") == 0.0

    def test_critical_priority(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1", "priority": "CRITICAL"}], {}, {},
        )
        score = analyzer.calculate_impact_score("R-1")
        assert score == 10.0

    def test_with_dependents_and_required(self):
        analyzer = MockImpactAnalyzer(
            [{"id": "R-1", "priority": "MEDIUM"}],
            {"R-1": ["R-2", "R-3"]},
            {"R-1": ["R-4"]},
        )
        score = analyzer.calculate_impact_score("R-1")
        # 2.0 (MEDIUM) + 4.0 (2 deps * 2.0) + 0.5 (1 req * 0.5) = 6.5
        assert score == 6.5


class TestRankByImpact:
    """Tests for rank_by_impact()."""

    def test_empty(self):
        analyzer = MockImpactAnalyzer([], {}, {})
        assert analyzer.rank_by_impact() == []

    def test_sorted_descending(self):
        analyzer = MockImpactAnalyzer(
            [
                {"id": "R-1", "name": "Low", "priority": "LOW"},
                {"id": "R-2", "name": "Critical", "priority": "CRITICAL"},
            ],
            {}, {},
        )
        result = analyzer.rank_by_impact()
        assert result[0]["rule_id"] == "R-2"
        assert result[1]["rule_id"] == "R-1"
