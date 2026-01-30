"""
Tests for workflow compliance models.

Per UI-AUDIT-009: Compliance reporting data models.
Covers ComplianceCheck and ComplianceReport lifecycle.

Created: 2026-01-30
"""

import pytest
from datetime import datetime

from governance.workflow_compliance.models import ComplianceCheck, ComplianceReport


class TestComplianceCheck:
    """Test ComplianceCheck dataclass."""

    def test_minimal(self):
        check = ComplianceCheck(
            rule_id="RULE-001", check_name="has_evidence",
            status="PASS", message="Evidence found"
        )
        assert check.rule_id == "RULE-001"
        assert check.status == "PASS"
        assert check.count == 0
        assert check.violations == []
        assert check.evidence is None

    def test_with_violations(self):
        check = ComplianceCheck(
            rule_id="RULE-008", check_name="test_guard",
            status="FAIL", message="Tests missing",
            count=3, violations=["file1.py", "file2.py", "file3.py"]
        )
        assert check.count == 3
        assert len(check.violations) == 3

    def test_to_dict(self):
        check = ComplianceCheck(
            rule_id="R1", check_name="check1",
            status="PASS", message="OK"
        )
        d = check.to_dict()
        assert d["rule_id"] == "R1"
        assert d["status"] == "PASS"
        assert "timestamp" in d

    def test_to_dict_truncates_violations(self):
        """Violations truncated to 10 for UI."""
        check = ComplianceCheck(
            rule_id="R1", check_name="c1",
            status="FAIL", message="Many violations",
            violations=[f"v{i}" for i in range(20)]
        )
        d = check.to_dict()
        assert len(d["violations"]) == 10

    def test_timestamp_auto_set(self):
        check = ComplianceCheck(
            rule_id="R1", check_name="c1",
            status="PASS", message="OK"
        )
        assert isinstance(check.timestamp, datetime)

    def test_with_evidence(self):
        check = ComplianceCheck(
            rule_id="R1", check_name="c1",
            status="PASS", message="OK",
            evidence="pytest output: 100 passed"
        )
        assert check.evidence == "pytest output: 100 passed"


class TestComplianceReport:
    """Test ComplianceReport lifecycle."""

    def test_initial_state(self):
        report = ComplianceReport()
        assert report.overall_status == "UNKNOWN"
        assert report.passed == 0
        assert report.failed == 0
        assert report.warnings == 0
        assert report.checks == []

    def test_add_pass(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "PASS", "OK"))
        assert report.passed == 1
        assert report.failed == 0

    def test_add_fail(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "FAIL", "Bad"))
        assert report.failed == 1
        assert report.passed == 0

    def test_add_warning(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "WARNING", "Hmm"))
        assert report.warnings == 1

    def test_add_skip_no_counter(self):
        """SKIP status doesn't increment any counter."""
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "SKIP", "Skipped"))
        assert report.passed == 0
        assert report.failed == 0
        assert report.warnings == 0
        assert len(report.checks) == 1

    def test_finalize_compliant(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "PASS", "OK"))
        report.add_check(ComplianceCheck("R2", "c2", "PASS", "OK"))
        report.finalize()
        assert report.overall_status == "COMPLIANT"

    def test_finalize_violations(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "PASS", "OK"))
        report.add_check(ComplianceCheck("R2", "c2", "FAIL", "Bad"))
        report.finalize()
        assert report.overall_status == "VIOLATIONS"

    def test_finalize_warnings(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "PASS", "OK"))
        report.add_check(ComplianceCheck("R2", "c2", "WARNING", "Hmm"))
        report.finalize()
        assert report.overall_status == "WARNINGS"

    def test_finalize_unknown_no_checks(self):
        report = ComplianceReport()
        report.finalize()
        assert report.overall_status == "UNKNOWN"

    def test_finalize_fail_overrides_warning(self):
        """Failures take priority over warnings."""
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "WARNING", "W"))
        report.add_check(ComplianceCheck("R2", "c2", "FAIL", "F"))
        report.finalize()
        assert report.overall_status == "VIOLATIONS"

    def test_to_dict(self):
        report = ComplianceReport()
        report.add_check(ComplianceCheck("R1", "c1", "PASS", "OK"))
        report.finalize()
        d = report.to_dict()
        assert d["overall_status"] == "COMPLIANT"
        assert d["passed"] == 1
        assert len(d["checks"]) == 1
        assert "timestamp" in d

    def test_recommendations(self):
        report = ComplianceReport()
        report.recommendations = ["Add tests", "Fix linting"]
        d = report.to_dict()
        assert len(d["recommendations"]) == 2

    def test_multiple_checks_counted(self):
        report = ComplianceReport()
        for i in range(5):
            report.add_check(ComplianceCheck(f"R{i}", f"c{i}", "PASS", "OK"))
        report.add_check(ComplianceCheck("R5", "c5", "FAIL", "Bad"))
        report.add_check(ComplianceCheck("R6", "c6", "WARNING", "W"))
        assert report.passed == 5
        assert report.failed == 1
        assert report.warnings == 1
        assert len(report.checks) == 7
