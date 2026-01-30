"""
Tests for governance quality models.

Per RULE-010, RULE-013: Quality analysis data models.
Covers IssueSeverity, IssueType, RuleIssue, and RuleHealthReport.

Created: 2026-01-30
"""

import json
import pytest

from governance.quality.models import (
    IssueSeverity,
    IssueType,
    RuleIssue,
    RuleHealthReport,
)


class TestIssueSeverity:
    """Test IssueSeverity enum."""

    def test_values(self):
        assert IssueSeverity.CRITICAL.value == "CRITICAL"
        assert IssueSeverity.HIGH.value == "HIGH"
        assert IssueSeverity.MEDIUM.value == "MEDIUM"
        assert IssueSeverity.LOW.value == "LOW"
        assert IssueSeverity.INFO.value == "INFO"

    def test_all_members(self):
        assert len(IssueSeverity) == 5


class TestIssueType:
    """Test IssueType enum."""

    def test_values(self):
        assert IssueType.ORPHANED.value == "orphaned"
        assert IssueType.SHALLOW.value == "shallow"
        assert IssueType.OVER_CONNECTED.value == "over_connected"
        assert IssueType.UNDER_DOCUMENTED.value == "under_documented"
        assert IssueType.CIRCULAR_DEPENDENCY.value == "circular"
        assert IssueType.STALE_REFERENCE.value == "stale_reference"
        assert IssueType.PRIORITY_MISMATCH.value == "priority_mismatch"
        assert IssueType.MISSING_DEPENDENCY.value == "missing_dependency"

    def test_all_members(self):
        assert len(IssueType) == 8


class TestRuleIssue:
    """Test RuleIssue dataclass."""

    def test_minimal(self):
        issue = RuleIssue(
            rule_id="RULE-001",
            issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.MEDIUM,
            description="No dependents",
            impact="May be unused",
            remediation="Add dependencies"
        )
        assert issue.rule_id == "RULE-001"
        assert issue.related_rules == []
        assert issue.metadata == {}

    def test_with_related_rules(self):
        issue = RuleIssue(
            rule_id="RULE-005",
            issue_type=IssueType.CIRCULAR_DEPENDENCY,
            severity=IssueSeverity.CRITICAL,
            description="A->B->A",
            impact="Infinite loop",
            remediation="Break cycle",
            related_rules=["RULE-005", "RULE-006", "RULE-005"]
        )
        assert len(issue.related_rules) == 3

    def test_with_metadata(self):
        issue = RuleIssue(
            rule_id="R1",
            issue_type=IssueType.OVER_CONNECTED,
            severity=IssueSeverity.MEDIUM,
            description="Too many deps",
            impact="High coupling",
            remediation="Split",
            metadata={"dependency_count": 8, "threshold": 5}
        )
        assert issue.metadata["dependency_count"] == 8

    def test_to_dict(self):
        issue = RuleIssue(
            rule_id="R1",
            issue_type=IssueType.SHALLOW,
            severity=IssueSeverity.HIGH,
            description="Missing attrs",
            impact="Incomplete",
            remediation="Add attrs",
            related_rules=["R2"],
            metadata={"missing": ["directive"]}
        )
        d = issue.to_dict()
        assert d["rule_id"] == "R1"
        assert d["issue_type"] == "shallow"
        assert d["severity"] == "HIGH"
        assert d["related_rules"] == ["R2"]
        assert d["metadata"]["missing"] == ["directive"]

    def test_to_dict_serializable(self):
        """to_dict output should be JSON serializable."""
        issue = RuleIssue(
            rule_id="R1", issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.LOW, description="D",
            impact="I", remediation="R"
        )
        json_str = json.dumps(issue.to_dict())
        assert "R1" in json_str


class TestRuleHealthReport:
    """Test RuleHealthReport dataclass."""

    def test_empty_report(self):
        report = RuleHealthReport(
            total_rules=50, issues_count=0,
            critical_count=0, high_count=0, medium_count=0, low_count=0,
            issues=[], healthy_rules=["R1", "R2"],
            timestamp="2026-01-30T10:00:00"
        )
        assert report.total_rules == 50
        assert report.issues_count == 0
        assert len(report.healthy_rules) == 2

    def test_with_issues(self):
        issue = RuleIssue(
            rule_id="R1", issue_type=IssueType.SHALLOW,
            severity=IssueSeverity.HIGH, description="D",
            impact="I", remediation="R"
        )
        report = RuleHealthReport(
            total_rules=10, issues_count=1,
            critical_count=0, high_count=1, medium_count=0, low_count=0,
            issues=[issue], healthy_rules=["R2", "R3"],
            timestamp="2026-01-30"
        )
        assert report.high_count == 1
        assert len(report.issues) == 1

    def test_to_dict(self):
        issue = RuleIssue(
            rule_id="R1", issue_type=IssueType.ORPHANED,
            severity=IssueSeverity.MEDIUM, description="D",
            impact="I", remediation="R"
        )
        report = RuleHealthReport(
            total_rules=5, issues_count=1,
            critical_count=0, high_count=0, medium_count=1, low_count=0,
            issues=[issue], healthy_rules=["R2"],
            timestamp="2026-01-30T12:00:00"
        )
        d = report.to_dict()
        assert d["total_rules"] == 5
        assert len(d["issues"]) == 1
        assert d["issues"][0]["rule_id"] == "R1"
        assert d["timestamp"] == "2026-01-30T12:00:00"

    def test_to_json(self):
        report = RuleHealthReport(
            total_rules=0, issues_count=0,
            critical_count=0, high_count=0, medium_count=0, low_count=0,
            issues=[], healthy_rules=[],
            timestamp="2026-01-30"
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["total_rules"] == 0
        assert isinstance(parsed["issues"], list)

    def test_to_json_with_issues(self):
        issues = [
            RuleIssue(rule_id=f"R{i}", issue_type=IssueType.ORPHANED,
                     severity=IssueSeverity.LOW, description="D",
                     impact="I", remediation="R")
            for i in range(3)
        ]
        report = RuleHealthReport(
            total_rules=10, issues_count=3,
            critical_count=0, high_count=0, medium_count=0, low_count=3,
            issues=issues, healthy_rules=["R3", "R4"],
            timestamp="2026-01-30"
        )
        parsed = json.loads(report.to_json())
        assert len(parsed["issues"]) == 3
        assert parsed["low_count"] == 3
