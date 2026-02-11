"""
Unit tests for Rules Curator Agent Models.

Per DOC-SIZE-01-v1: Tests for extracted curator_models.py module.
Tests: CurationAction, IssueSeverity, RuleIssue, CurationResult, ConflictResolution.
"""

import pytest
from datetime import datetime

from agent.orchestrator.curator_models import (
    CurationAction,
    IssueSeverity,
    RuleIssue,
    CurationResult,
    ConflictResolution,
)


class TestCurationAction:
    """Tests for CurationAction enum."""

    def test_values(self):
        assert CurationAction.ANALYZE_QUALITY.value == "analyze_quality"
        assert CurationAction.RESOLVE_CONFLICT.value == "resolve_conflict"
        assert CurationAction.FIND_ORPHANS.value == "find_orphans"
        assert CurationAction.CHECK_DEPENDENCIES.value == "check_dependencies"
        assert CurationAction.VALIDATE_RULE.value == "validate_rule"
        assert CurationAction.PROPOSE_CHANGE.value == "propose_change"

    def test_member_count(self):
        assert len(CurationAction) == 6


class TestIssueSeverity:
    """Tests for IssueSeverity enum."""

    def test_values(self):
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.LOW.value == "low"

    def test_member_count(self):
        assert len(IssueSeverity) == 4


class TestRuleIssue:
    """Tests for RuleIssue dataclass."""

    def test_basic_creation(self):
        issue = RuleIssue(
            issue_id="ISSUE-001",
            rule_id="RULE-001",
            issue_type="orphaned",
            severity=IssueSeverity.LOW,
            description="Rule has no dependencies",
            recommendation="Link to parent rule",
        )
        assert issue.issue_id == "ISSUE-001"
        assert issue.rule_id == "RULE-001"
        assert issue.issue_type == "orphaned"
        assert issue.severity == IssueSeverity.LOW
        assert issue.resolved is False
        assert issue.resolved_at is None

    def test_detected_at_auto_populated(self):
        before = datetime.now().isoformat()
        issue = RuleIssue(
            issue_id="ISSUE-002",
            rule_id="RULE-002",
            issue_type="conflict",
            severity=IssueSeverity.HIGH,
            description="Conflicts with RULE-003",
            recommendation="Merge rules",
        )
        after = datetime.now().isoformat()
        assert before <= issue.detected_at <= after

    def test_resolved_fields(self):
        issue = RuleIssue(
            issue_id="ISSUE-003",
            rule_id="RULE-003",
            issue_type="stale",
            severity=IssueSeverity.MEDIUM,
            description="Not updated in 90 days",
            recommendation="Review and update",
            resolved=True,
            resolved_at="2026-02-11T10:00:00",
        )
        assert issue.resolved is True
        assert issue.resolved_at == "2026-02-11T10:00:00"

    def test_all_severity_levels(self):
        for sev in IssueSeverity:
            issue = RuleIssue(
                issue_id=f"ISSUE-{sev.name}",
                rule_id="R-1",
                issue_type="test",
                severity=sev,
                description="test",
                recommendation="test",
            )
            assert issue.severity == sev


class TestCurationResult:
    """Tests for CurationResult dataclass."""

    def test_success_result(self):
        result = CurationResult(
            action=CurationAction.ANALYZE_QUALITY,
            success=True,
            issues_found=[],
            issues_resolved=0,
            message="Quality check passed",
        )
        assert result.success is True
        assert result.action == CurationAction.ANALYZE_QUALITY
        assert result.issues_found == []
        assert result.evidence is None

    def test_result_with_issues(self):
        issue = RuleIssue(
            issue_id="I-1", rule_id="R-1", issue_type="orphan",
            severity=IssueSeverity.LOW, description="d", recommendation="r",
        )
        result = CurationResult(
            action=CurationAction.FIND_ORPHANS,
            success=True,
            issues_found=[issue],
            issues_resolved=0,
            message="Found 1 orphan",
            evidence="evidence/curation-run.md",
        )
        assert len(result.issues_found) == 1
        assert result.issues_found[0].issue_id == "I-1"
        assert result.evidence == "evidence/curation-run.md"

    def test_defaults(self):
        result = CurationResult(
            action=CurationAction.VALIDATE_RULE,
            success=False,
        )
        assert result.issues_found == []
        assert result.issues_resolved == 0
        assert result.message == ""
        assert result.evidence is None


class TestConflictResolution:
    """Tests for ConflictResolution dataclass."""

    def test_basic(self):
        res = ConflictResolution(
            conflict_id="CONFLICT-001",
            rule_a="CONTAINER-SHELL-01",
            rule_b="WORKFLOW-SHELL-01",
            resolution_type="merge",
            rationale="Both rules cover shell command usage",
        )
        assert res.conflict_id == "CONFLICT-001"
        assert res.rule_a == "CONTAINER-SHELL-01"
        assert res.rule_b == "WORKFLOW-SHELL-01"
        assert res.resolution_type == "merge"
        assert res.proposed_changes == {}

    def test_with_proposed_changes(self):
        res = ConflictResolution(
            conflict_id="CONFLICT-002",
            rule_a="GOV-TRUST-01",
            rule_b="REPORT-DEC-01",
            resolution_type="update",
            rationale="Overlap in trust reporting",
            proposed_changes={"GOV-TRUST-01": {"add_reference": "REPORT-DEC-01"}},
        )
        assert res.proposed_changes["GOV-TRUST-01"]["add_reference"] == "REPORT-DEC-01"

    def test_resolution_types(self):
        for res_type in ["merge", "deprecate", "update", "escalate"]:
            res = ConflictResolution(
                conflict_id=f"C-{res_type}",
                rule_a="A", rule_b="B",
                resolution_type=res_type,
                rationale="test",
            )
            assert res.resolution_type == res_type
