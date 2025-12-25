"""
Tests for RuleQualityAnalyzer

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: Evidence-Based Wisdom (RULE-010)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass


class TestRuleQualityAnalyzerUnit:
    """Unit tests for RuleQualityAnalyzer class."""

    def test_rule_quality_analyzer_class_exists(self):
        """RuleQualityAnalyzer class exists and is importable."""
        from governance.rule_quality import RuleQualityAnalyzer
        assert RuleQualityAnalyzer is not None

    def test_issue_severity_enum(self):
        """IssueSeverity enum has expected values."""
        from governance.rule_quality import IssueSeverity
        assert IssueSeverity.CRITICAL.value == "CRITICAL"
        assert IssueSeverity.HIGH.value == "HIGH"
        assert IssueSeverity.MEDIUM.value == "MEDIUM"
        assert IssueSeverity.LOW.value == "LOW"

    def test_issue_type_enum(self):
        """IssueType enum has expected values."""
        from governance.rule_quality import IssueType
        assert IssueType.ORPHANED.value == "orphaned"
        assert IssueType.SHALLOW.value == "shallow"
        assert IssueType.OVER_CONNECTED.value == "over_connected"
        assert IssueType.CIRCULAR_DEPENDENCY.value == "circular"


class TestRuleIssueDataclass:
    """Tests for RuleIssue dataclass."""

    def test_rule_issue_creation(self):
        """RuleIssue dataclass creates correctly."""
        from governance.rule_quality import RuleIssue, IssueType, IssueSeverity

        issue = RuleIssue(
            rule_id="RULE-001",
            issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.MEDIUM,
            description="Test description",
            impact="Test impact",
            remediation="Test remediation"
        )

        assert issue.rule_id == "RULE-001"
        assert issue.issue_type == IssueType.ORPHANED
        assert issue.severity == IssueSeverity.MEDIUM

    def test_rule_issue_to_dict(self):
        """RuleIssue converts to dictionary."""
        from governance.rule_quality import RuleIssue, IssueType, IssueSeverity

        issue = RuleIssue(
            rule_id="RULE-002",
            issue_type=IssueType.SHALLOW,
            severity=IssueSeverity.HIGH,
            description="Missing directive",
            impact="Unclear enforcement",
            remediation="Add directive"
        )

        d = issue.to_dict()

        assert d["rule_id"] == "RULE-002"
        assert d["issue_type"] == "shallow"
        assert d["severity"] == "HIGH"


class TestRuleHealthReport:
    """Tests for RuleHealthReport dataclass."""

    def test_rule_health_report_creation(self):
        """RuleHealthReport dataclass creates correctly."""
        from governance.rule_quality import RuleHealthReport

        report = RuleHealthReport(
            total_rules=10,
            issues_count=3,
            critical_count=1,
            high_count=1,
            medium_count=1,
            low_count=0,
            issues=[],
            healthy_rules=["RULE-001", "RULE-002"],
            timestamp="2024-12-24T12:00:00"
        )

        assert report.total_rules == 10
        assert report.issues_count == 3
        assert len(report.healthy_rules) == 2

    def test_rule_health_report_to_json(self):
        """RuleHealthReport converts to JSON."""
        from governance.rule_quality import RuleHealthReport

        report = RuleHealthReport(
            total_rules=5,
            issues_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            issues=[],
            healthy_rules=["RULE-001"],
            timestamp="2024-12-24T12:00:00"
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert parsed["total_rules"] == 5
        assert parsed["issues_count"] == 0


class TestOrphanedRuleDetection:
    """Tests for orphaned rule detection."""

    def test_find_orphaned_rules_excludes_foundational(self):
        """Foundational rules (RULE-001, RULE-002) are not flagged as orphaned."""
        from governance.rule_quality import RuleQualityAnalyzer

        analyzer = RuleQualityAnalyzer()
        # Manually set cache to test logic without TypeDB
        analyzer._rules_cache = {
            "RULE-001": {"id": "RULE-001", "name": "Session Evidence", "status": "ACTIVE"},
            "RULE-002": {"id": "RULE-002", "name": "Architecture", "status": "ACTIVE"}
        }
        analyzer._dependencies_cache = {}
        analyzer._dependents_cache = {}

        issues = analyzer.find_orphaned_rules()

        orphan_ids = [i.rule_id for i in issues]
        assert "RULE-001" not in orphan_ids
        assert "RULE-002" not in orphan_ids

    def test_find_orphaned_rules_flags_non_foundational(self):
        """Non-foundational rules with no dependents are flagged."""
        from governance.rule_quality import RuleQualityAnalyzer, IssueType

        analyzer = RuleQualityAnalyzer()
        analyzer._rules_cache = {
            "RULE-001": {"id": "RULE-001", "name": "Session", "status": "ACTIVE"},
            "RULE-099": {"id": "RULE-099", "name": "Orphan", "status": "ACTIVE"}
        }
        analyzer._dependencies_cache = {"RULE-099": set()}
        analyzer._dependents_cache = {}

        issues = analyzer.find_orphaned_rules()

        assert len(issues) == 1
        assert issues[0].rule_id == "RULE-099"
        assert issues[0].issue_type == IssueType.ORPHANED


class TestShallowRuleDetection:
    """Tests for shallow rule detection."""

    def test_find_shallow_rules_detects_missing_attrs(self):
        """Rules missing required attributes are flagged."""
        from governance.rule_quality import RuleQualityAnalyzer, IssueType

        analyzer = RuleQualityAnalyzer()
        analyzer._rules_cache = {
            "RULE-001": {
                "id": "RULE-001",
                "name": "Complete Rule",
                "directive": "Do something",
                "category": "governance",
                "priority": "HIGH",
                "status": "ACTIVE"
            },
            "RULE-002": {
                "id": "RULE-002",
                "name": "Incomplete Rule",
                # Missing: directive, category, priority
                "status": "ACTIVE"
            }
        }

        issues = analyzer.find_shallow_rules()

        assert len(issues) == 1
        assert issues[0].rule_id == "RULE-002"
        assert issues[0].issue_type == IssueType.SHALLOW
        assert "directive" in issues[0].metadata["missing_attributes"]


class TestOverConnectedDetection:
    """Tests for over-connected rule detection."""

    def test_find_over_connected_rules(self):
        """Rules with too many dependencies are flagged."""
        from governance.rule_quality import RuleQualityAnalyzer, IssueType

        analyzer = RuleQualityAnalyzer()
        analyzer.MAX_DEPENDENCIES = 3  # Lower threshold for testing
        analyzer._rules_cache = {
            "RULE-001": {"id": "RULE-001", "name": "Normal", "status": "ACTIVE"},
            "RULE-002": {"id": "RULE-002", "name": "Over-connected", "status": "ACTIVE"}
        }
        analyzer._dependencies_cache = {
            "RULE-001": {"RULE-X"},
            "RULE-002": {"RULE-A", "RULE-B", "RULE-C", "RULE-D", "RULE-E"}  # 5 deps
        }
        analyzer._dependents_cache = {}

        issues = analyzer.find_over_connected_rules()

        assert len(issues) == 1
        assert issues[0].rule_id == "RULE-002"
        assert issues[0].issue_type == IssueType.OVER_CONNECTED
        assert issues[0].metadata["dependency_count"] == 5


class TestCircularDependencyDetection:
    """Tests for circular dependency detection."""

    def test_find_circular_dependencies_simple(self):
        """Simple A→B→A cycle is detected."""
        from governance.rule_quality import RuleQualityAnalyzer, IssueType

        analyzer = RuleQualityAnalyzer()
        analyzer._dependencies_cache = {
            "RULE-A": {"RULE-B"},
            "RULE-B": {"RULE-A"}  # Circular!
        }
        analyzer._dependents_cache = {}

        issues = analyzer.find_circular_dependencies()

        assert len(issues) >= 1
        assert any(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)

    def test_find_circular_dependencies_none(self):
        """No cycles when dependencies are acyclic."""
        from governance.rule_quality import RuleQualityAnalyzer

        analyzer = RuleQualityAnalyzer()
        analyzer._dependencies_cache = {
            "RULE-A": {"RULE-B"},
            "RULE-B": {"RULE-C"},
            "RULE-C": set()  # No cycle
        }
        analyzer._dependents_cache = {}

        issues = analyzer.find_circular_dependencies()

        assert len(issues) == 0


class TestImpactAnalysis:
    """Tests for rule impact analysis."""

    def test_get_rule_impact_returns_dict(self):
        """get_rule_impact returns impact dictionary."""
        from governance.rule_quality import RuleQualityAnalyzer

        analyzer = RuleQualityAnalyzer()
        analyzer._rules_cache = {
            "RULE-001": {
                "id": "RULE-001",
                "name": "Test Rule",
                "priority": "HIGH",
                "category": "governance",
                "status": "ACTIVE"
            }
        }
        analyzer._dependencies_cache = {"RULE-001": set()}
        analyzer._dependents_cache = {"RULE-001": {"RULE-002", "RULE-003"}}

        impact = analyzer.get_rule_impact("RULE-001")

        assert impact["rule_id"] == "RULE-001"
        assert "impact_score" in impact
        assert "recommendation" in impact
        assert len(impact["direct_dependents"]) == 2

    def test_impact_score_includes_priority(self):
        """Impact score accounts for rule priority."""
        from governance.rule_quality import RuleQualityAnalyzer

        analyzer = RuleQualityAnalyzer()
        analyzer._rules_cache = {
            "RULE-CRIT": {"id": "RULE-CRIT", "priority": "CRITICAL", "category": "test"},
            "RULE-LOW": {"id": "RULE-LOW", "priority": "LOW", "category": "test"}
        }
        analyzer._dependencies_cache = {}
        analyzer._dependents_cache = {}

        impact_crit = analyzer.get_rule_impact("RULE-CRIT")
        impact_low = analyzer.get_rule_impact("RULE-LOW")

        assert impact_crit["impact_score"] > impact_low["impact_score"]


class TestFullAnalysis:
    """Tests for full analysis report."""

    def test_analyze_returns_health_report(self):
        """analyze() returns RuleHealthReport."""
        from governance.rule_quality import RuleQualityAnalyzer, RuleHealthReport

        analyzer = RuleQualityAnalyzer()
        analyzer._rules_cache = {
            "RULE-001": {
                "id": "RULE-001",
                "name": "Complete",
                "directive": "Test",
                "category": "test",
                "priority": "HIGH",
                "status": "ACTIVE"
            }
        }
        analyzer._dependencies_cache = {}
        analyzer._dependents_cache = {}

        report = analyzer.analyze()

        assert isinstance(report, RuleHealthReport)
        assert report.total_rules == 1
        assert report.timestamp is not None


class TestMCPRuleQualityTools:
    """Tests for MCP rule quality tools."""

    def test_governance_analyze_rules_exists(self):
        """governance_analyze_rules MCP tool exists."""
        from governance.mcp_server import governance_analyze_rules
        assert governance_analyze_rules is not None
        assert callable(governance_analyze_rules)

    def test_governance_rule_impact_exists(self):
        """governance_rule_impact MCP tool exists."""
        from governance.mcp_server import governance_rule_impact
        assert governance_rule_impact is not None
        assert callable(governance_rule_impact)

    def test_governance_find_issues_exists(self):
        """governance_find_issues MCP tool exists."""
        from governance.mcp_server import governance_find_issues
        assert governance_find_issues is not None
        assert callable(governance_find_issues)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_analyze_rule_quality_returns_json(self):
        """analyze_rule_quality returns valid JSON."""
        from governance.rule_quality import analyze_rule_quality

        # Will return empty report or error without TypeDB
        result = analyze_rule_quality()
        parsed = json.loads(result)

        assert isinstance(parsed, dict)

    def test_find_rule_issues_returns_json(self):
        """find_rule_issues returns valid JSON."""
        from governance.rule_quality import find_rule_issues

        result = find_rule_issues("orphaned")
        parsed = json.loads(result)

        assert isinstance(parsed, (dict, list))
