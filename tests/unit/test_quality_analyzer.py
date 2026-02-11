"""
Unit tests for Rule Quality Analyzer.

Per RULE-010, RULE-013: Tests for RuleQualityAnalyzer issue detection
and impact analysis, using mock TypeDB client.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

from governance.quality.models import (
    IssueSeverity,
    IssueType,
    RuleIssue,
    RuleHealthReport,
)
from governance.quality.impact import calculate_rule_impact


@dataclass
class _FakeRule:
    id: str
    name: str = "Test Rule"
    directive: str = "Do something"
    category: str = "governance"
    priority: str = "MEDIUM"
    status: str = "ACTIVE"


def _make_rule_dict(**overrides):
    d = {
        "id": "R-1",
        "name": "Test Rule",
        "directive": "Do something",
        "category": "governance",
        "priority": "MEDIUM",
        "status": "ACTIVE",
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# RuleIssue / RuleHealthReport models
# ---------------------------------------------------------------------------
class TestRuleIssue:
    """Tests for RuleIssue dataclass."""

    def test_to_dict(self):
        issue = RuleIssue(
            rule_id="R-1",
            issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.MEDIUM,
            description="No dependents",
            impact="May be unused",
            remediation="Deprecate",
            related_rules=["R-2"],
            metadata={"count": 0},
        )
        d = issue.to_dict()
        assert d["rule_id"] == "R-1"
        assert d["issue_type"] == "orphaned"
        assert d["severity"] == "MEDIUM"
        assert d["related_rules"] == ["R-2"]

    def test_default_fields(self):
        issue = RuleIssue(
            rule_id="R-1",
            issue_type=IssueType.SHALLOW,
            severity=IssueSeverity.LOW,
            description="test",
            impact="test",
            remediation="test",
        )
        assert issue.related_rules == []
        assert issue.metadata == {}


class TestRuleHealthReport:
    """Tests for RuleHealthReport dataclass."""

    def test_to_dict(self):
        issue = RuleIssue(
            rule_id="R-1", issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.MEDIUM, description="test",
            impact="test", remediation="test",
        )
        report = RuleHealthReport(
            total_rules=5, issues_count=1,
            critical_count=0, high_count=0, medium_count=1, low_count=0,
            issues=[issue], healthy_rules=["R-2", "R-3"],
            timestamp="2026-02-11T10:00:00",
        )
        d = report.to_dict()
        assert d["total_rules"] == 5
        assert d["issues_count"] == 1
        assert len(d["issues"]) == 1
        assert len(d["healthy_rules"]) == 2

    def test_to_json(self):
        report = RuleHealthReport(
            total_rules=1, issues_count=0,
            critical_count=0, high_count=0, medium_count=0, low_count=0,
            issues=[], healthy_rules=["R-1"],
            timestamp="2026-02-11",
        )
        j = report.to_json()
        assert '"total_rules": 1' in j


# ---------------------------------------------------------------------------
# RuleQualityAnalyzer
# ---------------------------------------------------------------------------
class TestRuleQualityAnalyzer:
    """Tests for RuleQualityAnalyzer using mock TypeDB client."""

    @patch("governance.quality.analyzer.TYPEDB_AVAILABLE", True)
    def _make_analyzer(self, rules, deps, client_mock=None):
        """Create an analyzer with pre-loaded caches."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        analyzer = RuleQualityAnalyzer.__new__(RuleQualityAnalyzer)
        analyzer.host = "localhost"
        analyzer.port = 1729
        analyzer.database = "test"
        analyzer._client = client_mock or MagicMock()
        analyzer._rules_cache = {r.id: {"id": r.id, "name": r.name, "directive": r.directive,
                                         "category": r.category, "priority": r.priority,
                                         "status": r.status} for r in rules}
        analyzer._dependencies_cache = {}
        analyzer._dependents_cache = {}
        for rule_id, dep_list in deps.items():
            analyzer._dependencies_cache[rule_id] = set(dep_list)
            for dep in dep_list:
                analyzer._dependents_cache.setdefault(dep, set()).add(rule_id)
        return analyzer

    def test_find_orphaned_rules(self):
        rules = [
            _FakeRule(id="R-1"),
            _FakeRule(id="R-2"),
        ]
        deps = {"R-1": ["R-2"]}  # R-1 depends on R-2, so R-2 has a dependent
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_orphaned_rules()
        orphaned_ids = [i.rule_id for i in issues]
        assert "R-1" in orphaned_ids  # R-1 has no dependents
        assert "R-2" not in orphaned_ids  # R-2 has R-1 as dependent

    def test_foundational_rules_not_orphaned(self):
        rules = [_FakeRule(id="RULE-001")]
        deps = {}
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_orphaned_rules()
        assert len(issues) == 0

    def test_inactive_rules_not_orphaned(self):
        rules = [_FakeRule(id="R-1", status="DEPRECATED")]
        deps = {}
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_orphaned_rules()
        assert len(issues) == 0

    def test_find_shallow_rules_missing_directive(self):
        rules = [_FakeRule(id="R-1", directive="")]
        deps = {}
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_shallow_rules()
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.HIGH
        assert "directive" in issues[0].metadata["missing_attributes"]

    def test_find_shallow_rules_missing_name(self):
        rules = [_FakeRule(id="R-1", name="")]
        deps = {}
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_shallow_rules()
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.MEDIUM  # non-directive missing

    def test_find_shallow_rules_complete(self):
        rules = [_FakeRule(id="R-1")]
        deps = {}
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_shallow_rules()
        assert len(issues) == 0

    def test_find_over_connected_rules(self):
        rules = [_FakeRule(id="R-1")]
        deps = {"R-1": ["R-2", "R-3", "R-4", "R-5", "R-6", "R-7"]}  # 6 > MAX(5)
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_over_connected_rules()
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.OVER_CONNECTED

    def test_find_over_connected_under_threshold(self):
        rules = [_FakeRule(id="R-1")]
        deps = {"R-1": ["R-2", "R-3"]}  # 2 <= MAX(5)
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_over_connected_rules()
        assert len(issues) == 0

    def test_find_circular_dependencies(self):
        rules = [_FakeRule(id="R-1"), _FakeRule(id="R-2")]
        deps = {"R-1": ["R-2"], "R-2": ["R-1"]}  # R-1 → R-2 → R-1
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_circular_dependencies()
        assert len(issues) >= 1
        assert issues[0].issue_type == IssueType.CIRCULAR_DEPENDENCY
        assert issues[0].severity == IssueSeverity.CRITICAL

    def test_no_circular_dependencies(self):
        rules = [_FakeRule(id="R-1"), _FakeRule(id="R-2")]
        deps = {"R-1": ["R-2"]}  # Linear
        analyzer = self._make_analyzer(rules, deps)
        issues = analyzer.find_circular_dependencies()
        assert len(issues) == 0

    def test_analyze_full_report(self):
        rules = [
            _FakeRule(id="R-1", directive=""),  # shallow
            _FakeRule(id="R-2"),  # healthy
        ]
        deps = {"R-2": ["R-1"]}  # R-1 has dependent R-2
        client = MagicMock()
        # Mock execute_query for under_documented check
        client.execute_query.return_value = []
        analyzer = self._make_analyzer(rules, deps, client_mock=client)
        report = analyzer.analyze()
        assert isinstance(report, RuleHealthReport)
        assert report.total_rules == 2
        assert report.issues_count >= 1  # at least the shallow rule

    def test_get_rule_impact(self):
        rules = [_FakeRule(id="R-1"), _FakeRule(id="R-2")]
        deps = {"R-2": ["R-1"]}  # R-2 depends on R-1
        analyzer = self._make_analyzer(rules, deps)
        impact = analyzer.get_rule_impact("R-1")
        assert impact["rule_id"] == "R-1"
        assert "R-2" in impact["direct_dependents"]

    def test_close(self):
        rules = []
        deps = {}
        client = MagicMock()
        analyzer = self._make_analyzer(rules, deps, client_mock=client)
        analyzer.close()
        client.close.assert_called_once()
        assert analyzer._client is None


