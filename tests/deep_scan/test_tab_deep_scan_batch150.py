"""Deep scan batch 150: Workflow orchestrator engine.

Batch 150 findings: 6 total, 0 confirmed fixes, 6 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Cycle history completeness defense ──────────────


class TestCycleHistoryDefense:
    """Verify cycle_history captures necessary audit fields."""

    def test_history_captures_core_fields(self):
        """cycle_history captures task_id, spec, impl, validation."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "TASK-001", "priority": "HIGH"},
            "cycles_completed": 0,
            "cycle_history": [],
            "specification": {"task_id": "TASK-001", "title": "Test"},
            "implementation": {"code": "print('hello')"},
            "validation_results": {"passed": True},
            "validation_passed": True,
        }
        result = complete_cycle_node(state)
        history = result["cycle_history"]
        assert len(history) == 1
        entry = history[0]
        assert entry["task_id"] == "TASK-001"
        assert entry["specification"] is not None
        assert entry["implementation"] is not None
        assert entry["validation"] is not None

    def test_history_preserves_previous_entries(self):
        """New cycle appends to existing history."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        existing = [{"task_id": "TASK-000", "specification": {}}]
        state = {
            "current_task": {"task_id": "TASK-001", "priority": "LOW"},
            "cycles_completed": 1,
            "cycle_history": existing,
            "specification": None,
            "implementation": None,
            "validation_results": None,
        }
        result = complete_cycle_node(state)
        assert len(result["cycle_history"]) == 2

    def test_no_task_returns_error(self):
        """complete_cycle_node with no current_task returns error."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {"current_task": None, "cycles_completed": 0}
        result = complete_cycle_node(state)
        assert "error" in result.get("current_phase", "")


# ── State update merge defense ──────────────


class TestStateUpdateMergeDefense:
    """Verify state.update() preserves keys not in node return."""

    def test_update_preserves_unmentioned_keys(self):
        """dict.update() only overwrites keys present in source."""
        state = {
            "backlog": [{"task_id": "T1"}],
            "max_cycles": 10,
            "current_phase": "gate",
        }
        result = {"current_phase": "backlog", "current_task": {"task_id": "T1"}}
        state.update(result)
        assert state["backlog"] == [{"task_id": "T1"}]  # Preserved
        assert state["max_cycles"] == 10  # Preserved
        assert state["current_phase"] == "backlog"  # Updated

    def test_cleared_fields_become_none(self):
        """Fields explicitly set to None in result are cleared."""
        state = {"specification": {"title": "old"}, "current_task": {"id": "T1"}}
        result = {"specification": None, "current_task": None}
        state.update(result)
        assert state["specification"] is None
        assert state["current_task"] is None


# ── Budget computation defense ──────────────


class TestBudgetComputationDefense:
    """Verify budget thresholds are correctly computed."""

    def test_value_delivered_incremented(self):
        """Budget value_delivered incremented by task priority value."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "T1", "priority": "HIGH"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 5,
            "tokens_used": 20,
            "specification": None,
            "implementation": None,
            "validation_results": None,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] > 5  # HIGH = 3, so 5+3=8

    def test_tokens_used_incremented(self):
        """Budget tokens_used incremented by TOKEN_COST_PER_CYCLE."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        from governance.workflows.orchestrator.budget import TOKEN_COST_PER_CYCLE
        state = {
            "current_task": {"task_id": "T1", "priority": "MEDIUM"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 0,
            "specification": None,
            "implementation": None,
            "validation_results": None,
        }
        result = complete_cycle_node(state)
        assert result["tokens_used"] == TOKEN_COST_PER_CYCLE


# ── Spec tiers defense ──────────────


class TestSpecTiersDefense:
    """Verify spec generation produces valid output."""

    def test_generate_spec_returns_dict(self):
        """generate_spec returns dict with tier_1, tier_2, tier_3 keys."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        spec = generate_spec(
            task_id="T1", description="Add login feature",
            endpoint="/api/login", method="POST",
        )
        assert isinstance(spec, dict)
        assert "tier_1" in spec
        assert "tier_2" in spec
        assert "tier_3" in spec

    def test_generate_spec_tier1_has_feature(self):
        """Tier 1 spec includes Feature/user story."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        spec = generate_spec(
            task_id="T1", description="Add login",
            endpoint="/api/login", method="POST",
        )
        assert "Feature" in spec["tier_1"] or "feature" in spec["tier_1"].lower()

    def test_generate_spec_tier2_has_scenario(self):
        """Tier 2 spec includes Gherkin scenario."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        spec = generate_spec(
            task_id="T1", description="Add login",
            endpoint="/api/login", method="POST",
        )
        assert "Scenario" in spec["tier_2"] or "Given" in spec["tier_2"]
