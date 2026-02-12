"""
Unit tests for SFDC LangGraph Conditional Edges.

Per DOC-SIZE-01-v1: Tests for sfdc/langgraph/edges.py module.
Tests: check_discover_status, check_phase_status, check_test_result,
       check_review_result, check_deploy_result, check_validation_result.
"""

from governance.sfdc.langgraph.edges import (
    check_discover_status,
    check_phase_status,
    check_test_result,
    check_review_result,
    check_deploy_result,
    check_validation_result,
)


class TestCheckDiscoverStatus:
    def test_normal(self):
        assert check_discover_status({}) == "develop"

    def test_breaking(self):
        assert check_discover_status({"has_breaking_changes": True}) == "skip_to_report"

    def test_failed(self):
        assert check_discover_status({"status": "failed"}) == "abort"


class TestCheckPhaseStatus:
    def test_continue(self):
        assert check_phase_status({}) == "continue"

    def test_failed(self):
        assert check_phase_status({"status": "failed"}) == "abort"


class TestCheckTestResult:
    def test_pass(self):
        assert check_test_result({"coverage_met": True}) == "continue"

    def test_fail_retry(self):
        assert check_test_result({"coverage_met": False, "retry_count": 0}) == "loop_to_develop"

    def test_fail_no_retry(self):
        assert check_test_result({"coverage_met": False, "retry_count": 3}) == "abort"

    def test_failed(self):
        assert check_test_result({"status": "failed"}) == "abort"


class TestCheckReviewResult:
    def test_pass(self):
        assert check_review_result({"security_scan_passed": True}) == "continue"

    def test_fail_retry(self):
        assert check_review_result({"security_scan_passed": False, "retry_count": 0}) == "loop_to_develop"

    def test_fail_no_retry(self):
        assert check_review_result({"security_scan_passed": False, "retry_count": 3}) == "abort"


class TestCheckDeployResult:
    def test_success(self):
        assert check_deploy_result({"deployment_status": "Succeeded"}) == "validate"

    def test_failed_deploy(self):
        assert check_deploy_result({"deployment_status": "Failed"}) == "rollback"

    def test_phase_failed(self):
        assert check_deploy_result({"status": "failed"}) == "abort"


class TestCheckValidationResult:
    def test_pass(self):
        assert check_validation_result({"validation_passed": True}) == "monitor"

    def test_fail(self):
        assert check_validation_result({"validation_passed": False}) == "rollback"

    def test_skip_monitor(self):
        assert check_validation_result({"validation_passed": True, "should_skip_monitor": True}) == "skip_monitor"

    def test_phase_failed(self):
        assert check_validation_result({"status": "failed"}) == "abort"
