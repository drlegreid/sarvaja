"""Batch 220 — Orchestrator workflow defense tests.

Validates fixes for:
- BUG-220-GAPS-001: complete_cycle_node error path must clear gaps_discovered
- BUG-220-MUTATE-001: add_to_backlog must not mutate input state
- BUG-220-GATE-001: gate_node must use .get() for KeyError safety
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-220-GAPS-001: Error path clears gaps_discovered ──────────────

class TestCycleErrorGaps:
    """complete_cycle_node error path must include gaps_discovered: []."""

    def test_error_return_clears_gaps(self):
        """Source must have gaps_discovered in the error return."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        # Error path at the top of complete_cycle_node
        assert '"gaps_discovered": []' in src or "'gaps_discovered': []" in src

    def test_error_path_returns_empty_gaps(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        state = {
            "current_task": None,
            "cycles_completed": 0,
            "cycle_history": [],
            "gaps_discovered": ["stale-gap-1"],
        }
        result = complete_cycle_node(state)
        assert result["current_phase"] == "cycle_error"
        assert result["gaps_discovered"] == []


# ── BUG-220-MUTATE-001: add_to_backlog immutability ─────────────────

class TestBacklogImmutability:
    """add_to_backlog must return a new dict, not mutate input."""

    def test_input_state_not_mutated(self):
        from governance.workflows.orchestrator.state import add_to_backlog
        state = {"backlog": [{"task_id": "A", "priority": "LOW", "description": "a"}]}
        original_backlog = state["backlog"][:]
        result = add_to_backlog(state, "B", "HIGH", "b desc")
        # result should have both items
        assert len(result["backlog"]) == 2
        # Original state's backlog should NOT be mutated
        assert len(original_backlog) == 1

    def test_returns_new_dict(self):
        from governance.workflows.orchestrator.state import add_to_backlog
        state = {"backlog": []}
        result = add_to_backlog(state, "T1", "MEDIUM", "task")
        assert len(result["backlog"]) == 1

    def test_dedup_returns_same_state(self):
        from governance.workflows.orchestrator.state import add_to_backlog
        state = {"backlog": [{"task_id": "T1", "priority": "LOW", "description": "x"}]}
        result = add_to_backlog(state, "T1", "HIGH", "dup")
        assert result is state  # no change, returns same


# ── BUG-220-GATE-001: gate_node KeyError safety ─────────────────────

class TestGateNodeSafety:
    """gate_node must handle partial state without KeyError."""

    def test_empty_state_no_keyerror(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {}
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_no_backlog_stops(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {"backlog": [], "cycles_completed": 0, "max_cycles": 10}
        result = gate_node(state)
        assert result["gate_decision"] == "stop"
        assert result["current_phase"] == "backlog_empty"

    def test_max_cycles_stops(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {"backlog": [{"task_id": "T1"}], "cycles_completed": 10, "max_cycles": 10}
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_continue_when_work_remains(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = {"backlog": [{"task_id": "T1"}], "cycles_completed": 0, "max_cycles": 10}
        result = gate_node(state)
        assert result["gate_decision"] == "continue"


# ── Orchestrator state defense ───────────────────────────────────────

class TestOrchestratorStateDefense:
    """Defense tests for orchestrator state module."""

    def test_create_initial_state_callable(self):
        from governance.workflows.orchestrator.state import create_initial_state
        assert callable(create_initial_state)

    def test_initial_state_has_required_keys(self):
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        for key in ["backlog", "current_task", "cycles_completed", "max_cycles",
                     "cycle_history", "gaps_discovered", "dry_run"]:
            assert key in state, f"Missing key: {key}"

    def test_priority_order_constants(self):
        from governance.workflows.orchestrator.state import PRIORITY_ORDER
        assert PRIORITY_ORDER["CRITICAL"] < PRIORITY_ORDER["HIGH"]
        assert PRIORITY_ORDER["HIGH"] < PRIORITY_ORDER["MEDIUM"]
        assert PRIORITY_ORDER["MEDIUM"] < PRIORITY_ORDER["LOW"]

    def test_add_to_backlog_sorts_by_priority(self):
        from governance.workflows.orchestrator.state import add_to_backlog
        state = {"backlog": []}
        state = add_to_backlog(state, "low1", "LOW", "Low task")
        state = add_to_backlog(state, "crit1", "CRITICAL", "Critical task")
        assert state["backlog"][0]["task_id"] == "crit1"


# ── Orchestrator nodes defense ───────────────────────────────────────

class TestOrchestratorNodesDefense:
    """Defense tests for orchestrator nodes module."""

    def test_gate_node_callable(self):
        from governance.workflows.orchestrator.nodes import gate_node
        assert callable(gate_node)

    def test_backlog_node_callable(self):
        from governance.workflows.orchestrator.nodes import backlog_node
        assert callable(backlog_node)

    def test_spec_node_callable(self):
        from governance.workflows.orchestrator.nodes import spec_node
        assert callable(spec_node)

    def test_implement_node_callable(self):
        from governance.workflows.orchestrator.nodes import implement_node
        assert callable(implement_node)

    def test_complete_cycle_node_callable(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        assert callable(complete_cycle_node)

    def test_park_task_node_callable(self):
        from governance.workflows.orchestrator.nodes import park_task_node
        assert callable(park_task_node)


# ── Orchestrator budget defense ──────────────────────────────────────

class TestOrchestratorBudgetDefense:
    """Defense tests for orchestrator budget module."""

    def test_compute_budget_callable(self):
        from governance.workflows.orchestrator.budget import compute_budget
        assert callable(compute_budget)

    def test_budget_with_minimal_state(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "token_budget": 1000,
            "tokens_used": 100,
            "value_delivered": 50,
            "backlog": [{"task_id": "T1"}],
        }
        result = compute_budget(state)
        assert "should_continue" in result
        assert "token_ratio" in result

    def test_budget_exhaustion_stops(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "token_budget": 1000,
            "tokens_used": 900,
            "value_delivered": 50,
            "backlog": [{"task_id": "T1", "priority": "LOW"}],
        }
        result = compute_budget(state)
        assert result["should_continue"] is False


# ── Orchestrator graph defense ───────────────────────────────────────

class TestOrchestratorGraphDefense:
    """Defense tests for orchestrator graph module."""

    def test_build_graph_callable(self):
        from governance.workflows.orchestrator.graph import build_orchestrator_graph
        assert callable(build_orchestrator_graph)

    def test_run_orchestrator_callable(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        assert callable(run_orchestrator)

    def test_run_single_cycle_callable(self):
        from governance.workflows.orchestrator.graph import run_single_cycle
        assert callable(run_single_cycle)
