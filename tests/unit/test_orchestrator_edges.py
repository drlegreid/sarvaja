"""
Unit tests for Orchestrator Conditional Routing Edges.

Per WORKFLOW-ORCH-01-v1: Tests for check_gate_decision and
check_validation_result edge functions.
"""

import pytest

from governance.workflows.orchestrator.edges import (
    check_gate_decision,
    check_validation_result,
)
from governance.workflows.orchestrator.state import MAX_RETRIES


# ---------------------------------------------------------------------------
# check_gate_decision
# ---------------------------------------------------------------------------
class TestCheckGateDecision:
    """Tests for check_gate_decision() edge."""

    def test_continue_routes_to_backlog(self):
        assert check_gate_decision({"gate_decision": "continue"}) == "backlog"

    def test_stop_routes_to_complete(self):
        assert check_gate_decision({"gate_decision": "stop"}) == "complete"

    def test_empty_routes_to_complete(self):
        assert check_gate_decision({}) == "complete"

    def test_none_routes_to_complete(self):
        assert check_gate_decision({"gate_decision": None}) == "complete"


# ---------------------------------------------------------------------------
# check_validation_result
# ---------------------------------------------------------------------------
class TestCheckValidationResult:
    """Tests for check_validation_result() edge."""

    def test_passed_no_gaps_completes(self):
        state = {"validation_passed": True}
        assert check_validation_result(state) == "complete_cycle"

    def test_passed_with_gaps_injects(self):
        state = {"validation_passed": True, "gaps_discovered": ["GAP-1"]}
        assert check_validation_result(state) == "inject"

    def test_failed_under_retry_limit(self):
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_failed_at_retry_limit(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES}
        assert check_validation_result(state) == "park_task"

    def test_failed_over_retry_limit(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES + 1}
        assert check_validation_result(state) == "park_task"

    def test_failed_no_retry_count(self):
        state = {"validation_passed": False}
        assert check_validation_result(state) == "loop_to_spec"

    def test_passed_empty_gaps_completes(self):
        state = {"validation_passed": True, "gaps_discovered": []}
        assert check_validation_result(state) == "complete_cycle"


# ---------------------------------------------------------------------------
# MAX_RETRIES constant
# ---------------------------------------------------------------------------
class TestMaxRetries:
    """Tests for MAX_RETRIES constant."""

    def test_max_retries_value(self):
        assert MAX_RETRIES == 3
