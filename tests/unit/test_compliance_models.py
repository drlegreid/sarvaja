"""
Unit tests for Workflow Compliance Models.

Per DOC-SIZE-01-v1: Tests for workflow_compliance/models.py module.
Tests: ComplianceCheck, ComplianceReport.
"""

from governance.workflow_compliance.models import ComplianceCheck, ComplianceReport


class TestComplianceCheck:
    def test_basic(self):
        c = ComplianceCheck(
            rule_id="R-001", check_name="test_check",
            status="PASS", message="All good",
        )
        assert c.rule_id == "R-001"
        assert c.status == "PASS"
        assert c.count == 0
        assert c.violations == []
        assert c.evidence is None

    def test_to_dict(self):
        c = ComplianceCheck(
            rule_id="R-001", check_name="test_check",
            status="FAIL", message="Bad", count=5,
            violations=["v1", "v2"],
        )
        d = c.to_dict()
        assert d["rule_id"] == "R-001"
        assert d["status"] == "FAIL"
        assert d["count"] == 5
        assert len(d["violations"]) == 2
        assert "timestamp" in d

    def test_violations_limited(self):
        c = ComplianceCheck(
            rule_id="R-001", check_name="t", status="FAIL",
            message="m", violations=[f"v{i}" for i in range(20)],
        )
        d = c.to_dict()
        assert len(d["violations"]) == 10  # capped at 10


class TestComplianceReport:
    def test_defaults(self):
        r = ComplianceReport()
        assert r.overall_status == "UNKNOWN"
        assert r.passed == 0
        assert r.failed == 0
        assert r.warnings == 0

    def test_add_check_pass(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="PASS", message="ok",
        ))
        assert r.passed == 1
        assert r.failed == 0

    def test_add_check_fail(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="FAIL", message="bad",
        ))
        assert r.failed == 1

    def test_add_check_warning(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="WARNING", message="warn",
        ))
        assert r.warnings == 1

    def test_finalize_compliant(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="PASS", message="ok",
        ))
        r.finalize()
        assert r.overall_status == "COMPLIANT"

    def test_finalize_violations(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="FAIL", message="bad",
        ))
        r.finalize()
        assert r.overall_status == "VIOLATIONS"

    def test_finalize_warnings(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="WARNING", message="warn",
        ))
        r.finalize()
        assert r.overall_status == "WARNINGS"

    def test_finalize_empty(self):
        r = ComplianceReport()
        r.finalize()
        assert r.overall_status == "UNKNOWN"

    def test_finalize_fail_overrides_warning(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c1", status="WARNING", message="w",
        ))
        r.add_check(ComplianceCheck(
            rule_id="R-2", check_name="c2", status="FAIL", message="f",
        ))
        r.finalize()
        assert r.overall_status == "VIOLATIONS"

    def test_to_dict(self):
        r = ComplianceReport()
        r.add_check(ComplianceCheck(
            rule_id="R-1", check_name="c", status="PASS", message="ok",
        ))
        r.recommendations = ["Improve coverage"]
        d = r.to_dict()
        assert d["passed"] == 1
        assert len(d["checks"]) == 1
        assert "Improve coverage" in d["recommendations"]
        assert "timestamp" in d
