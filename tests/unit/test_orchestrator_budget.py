"""
Unit tests for Orchestrator Dynamic Budget.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/budget.py module.
Tests: compute_budget(), PRIORITY_VALUE, budget decisions.
"""

from governance.workflows.orchestrator.budget import (
    compute_budget,
    PRIORITY_VALUE,
    TOKEN_EXHAUSTION_THRESHOLD,
    LOW_VALUE_THRESHOLD,
)


class TestPriorityValue:
    def test_values(self):
        assert PRIORITY_VALUE["CRITICAL"] == 4
        assert PRIORITY_VALUE["HIGH"] == 3
        assert PRIORITY_VALUE["MEDIUM"] == 2
        assert PRIORITY_VALUE["LOW"] == 1


class TestComputeBudget:
    def test_empty_backlog(self):
        state = {"backlog": [], "cycles_completed": 0, "max_cycles": 10}
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "backlog_empty"

    def test_max_cycles_reached(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 10,
            "max_cycles": 10,
        }
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "max_cycles_reached"

    def test_budget_available(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 10,
        }
        result = compute_budget(state)
        assert result["should_continue"] is True
        assert result["reason"] == "budget_available"
        assert result["remaining_value"] == 3

    def test_token_budget_exhausted(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "CRITICAL"}],
            "cycles_completed": 5,
            "max_cycles": 20,
            "token_budget": 100,
            "tokens_used": 85,  # 85% > 80% threshold
        }
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "token_budget_exhausted"

    def test_low_value_remaining(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "LOW"}],
            "cycles_completed": 3,
            "max_cycles": 20,
            "token_budget": 100,
            "tokens_used": 55,  # 55% > 50% for LOW-only
        }
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "low_value_remaining"

    def test_low_but_under_threshold(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "LOW"}],
            "cycles_completed": 1,
            "max_cycles": 20,
            "token_budget": 100,
            "tokens_used": 30,  # 30% < 50%
        }
        result = compute_budget(state)
        assert result["should_continue"] is True

    def test_mixed_priorities_above_low_threshold(self):
        state = {
            "backlog": [
                {"task_id": "T-1", "priority": "HIGH"},
                {"task_id": "T-2", "priority": "LOW"},
            ],
            "cycles_completed": 3,
            "max_cycles": 20,
            "token_budget": 100,
            "tokens_used": 55,
        }
        result = compute_budget(state)
        # Not all LOW, so low_value check doesn't apply
        assert result["should_continue"] is True

    def test_remaining_value_calculation(self):
        state = {
            "backlog": [
                {"task_id": "T-1", "priority": "CRITICAL"},
                {"task_id": "T-2", "priority": "HIGH"},
                {"task_id": "T-3", "priority": "LOW"},
            ],
            "cycles_completed": 0,
            "max_cycles": 10,
        }
        result = compute_budget(state)
        assert result["remaining_value"] == 4 + 3 + 1  # 8

    def test_roi_calculation(self):
        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 2,
            "max_cycles": 10,
            "tokens_used": 50,
            "value_delivered": 10,
        }
        result = compute_budget(state)
        assert result["roi"] == 10 / 50

    def test_no_token_budget(self):
        # Without token_budget, should use static max_cycles
        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 5,
            "max_cycles": 10,
        }
        result = compute_budget(state)
        assert result["should_continue"] is True
        assert result["token_ratio"] == 0.0
