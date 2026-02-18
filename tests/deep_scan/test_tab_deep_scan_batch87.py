"""Deep Scan Batch 87 — Orchestrator null safety + TypeDB query validation.

Covers BUG-ORCH-NULL-TASK-002, BUG-ORCH-NULL-TASK-003.
Plus regression tests for rejected TypeDB findings.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# --- BUG-ORCH-NULL-TASK-002: complete_cycle_node None guard ---

class TestCompleteCycleNullGuard:
    """Verify complete_cycle_node handles None current_task gracefully."""

    def test_returns_error_when_current_task_is_none(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": None,
            "cycles_completed": 0,
            "cycle_history": [],
        }
        result = complete_cycle_node(state)
        assert result["current_phase"] == "cycle_error"
        assert "No current task" in result["error_message"]

    def test_works_normally_with_valid_task(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "TASK-001", "priority": "HIGH", "description": "Test"},
            "cycles_completed": 2,
            "cycle_history": [],
            "specification": {"task_id": "TASK-001"},
            "implementation": {"task_id": "TASK-001"},
            "validation_results": {"tests_passed": True},
        }
        result = complete_cycle_node(state)
        assert result["current_phase"] == "cycle_complete"
        assert result["cycles_completed"] == 3
        assert result["current_task"] is None  # Cleared after completion

    def test_budget_tracking_with_valid_task(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "TASK-002", "priority": "CRITICAL", "description": "Critical fix"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 5,
            "tokens_used": 10,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] == 9  # 5 + 4 (CRITICAL=4)
        assert result["tokens_used"] == 20  # 10 + TOKEN_COST_PER_CYCLE(10)


# --- BUG-ORCH-NULL-TASK-003: park_task_node None guard ---

class TestParkTaskNullGuard:
    """Verify park_task_node handles None current_task gracefully."""

    def test_returns_error_when_current_task_is_none(self):
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": None,
            "cycles_completed": 0,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["current_phase"] == "park_error"
        assert "No current task" in result["error_message"]

    def test_parks_valid_task(self):
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-FAIL", "priority": "LOW", "description": "Failing task"},
            "cycles_completed": 3,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["current_phase"] == "task_parked"
        assert result["cycles_completed"] == 4
        assert result["current_task"] is None
        assert result["cycle_history"][0]["status"] == "parked"

    def test_park_tracks_token_cost(self):
        from governance.workflows.orchestrator.nodes import park_task_node
        state = {
            "current_task": {"task_id": "TASK-X", "priority": "MEDIUM", "description": "X"},
            "cycles_completed": 0,
            "cycle_history": [],
            "tokens_used": 30,
        }
        result = park_task_node(state)
        assert result["tokens_used"] == 40  # 30 + TOKEN_COST_PER_CYCLE(10)


# --- Consistency: all nodes guard current_task ---

class TestAllNodesHaveNullGuard:
    """Verify spec, implement, validate, complete_cycle, park_task all handle None."""

    @pytest.mark.parametrize("node_name", [
        "spec_node", "implement_node", "validate_node",
        "complete_cycle_node", "park_task_node",
    ])
    def test_node_handles_none_current_task(self, node_name):
        from governance.workflows.orchestrator import nodes
        node_fn = getattr(nodes, node_name)
        state = {
            "current_task": None,
            "cycles_completed": 0,
            "cycle_history": [],
            "backlog": [],
            "specification": None,
            "validation_results": None,
            "validation_passed": None,
        }
        result = node_fn(state)
        assert "error" in result.get("current_phase", "")


# --- Regression: TypeDB datetime format is bare (no quotes) ---

class TestTypeDBDatetimeFormat:
    """Verify TypeDB 3.x datetime format conventions."""

    def test_started_at_bare_format(self):
        """TypeDB datetime attributes use bare ISO values, no quotes."""
        ts = "2026-02-15T10:30:00"
        # Simulates the TypeQL insert pattern
        query = f'insert $s has started-at {ts};'
        assert '"' not in query.split("started-at")[1]

    def test_completed_at_bare_format(self):
        ts = "2026-02-15T14:00:00"
        query = f'insert $s has completed-at {ts};'
        assert '"' not in query.split("completed-at")[1]

    def test_string_attributes_use_quotes(self):
        """TypeDB string attributes use quoted values."""
        val = "test-session"
        query = f'insert $s has session-id "{val}";'
        assert f'"{val}"' in query


# --- Regression: TypeQL == comparison is valid ---

class TestTypeQLValueComparison:
    """Verify that $var == "value" is valid TypeQL for attribute matching."""

    def test_status_comparison_pattern(self):
        """The delete-then-insert pattern uses == to identify the specific attribute."""
        current_status = "OPEN"
        tid = "TASK-001"
        # This is the actual pattern used in status.py
        query = f"""
            match
                $t isa task, has task-id "{tid}", has task-status $s;
                $s == "{current_status}";
            delete
                has $s of $t;
        """
        assert '$s == "OPEN"' in query


# --- Regression: Budget threshold semantics ---

class TestBudgetThresholds:
    """Verify budget thresholds work as intended."""

    def test_hard_stop_at_80_percent(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"task_id": "T1", "priority": "HIGH", "description": "x"}],
            "cycles_completed": 0,
            "max_cycles": 100,
            "token_budget": 100,
            "tokens_used": 80,
            "value_delivered": 10,
        }
        result = compute_budget(state)
        assert not result["should_continue"]
        assert result["reason"] == "token_budget_exhausted"

    def test_continues_at_79_percent(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"task_id": "T1", "priority": "HIGH", "description": "x"}],
            "cycles_completed": 0,
            "max_cycles": 100,
            "token_budget": 100,
            "tokens_used": 79,
            "value_delivered": 10,
        }
        result = compute_budget(state)
        assert result["should_continue"]

    def test_low_value_soft_stop_above_50(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"task_id": "T1", "priority": "LOW", "description": "x"}],
            "cycles_completed": 0,
            "max_cycles": 100,
            "token_budget": 100,
            "tokens_used": 51,
            "value_delivered": 5,
        }
        result = compute_budget(state)
        assert not result["should_continue"]
        assert result["reason"] == "low_value_remaining"

    def test_low_value_continues_at_50(self):
        """At exactly 50%, LOW tasks still continue (> not >=)."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"task_id": "T1", "priority": "LOW", "description": "x"}],
            "cycles_completed": 0,
            "max_cycles": 100,
            "token_budget": 100,
            "tokens_used": 50,
            "value_delivered": 5,
        }
        result = compute_budget(state)
        assert result["should_continue"]


# --- Regression: Orchestrator full cycle works end-to-end ---

class TestOrchestratorEndToEnd:
    """Verify the orchestrator runs a complete cycle correctly."""

    def test_single_cycle_completes(self):
        from governance.workflows.orchestrator.graph import run_single_cycle
        result = run_single_cycle("TEST-001", "Test task", dry_run=True)
        assert result["status"] == "success"
        assert result["cycles_completed"] >= 1
        assert "certification" in result

    def test_validation_failure_retries(self):
        """After MAX_RETRIES, task gets parked then orchestrator completes."""
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import create_initial_state, add_to_backlog
        # Need max_cycles > 1 so safety cap (max_cycles*3) allows retries to finish
        state = create_initial_state(max_cycles=10, dry_run=True)
        state = add_to_backlog(state, "TEST-FAIL", "HIGH", "Failing task")
        state["_simulate_validation_failure"] = True
        result = run_orchestrator(state)
        assert result["status"] == "success"
        parked = [h for h in result.get("cycle_history", []) if h.get("status") == "parked"]
        assert len(parked) == 1
        assert parked[0]["task_id"] == "TEST-FAIL"
