"""
Unit tests for Orchestrator Conditional Routing Edges.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/edges.py module.
Tests: check_gate_decision, check_validation_result.
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
    """Tests for check_gate_decision()."""

    def test_continue_routes_to_backlog(self):
        assert check_gate_decision({"gate_decision": "continue"}) == "backlog"

    def test_stop_routes_to_complete(self):
        assert check_gate_decision({"gate_decision": "stop"}) == "complete"

    def test_missing_decision_routes_to_complete(self):
        assert check_gate_decision({}) == "complete"

    def test_none_routes_to_complete(self):
        assert check_gate_decision({"gate_decision": None}) == "complete"


# ---------------------------------------------------------------------------
# check_validation_result
# ---------------------------------------------------------------------------
class TestCheckValidationResult:
    """Tests for check_validation_result()."""

    def test_passed_no_gaps_completes_cycle(self):
        state = {"validation_passed": True, "gaps_discovered": []}
        assert check_validation_result(state) == "complete_cycle"

    def test_passed_with_gaps_injects(self):
        state = {"validation_passed": True, "gaps_discovered": ["GAP-1"]}
        assert check_validation_result(state) == "inject"

    def test_failed_with_retries_loops(self):
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_failed_retries_exhausted_parks(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES}
        assert check_validation_result(state) == "park_task"

    def test_at_max_minus_one_still_loops(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES - 1}
        assert check_validation_result(state) == "loop_to_spec"

    def test_max_retries_is_3(self):
        assert MAX_RETRIES == 3

    def test_none_validation_with_retries_loops(self):
        state = {"validation_passed": None, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_passed_truthy_gaps_injects(self):
        state = {"validation_passed": True, "gaps_discovered": ["GAP-X"]}
        assert check_validation_result(state) == "inject"
