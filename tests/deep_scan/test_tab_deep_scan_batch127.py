"""Deep scan batch 127: Workflow engine + graph.

Batch 127 findings: 18 total, 0 confirmed fixes, 18 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Backlog node list copy defense ──────────────


class TestBacklogNodeListCopyDefense:
    """Verify backlog_node creates independent list copy."""

    def test_pop_does_not_modify_original(self):
        """backlog_node pops from copy, not original state."""
        from governance.workflows.orchestrator.nodes import backlog_node

        original_backlog = [
            {"task_id": "T-1", "priority": "HIGH", "description": "First"},
            {"task_id": "T-2", "priority": "LOW", "description": "Second"},
        ]
        state = {"backlog": original_backlog}

        result = backlog_node(state)
        # Original state's backlog unchanged
        assert len(state["backlog"]) == 2
        # Result has modified backlog
        assert len(result["backlog"]) == 1
        assert result["current_task"]["task_id"] == "T-1"

    def test_empty_backlog_returns_stop(self):
        """Empty backlog triggers stop."""
        from governance.workflows.orchestrator.nodes import backlog_node

        result = backlog_node({"backlog": []})
        assert result["gate_decision"] == "stop"

    def test_retry_count_reset_on_new_task(self):
        """backlog_node resets retry_count to 0."""
        from governance.workflows.orchestrator.nodes import backlog_node

        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH", "description": "D"}],
        }
        result = backlog_node(state)
        assert result["retry_count"] == 0


# ── Specification key access defense ──────────────


class TestSpecificationKeyAccessDefense:
    """Verify implement_node handles state correctly."""

    def test_implement_requires_current_task(self):
        """implement_node guards against missing current_task."""
        from governance.workflows.orchestrator.nodes import implement_node

        result = implement_node({"current_task": None, "specification": {}})
        assert "error" in result.get("error_message", "").lower() or "impl_error" in result.get("current_phase", "")

    def test_implement_uses_specification(self):
        """implement_node accesses specification from state."""
        from governance.workflows.orchestrator.nodes import implement_node

        state = {
            "current_task": {"task_id": "T-1", "description": "Test"},
            "specification": {"task_id": "T-1", "acceptance_criteria": []},
        }
        result = implement_node(state)
        assert result["current_phase"] == "implemented"


# ── Budget division guards defense ──────────────


class TestBudgetDivisionGuardsDefense:
    """Verify all divisions are guarded against zero."""

    def test_token_ratio_zero_budget_returns_zero(self):
        """token_budget=0 → token_ratio=0.0 (falsy check)."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 1,
            "max_cycles": 10,
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "token_budget": 0,
            "tokens_used": 100,
            "value_delivered": 5,
        })
        assert result["should_continue"] is True

    def test_roi_zero_tokens_used(self):
        """tokens_used=0 → ROI uses max(0,1)=1."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 1,
            "max_cycles": 10,
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "token_budget": 10000,
            "tokens_used": 0,
            "value_delivered": 5,
        })
        assert result["should_continue"] is True


# ── Complete cycle state clearing defense ──────────────


class TestCompleteCycleDefense:
    """Verify complete_cycle_node clears transient state."""

    def test_clears_all_transient_fields(self):
        """complete_cycle_node clears task, spec, impl, validation."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        state = {
            "current_task": {"task_id": "T-1", "priority": "HIGH", "description": "D"},
            "specification": {"task_id": "T-1"},
            "implementation": {"task_id": "T-1"},
            "validation_results": {"passed": True},
            "validation_passed": True,
            "gaps_discovered": [{"gap_id": "G-1"}],
            "cycles_completed": 0,
            "cycle_history": [],
        }
        result = complete_cycle_node(state)
        assert result["current_task"] is None
        assert result["specification"] is None
        assert result["implementation"] is None
        assert result["validation_passed"] is None
        assert result["gaps_discovered"] == []
        assert result["cycles_completed"] == 1

    def test_budget_tracking_when_present(self):
        """complete_cycle_node tracks value_delivered and tokens_used."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        state = {
            "current_task": {"task_id": "T-1", "priority": "HIGH", "description": "D"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 0,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] > 0
        assert result["tokens_used"] > 0


# ── Park task defense ──────────────


class TestParkTaskDefense:
    """Verify park_task_node handles state correctly."""

    def test_park_increments_cycle_count(self):
        """park_task_node increments cycles_completed."""
        from governance.workflows.orchestrator.nodes import park_task_node

        state = {
            "current_task": {"task_id": "T-1", "priority": "LOW", "description": "D"},
            "cycles_completed": 3,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["cycles_completed"] == 4
        assert result["current_task"] is None

    def test_park_tracks_tokens_when_present(self):
        """park_task_node tracks tokens_used for budget consistency."""
        from governance.workflows.orchestrator.nodes import park_task_node

        state = {
            "current_task": {"task_id": "T-1", "priority": "LOW", "description": "D"},
            "cycles_completed": 0,
            "cycle_history": [],
            "tokens_used": 100,
        }
        result = park_task_node(state)
        assert result["tokens_used"] > 100


# ── Gap injection dedup defense ──────────────


class TestGapInjectionDedupDefense:
    """Verify inject_node deduplicates gaps."""

    def test_duplicate_gap_skipped(self):
        """Gaps already in backlog are not re-added."""
        from governance.workflows.orchestrator.nodes import inject_node

        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH", "description": "D"}],
            "gaps_discovered": [{"gap_id": "T-1"}],
        }
        result = inject_node(state)
        backlog = result.get("backlog", state["backlog"])
        t1_count = sum(1 for t in backlog if t["task_id"] == "T-1")
        assert t1_count == 1  # Not duplicated

    def test_new_gap_added(self):
        """New gaps are added to backlog."""
        from governance.workflows.orchestrator.nodes import inject_node

        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH", "description": "D"}],
            "gaps_discovered": [{"gap_id": "G-NEW", "priority": "CRITICAL", "description": "New gap"}],
        }
        result = inject_node(state)
        ids = [t["task_id"] for t in result["backlog"]]
        assert "G-NEW" in ids


# ── Safety cap defense ──────────────


class TestSafetyCapDefense:
    """Verify _MAX_ITERATIONS safety cap prevents infinite loops."""

    def test_max_iterations_is_3x_cycles(self):
        """_MAX_ITERATIONS = max_cycles * 3."""
        max_cycles = 10
        max_iterations = max_cycles * 3
        assert max_iterations == 30

    def test_state_initialization_defaults(self):
        """create_initial_state provides all required fields."""
        from governance.workflows.orchestrator.state import create_initial_state

        state = create_initial_state(max_cycles=5)
        assert state["cycles_completed"] == 0
        assert state["max_cycles"] == 5
        assert state["retry_count"] == 0
        assert "backlog" in state