# ---------------------------------------------------------------------------
# calculate_rule_impact (pure function)
# ---------------------------------------------------------------------------
class TestCalculateRuleImpact:
    """Tests for calculate_rule_impact() pure function."""

    def test_basic_impact(self):
        rule = _make_rule_dict(priority="HIGH", category="governance")
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache={"R-1": {"R-2"}},
            all_rules={"R-1": rule, "R-2": _make_rule_dict(id="R-2")},
        )
        assert result["rule_id"] == "R-1"
        assert result["rule_name"] == "Test Rule"
        assert result["direct_dependents"] == ["R-2"]
        assert result["priority"] == "HIGH"

    def test_transitive_dependents(self):
        rule = _make_rule_dict()
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache={"R-1": {"R-2"}, "R-2": {"R-3"}},
            all_rules={},
        )
        assert "R-2" in result["all_affected_rules"]
        assert "R-3" in result["all_affected_rules"]

    def test_critical_priority_high_score(self):
        rule = _make_rule_dict(priority="CRITICAL", category="governance")
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache={"R-1": {"R-2", "R-3", "R-4"}},
            all_rules={},
        )
        assert result["impact_score"] >= 70
        assert "HIGH RISK" in result["recommendation"]

    def test_low_priority_no_dependents_low_score(self):
        rule = _make_rule_dict(priority="LOW", category="testing")
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache={},
            all_rules={},
        )
        assert result["impact_score"] <= 30
        assert "LOW RISK" in result["recommendation"]

    def test_medium_risk_range(self):
        rule = _make_rule_dict(priority="HIGH", category="testing")
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache={"R-1": {"R-2"}},
            all_rules={},
        )
        assert 40 <= result["impact_score"] < 70
        assert "MEDIUM RISK" in result["recommendation"]

    def test_score_capped_at_100(self):
        rule = _make_rule_dict(priority="CRITICAL", category="governance")
        # Many dependents to push score high
        deps = {f"D-{i}" for i in range(20)}
        dep_cache = {"R-1": deps}
        for d in deps:
            dep_cache[d] = set()
        result = calculate_rule_impact(
            rule_id="R-1", rule=rule,
            dependents_cache=dep_cache,
            all_rules={},
        )
        assert result["impact_score"] == 100

    def test_unknown_rule_defaults(self):
        result = calculate_rule_impact(
            rule_id="UNKNOWN", rule={},
            dependents_cache={},
            all_rules={},
        )
        assert result["rule_name"] == "Unknown"
        assert result["priority"] is None
