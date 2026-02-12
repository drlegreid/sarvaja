"""
Unit tests for Orchestrator Conditional Routing Edges.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/edges.py module.
Tests: check_gate_decision(), check_validation_result().
"""

from governance.workflows.orchestrator.edges import (
    check_gate_decision,
    check_validation_result,
)
from governance.workflows.orchestrator.state import MAX_RETRIES


class TestCheckGateDecision:
    def test_continue(self):
        assert check_gate_decision({"gate_decision": "continue"}) == "backlog"

    def test_stop(self):
        assert check_gate_decision({"gate_decision": "stop"}) == "complete"

    def test_missing_key(self):
        assert check_gate_decision({}) == "complete"

    def test_none_value(self):
        assert check_gate_decision({"gate_decision": None}) == "complete"


class TestCheckValidationResult:
    def test_passed_no_gaps(self):
        state = {"validation_passed": True, "gaps_discovered": []}
        assert check_validation_result(state) == "complete_cycle"

    def test_passed_with_gaps(self):
        state = {"validation_passed": True, "gaps_discovered": ["GAP-001"]}
        assert check_validation_result(state) == "inject"

    def test_failed_retry_available(self):
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_failed_retry_at_limit(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES}
        assert check_validation_result(state) == "park_task"

    def test_failed_no_retry_count(self):
        state = {"validation_passed": False}
        assert check_validation_result(state) == "loop_to_spec"

    def test_failed_retry_below_max(self):
        state = {"validation_passed": False, "retry_count": MAX_RETRIES - 1}
        assert check_validation_result(state) == "loop_to_spec"

    def test_passed_gaps_none(self):
        state = {"validation_passed": True, "gaps_discovered": None}
        assert check_validation_result(state) == "complete_cycle"
