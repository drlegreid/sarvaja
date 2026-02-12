"""
Unit tests for DSP LangGraph Conditional Edges.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/edges.py module.
Tests: check_start_status, check_audit_result, check_phase_status,
       check_validation_result, check_should_skip_dream, check_report_status.
"""

import pytest

from governance.dsm.langgraph.edges import (
    check_start_status,
    check_audit_result,
    check_phase_status,
    check_validation_result,
    check_should_skip_dream,
    check_report_status,
)
from governance.dsm.langgraph.state import MAX_PHASE_RETRIES


# ---------------------------------------------------------------------------
# check_start_status
# ---------------------------------------------------------------------------
class TestCheckStartStatus:
    """Tests for check_start_status()."""

    def test_success_routes_to_audit(self):
        assert check_start_status({"status": "running"}) == "audit"

    def test_failed_routes_to_abort(self):
        assert check_start_status({"status": "failed"}) == "abort"

    def test_empty_state_routes_to_audit(self):
        assert check_start_status({}) == "audit"


# ---------------------------------------------------------------------------
# check_audit_result
# ---------------------------------------------------------------------------
class TestCheckAuditResult:
    """Tests for check_audit_result()."""

    def test_normal_flow_to_hypothesize(self):
        assert check_audit_result({"status": "running"}) == "hypothesize"

    def test_failed_routes_to_abort(self):
        assert check_audit_result({"status": "failed"}) == "abort"

    def test_critical_gaps_skip_to_report(self):
        state = {"status": "running", "has_critical_gaps": True}
        assert check_audit_result(state) == "skip_to_report"

    def test_no_critical_gaps(self):
        state = {"status": "running", "has_critical_gaps": False}
        assert check_audit_result(state) == "hypothesize"

    def test_empty_state(self):
        assert check_audit_result({}) == "hypothesize"


# ---------------------------------------------------------------------------
# check_phase_status
# ---------------------------------------------------------------------------
class TestCheckPhaseStatus:
    """Tests for check_phase_status()."""

    def test_continue_on_success(self):
        assert check_phase_status({"status": "running"}) == "continue"

    def test_abort_on_failure(self):
        assert check_phase_status({"status": "failed"}) == "abort"

    def test_empty_state_continues(self):
        assert check_phase_status({}) == "continue"


# ---------------------------------------------------------------------------
# check_validation_result
# ---------------------------------------------------------------------------
class TestCheckValidationResult:
    """Tests for check_validation_result()."""

    def test_passed_routes_to_dream(self):
        state = {"validation_passed": True}
        assert check_validation_result(state) == "dream"

    def test_failed_routes_to_abort(self):
        state = {"status": "failed"}
        assert check_validation_result(state) == "abort"

    def test_not_passed_with_retries_loops(self):
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_hypothesize"

    def test_not_passed_retries_exhausted_reports(self):
        state = {"validation_passed": False, "retry_count": MAX_PHASE_RETRIES}
        assert check_validation_result(state) == "report"

    def test_not_passed_at_max_minus_one_still_loops(self):
        state = {"validation_passed": False, "retry_count": MAX_PHASE_RETRIES - 1}
        assert check_validation_result(state) == "loop_to_hypothesize"

    def test_no_validation_key_loops(self):
        state = {"retry_count": 0}
        assert check_validation_result(state) == "loop_to_hypothesize"

    def test_max_phase_retries_is_3(self):
        assert MAX_PHASE_RETRIES == 3


# ---------------------------------------------------------------------------
# check_should_skip_dream
# ---------------------------------------------------------------------------
class TestCheckShouldSkipDream:
    """Tests for check_should_skip_dream()."""

    def test_skip_routes_to_report(self):
        assert check_should_skip_dream({"should_skip_dream": True}) == "report"

    def test_no_skip_routes_to_dream(self):
        assert check_should_skip_dream({"should_skip_dream": False}) == "dream"

    def test_empty_state_routes_to_dream(self):
        assert check_should_skip_dream({}) == "dream"


# ---------------------------------------------------------------------------
# check_report_status
# ---------------------------------------------------------------------------
class TestCheckReportStatus:
    """Tests for check_report_status()."""

    def test_always_returns_complete(self):
        assert check_report_status({}) == "complete"
        assert check_report_status({"status": "failed"}) == "complete"
        assert check_report_status({"whatever": True}) == "complete"
