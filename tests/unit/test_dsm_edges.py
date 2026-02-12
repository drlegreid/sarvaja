"""
Unit tests for DSP LangGraph Conditional Edges.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/edges.py module.
Tests: check_start_status, check_audit_result, check_phase_status,
       check_validation_result, check_should_skip_dream, check_report_status.
"""

from governance.dsm.langgraph.edges import (
    check_start_status,
    check_audit_result,
    check_phase_status,
    check_validation_result,
    check_should_skip_dream,
    check_report_status,
)


class TestCheckStartStatus:
    def test_success(self):
        assert check_start_status({"status": "running"}) == "audit"

    def test_failed(self):
        assert check_start_status({"status": "failed"}) == "abort"


class TestCheckAuditResult:
    def test_normal(self):
        assert check_audit_result({"status": "running"}) == "hypothesize"

    def test_critical_gaps(self):
        assert check_audit_result({"has_critical_gaps": True}) == "skip_to_report"

    def test_failed(self):
        assert check_audit_result({"status": "failed"}) == "abort"


class TestCheckPhaseStatus:
    def test_continue(self):
        assert check_phase_status({"status": "running"}) == "continue"

    def test_failed(self):
        assert check_phase_status({"status": "failed"}) == "abort"


class TestCheckValidationResult:
    def test_passed(self):
        assert check_validation_result({"validation_passed": True}) == "dream"

    def test_failed_with_retries(self):
        assert check_validation_result({"validation_passed": False, "retry_count": 0}) == "loop_to_hypothesize"

    def test_failed_no_retries(self):
        assert check_validation_result({"validation_passed": False, "retry_count": 3}) == "report"

    def test_phase_failed(self):
        assert check_validation_result({"status": "failed"}) == "abort"


class TestCheckShouldSkipDream:
    def test_skip(self):
        assert check_should_skip_dream({"should_skip_dream": True}) == "report"

    def test_normal(self):
        assert check_should_skip_dream({"should_skip_dream": False}) == "dream"

    def test_default(self):
        assert check_should_skip_dream({}) == "dream"


class TestCheckReportStatus:
    def test_always_complete(self):
        assert check_report_status({}) == "complete"
