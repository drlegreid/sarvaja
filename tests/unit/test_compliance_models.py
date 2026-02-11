"""
Unit tests for Workflow Compliance Models.

Per DOC-SIZE-01-v1: Tests for extracted workflow_compliance/models.py.
Tests: ComplianceCheck, ComplianceReport.
"""

import pytest
from datetime import datetime

from governance.workflow_compliance.models import (
    ComplianceCheck,
    ComplianceReport,
)


class TestComplianceCheck:
    """Tests for ComplianceCheck dataclass."""

    def test_minimal_creation(self):
        check = ComplianceCheck(
            rule_id="TEST-001", check_name="test", status="PASS",
            message="OK",
        )
        assert check.rule_id == "TEST-001"
        assert check.count == 0
        assert check.violations == []
        assert check.evidence is None

    def test_with_violations(self):
        check = ComplianceCheck(
            rule_id="TEST-001", check_name="test", status="FAIL",
            message="Bad", violations=["V-1", "V-2"],
        )
        assert len(check.violations) == 2

    def test_to_dict(self):
        check = ComplianceCheck(
            rule_id="TEST-001", check_name="test", status="PASS",
            message="OK", count=5,
        )
        d = check.to_dict()
        assert d["rule_id"] == "TEST-001"
        assert d["status"] == "PASS"
        assert d["count"] == 5
        assert "timestamp" in d

    def test_to_dict_caps_violations_at_10(self):
        check = ComplianceCheck(
            rule_id="TEST-001", check_name="test", status="FAIL",
            message="Bad", violations=[f"V-{i}" for i in range(15)],
        )
        d = check.to_dict()
        assert len(d["violations"]) == 10

    def test_timestamp_default(self):
        before = datetime.now()
        check = ComplianceCheck(
            rule_id="R-1", check_name="c", status="PASS", message="ok",
        )
        after = datetime.now()
        assert before <= check.timestamp <= after


class TestComplianceReport:
    """Tests for ComplianceReport dataclass."""

    def test_empty_report(self):
        report = ComplianceReport()
        assert report.overall_status == "UNKNOWN"
        assert report.passed == 0
        assert report.failed == 0
        assert report.checks == []

    def test_add_pass_check(self):
        report = ComplianceReport()
        check = ComplianceCheck(rule_id="R-1", check_name="c", status="PASS", message="ok")
        report.add_check(check)
        assert report.passed == 1
        assert report.failed == 0

    def test_add_fail_check(self):
        report = ComplianceReport()
        check = ComplianceCheck(rule_id="R-1", check_name="c", status="FAIL", message="bad")
        report.add_check(check)
        assert report.failed == 1

    def test_add_warning_check(self):
        report = ComplianceReport()
        check = ComplianceCheck(rule_id="R-1", check_name="c", status="WARNING", message="warn")
        report.add_check(check)
        assert report.warnings == 1

    def test_finalize_compliant(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck(rule_id="R-1", check_name="c", status="PASS", message="ok"))
        report.finalize()
        assert report.overall_status == "COMPLIANT"

    def test_finalize_violations(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck(rule_id="R-1", check_name="c", status="PASS", message="ok"))
        report.add_check(ComplianceCheck(rule_id="R-2", check_name="c", status="FAIL", message="bad"))
        report.finalize()
        assert report.overall_status == "VIOLATIONS"

    def test_finalize_warnings(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck(rule_id="R-1", check_name="c", status="PASS", message="ok"))
        report.add_check(ComplianceCheck(rule_id="R-2", check_name="c", status="WARNING", message="warn"))
        report.finalize()
        assert report.overall_status == "WARNINGS"

    def test_finalize_empty(self):
        report = ComplianceReport()
        report.finalize()
        assert report.overall_status == "UNKNOWN"

    def test_to_dict(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck(rule_id="R-1", check_name="c", status="PASS", message="ok"))
        report.finalize()
        d = report.to_dict()
        assert d["overall_status"] == "COMPLIANT"
        assert d["passed"] == 1
        assert len(d["checks"]) == 1
        assert "timestamp" in d
