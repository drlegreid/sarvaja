"""
TDD RED Phase: Tests for Orchestrator Dynamic Cycle Budget.

Per TEST-TDD-01-v1: Tests written BEFORE implementation.
Per WORKFLOW-ORCH-01-v1: Gate decision uses ROI-based budget.

The budget replaces static max_cycles with a dynamic decision based on:
  - Impact: priority-weighted value of remaining backlog
  - Progress: value already delivered vs total
  - Cost: token/resource usage per cycle (diminishing returns)
"""

import pytest


class TestPriorityValue:
    """Tests for priority-to-value mapping."""

    def test_critical_highest_value(self):
        from governance.workflows.orchestrator.budget import PRIORITY_VALUE
        assert PRIORITY_VALUE["CRITICAL"] > PRIORITY_VALUE["HIGH"]

    def test_value_ordering(self):
        from governance.workflows.orchestrator.budget import PRIORITY_VALUE
        assert (
            PRIORITY_VALUE["CRITICAL"]
            > PRIORITY_VALUE["HIGH"]
            > PRIORITY_VALUE["MEDIUM"]
            > PRIORITY_VALUE["LOW"]
        )


class TestComputeBudget:
    """Tests for the budget computation function."""

    def _make_state(self, backlog_priorities, cycles_done=0, token_budget=100):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        for i, pri in enumerate(backlog_priorities):
            state = add_to_backlog(state, f"T-{i}", pri, f"Task {i}")
        state["cycles_completed"] = cycles_done
        state["token_budget"] = token_budget
        state["tokens_used"] = cycles_done * 10
        state["value_delivered"] = 0
        return state

    def test_continue_with_high_value_backlog(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["CRITICAL", "HIGH"])
        result = compute_budget(state)
        assert result["should_continue"] is True

    def test_stop_on_empty_backlog(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state([])
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "backlog_empty"

    def test_stop_on_token_budget_exhausted(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["HIGH"], token_budget=100)
        state["tokens_used"] = 85  # >80% threshold
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert "token" in result["reason"]

    def test_stop_on_hard_cap(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["HIGH"], cycles_done=10)
        state["max_cycles"] = 10
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert "max_cycles" in result["reason"]

    def test_stop_when_only_low_and_past_half_budget(self):
        """LOW-only tasks aren't worth spending >50% budget on."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["LOW", "LOW", "LOW"], token_budget=100)
        state["tokens_used"] = 55  # >50%
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert "low_value" in result["reason"]

    def test_continue_when_low_but_budget_available(self):
        """LOW tasks still run if plenty of budget remains."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["LOW", "LOW"], token_budget=100)
        state["tokens_used"] = 10  # only 10%
        result = compute_budget(state)
        assert result["should_continue"] is True

    def test_remaining_value_computed(self):
        from governance.workflows.orchestrator.budget import (
            compute_budget, PRIORITY_VALUE,
        )
        state = self._make_state(["CRITICAL", "MEDIUM"])
        result = compute_budget(state)
        expected = PRIORITY_VALUE["CRITICAL"] + PRIORITY_VALUE["MEDIUM"]
        assert result["remaining_value"] == expected

    def test_roi_included_in_result(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["HIGH"])
        state["value_delivered"] = 10
        result = compute_budget(state)
        assert "roi" in result
        assert result["roi"] > 0

    def test_token_ratio_computed(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = self._make_state(["HIGH"], token_budget=100)
        state["tokens_used"] = 30
        result = compute_budget(state)
        assert result["token_ratio"] == pytest.approx(0.3)


class TestGateNodeWithBudget:
    """Tests that gate_node uses budget when token_budget is set."""

    def _make_state(self, backlog_priorities, token_budget=100):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        for i, pri in enumerate(backlog_priorities):
            state = add_to_backlog(state, f"T-{i}", pri, f"Task {i}")
        state["token_budget"] = token_budget
        state["tokens_used"] = 0
        state["value_delivered"] = 0
        return state

    def test_gate_uses_budget_when_token_budget_set(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = self._make_state(["HIGH"], token_budget=100)
        state["tokens_used"] = 90  # exhausted
        result = gate_node(state)
        assert result["gate_decision"] == "stop"
        assert "budget" in result.get("current_phase", "")

    def test_gate_continues_with_budget_available(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = self._make_state(["HIGH"], token_budget=100)
        state["tokens_used"] = 10
        result = gate_node(state)
        assert result["gate_decision"] == "continue"

    def test_gate_still_works_without_token_budget(self):
        """Backward compat: no token_budget = original behavior."""
        from governance.workflows.orchestrator.nodes import gate_node
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        state = add_to_backlog(state, "T-1", "HIGH", "Task")
        # No token_budget key at all
        result = gate_node(state)
        assert result["gate_decision"] == "continue"


class TestCompleteCycleTracksBudget:
    """Tests that complete_cycle_node updates budget tracking."""

    def test_value_delivered_incremented(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        from governance.workflows.orchestrator.budget import PRIORITY_VALUE
        state = {
            "current_task": {"task_id": "T-1", "priority": "HIGH",
                             "description": "Test"},
            "specification": {},
            "implementation": {},
            "validation_results": {},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 0,
        }
        result = complete_cycle_node(state)
        state.update(result)
        assert state["value_delivered"] == PRIORITY_VALUE["HIGH"]

    def test_tokens_used_incremented(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": {"task_id": "T-1", "priority": "MEDIUM",
                             "description": "Test"},
            "specification": {},
            "implementation": {},
            "validation_results": {},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 20,
        }
        result = complete_cycle_node(state)
        state.update(result)
        assert state["tokens_used"] > 20


class TestCertifyNode:
    """Tests for the certify node that produces impact summaries."""

    def test_certify_produces_certification(self):
        from governance.workflows.orchestrator.nodes import certify_node
        state = {
            "cycle_history": [
                {
                    "task_id": "GAP-001",
                    "implementation": {
                        "files_changed": ["a.py", "b.py"],
                        "summary": "Fixed GAP-001",
                    },
                },
                {
                    "task_id": "GAP-002",
                    "implementation": {
                        "files_changed": ["b.py", "c.py"],
                        "summary": "Fixed GAP-002",
                    },
                },
            ],
            "backlog": [{"task_id": "GAP-003"}],
        }
        result = certify_node(state)

        assert result["current_phase"] == "certified"
        cert = result["certification"]
        assert cert["cycles_completed"] == 2
        assert cert["tasks_completed"] == ["GAP-001", "GAP-002"]
        assert sorted(cert["files_changed"]) == ["a.py", "b.py", "c.py"]
        assert cert["remaining_backlog"] == 1
        assert "GAP-001" in cert["impact_summary"]

    def test_certify_tracks_parked_tasks(self):
        from governance.workflows.orchestrator.nodes import certify_node
        state = {
            "cycle_history": [
                {"task_id": "T-1", "implementation": {"summary": "Done"}},
                {"task_id": "T-2", "status": "parked", "reason": "exhausted_retries"},
            ],
            "backlog": [],
        }
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 1
        assert cert["cycles_parked"] == 1
        assert cert["tasks_parked"] == ["T-2"]

    def test_certify_includes_budget_metrics(self):
        from governance.workflows.orchestrator.nodes import certify_node
        state = {
            "cycle_history": [
                {"task_id": "T-1", "implementation": {"summary": "Done"}},
            ],
            "backlog": [],
            "value_delivered": 7,
            "tokens_used": 20,
            "token_budget": 100,
        }
        result = certify_node(state)
        cert = result["certification"]
        assert cert["value_delivered"] == 7
        assert cert["tokens_used"] == 20
        assert cert["budget_utilization"] == 20.0

    def test_orchestrator_run_includes_certification(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        state = add_to_backlog(state, "T-1", "HIGH", "Test task")
        result = run_orchestrator(state)

        assert "certification" in result
        assert result["certification"]["cycles_completed"] == 1
        assert result["certification"]["tasks_completed"] == ["T-1"]


class TestOrchestratorWithBudget:
    """Integration: orchestrator respects dynamic budget."""

    def test_orchestrator_stops_on_token_exhaustion(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True, max_cycles=20)
        for i in range(10):
            state = add_to_backlog(state, f"T-{i}", "HIGH", f"Task {i}")
        state["token_budget"] = 30  # very tight budget
        state["tokens_used"] = 0
        state["value_delivered"] = 0

        result = run_orchestrator(state)

        # Should stop before processing all 10 tasks
        assert result["cycles_completed"] < 10
        assert len(result["backlog"]) > 0

    def test_orchestrator_processes_all_if_budget_allows(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True, max_cycles=20)
        state = add_to_backlog(state, "A", "HIGH", "Task A")
        state = add_to_backlog(state, "B", "MEDIUM", "Task B")
        state["token_budget"] = 1000  # generous
        state["tokens_used"] = 0
        state["value_delivered"] = 0

        result = run_orchestrator(state)

        assert result["cycles_completed"] == 2
        assert len(result["backlog"]) == 0
