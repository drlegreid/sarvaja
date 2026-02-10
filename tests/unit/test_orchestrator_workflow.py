"""
TDD RED Phase: Unit tests for Orchestrator Continuous Workflow.

Per TEST-TDD-01-v1: Tests written BEFORE implementation.
Per WORKFLOW-ORCH-01-v1: Spec → Impl → Validate continuous loop.
Per TEST-STRUCT-01-v1: DRY/SRP/OOP, max 300 lines per file.

These tests MUST FAIL initially (RED phase).
Implementation comes next (GREEN phase).
"""

import pytest


class TestOrchestratorState:
    """Tests for orchestrator state creation and manipulation."""

    def test_create_initial_state_defaults(self):
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()

        assert state["cycle_id"].startswith("ORCH-")
        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["backlog"] == []
        assert state["cycles_completed"] == 0
        assert state["max_cycles"] == 10
        assert state["cycle_history"] == []
        assert state["dry_run"] is False

    def test_create_initial_state_with_options(self):
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(max_cycles=5, dry_run=True)

        assert state["max_cycles"] == 5
        assert state["dry_run"] is True

    def test_add_to_backlog(self):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state()
        state = add_to_backlog(
            state, task_id="GAP-001", priority="HIGH",
            description="Fix something",
        )

        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["task_id"] == "GAP-001"
        assert state["backlog"][0]["priority"] == "HIGH"

    def test_backlog_sorts_by_priority(self):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state()
        state = add_to_backlog(state, "LOW-1", "LOW", "Low task")
        state = add_to_backlog(state, "HIGH-1", "HIGH", "High task")
        state = add_to_backlog(state, "CRIT-1", "CRITICAL", "Critical task")
        state = add_to_backlog(state, "MED-1", "MEDIUM", "Medium task")

        assert state["backlog"][0]["task_id"] == "CRIT-1"
        assert state["backlog"][1]["task_id"] == "HIGH-1"
        assert state["backlog"][2]["task_id"] == "MED-1"
        assert state["backlog"][3]["task_id"] == "LOW-1"

    def test_add_to_backlog_rejects_duplicates(self):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state()
        state = add_to_backlog(state, "GAP-001", "HIGH", "First")
        state = add_to_backlog(state, "GAP-001", "HIGH", "Duplicate")

        assert len(state["backlog"]) == 1


class TestOrchestratorNodes:
    """Tests for individual orchestrator phase nodes."""

    def _make_state_with_backlog(self, *specs):
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        for spec in specs:
            tid, pri = spec.split(":")
            state = add_to_backlog(state, tid, pri, f"Task {tid}")
        return state

    # --- gate_node ---

    def test_gate_node_empty_backlog(self):
        from governance.workflows.orchestrator.state import create_initial_state
        from governance.workflows.orchestrator.nodes import gate_node
        state = create_initial_state()

        result = gate_node(state)

        assert result["current_phase"] == "backlog_empty"
        assert result["gate_decision"] == "stop"

    def test_gate_node_with_tasks(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = self._make_state_with_backlog("GAP-001:HIGH")

        result = gate_node(state)

        assert result["gate_decision"] == "continue"

    def test_gate_node_max_cycles_reached(self):
        from governance.workflows.orchestrator.nodes import gate_node
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state["cycles_completed"] = 10
        state["max_cycles"] = 10

        result = gate_node(state)

        assert result["gate_decision"] == "stop"
        assert result["current_phase"] == "max_cycles_reached"

    # --- backlog_node ---

    def test_backlog_node_picks_first(self):
        from governance.workflows.orchestrator.nodes import backlog_node
        state = self._make_state_with_backlog(
            "LOW-1:LOW", "CRIT-1:CRITICAL", "MED-1:MEDIUM",
        )

        result = backlog_node(state)

        assert result["current_task"]["task_id"] == "CRIT-1"
        assert result["current_phase"] == "task_selected"

    def test_backlog_node_removes_from_backlog(self):
        from governance.workflows.orchestrator.nodes import backlog_node
        state = self._make_state_with_backlog("A:HIGH", "B:MEDIUM")

        result = backlog_node(state)
        state.update(result)

        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["task_id"] == "B"

    # --- spec_node ---

    def test_spec_node_produces_specification(self):
        from governance.workflows.orchestrator.nodes import (
            backlog_node, spec_node,
        )
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state.update(backlog_node(state))

        result = spec_node(state)

        assert result["current_phase"] == "specified"
        assert "acceptance_criteria" in result["specification"]
        assert "files_to_modify" in result["specification"]
        assert len(result["specification"]["acceptance_criteria"]) > 0

    # --- implement_node ---

    def test_implement_node_records_changes(self):
        from governance.workflows.orchestrator.nodes import (
            backlog_node, spec_node, implement_node,
        )
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state.update(backlog_node(state))
        state.update(spec_node(state))

        result = implement_node(state)

        assert result["current_phase"] == "implemented"
        assert "files_changed" in result["implementation"]
        assert "summary" in result["implementation"]

    # --- validate_node ---

    def test_validate_node_runs_checks(self):
        from governance.workflows.orchestrator.nodes import (
            backlog_node, spec_node, implement_node, validate_node,
        )
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state.update(backlog_node(state))
        state.update(spec_node(state))
        state.update(implement_node(state))

        result = validate_node(state)

        assert result["current_phase"] == "validated"
        assert "tests_passed" in result["validation_results"]
        assert "heuristics_passed" in result["validation_results"]

    def test_validate_node_discovers_gaps(self):
        from governance.workflows.orchestrator.nodes import (
            backlog_node, spec_node, implement_node, validate_node,
        )
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state.update(backlog_node(state))
        state.update(spec_node(state))
        state.update(implement_node(state))
        state["_simulate_gap_discovery"] = True

        result = validate_node(state)

        assert len(result["gaps_discovered"]) > 0

    def test_validate_node_passes_in_dry_run(self):
        from governance.workflows.orchestrator.nodes import (
            backlog_node, spec_node, implement_node, validate_node,
        )
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state.update(backlog_node(state))
        state.update(spec_node(state))
        state.update(implement_node(state))

        result = validate_node(state)

        assert result["validation_passed"] is True

    # --- inject_node ---

    def test_inject_node_adds_gaps_to_backlog(self):
        from governance.workflows.orchestrator.nodes import inject_node
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state["gaps_discovered"] = [
            {"gap_id": "GAP-NEW-001", "priority": "MEDIUM",
             "description": "New gap from validation"},
        ]

        result = inject_node(state)
        state.update(result)

        ids = [t["task_id"] for t in state["backlog"]]
        assert "GAP-NEW-001" in ids

    def test_inject_node_skips_when_no_gaps(self):
        from governance.workflows.orchestrator.nodes import inject_node
        state = self._make_state_with_backlog("GAP-001:HIGH")
        state["gaps_discovered"] = []

        result = inject_node(state)

        assert result["current_phase"] == "no_gaps_to_inject"


class TestOrchestratorEdges:
    """Tests for orchestrator conditional routing."""

    def test_check_gate_decision_continue(self):
        from governance.workflows.orchestrator.edges import check_gate_decision
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["gate_decision"] = "continue"

        assert check_gate_decision(state) == "backlog"

    def test_check_gate_decision_stop(self):
        from governance.workflows.orchestrator.edges import check_gate_decision
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["gate_decision"] = "stop"

        assert check_gate_decision(state) == "complete"

    def test_check_validation_result_passed(self):
        from governance.workflows.orchestrator.edges import (
            check_validation_result,
        )
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["validation_passed"] = True
        state["gaps_discovered"] = []

        assert check_validation_result(state) == "complete_cycle"

    def test_check_validation_result_with_gaps(self):
        from governance.workflows.orchestrator.edges import (
            check_validation_result,
        )
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["validation_passed"] = True
        state["gaps_discovered"] = [{"gap_id": "NEW-1"}]

        assert check_validation_result(state) == "inject"

    def test_check_validation_result_failed_retries_remain(self):
        from governance.workflows.orchestrator.edges import (
            check_validation_result,
        )
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["validation_passed"] = False
        state["retry_count"] = 0

        assert check_validation_result(state) == "loop_to_spec"

    def test_check_validation_result_failed_exhausted(self):
        from governance.workflows.orchestrator.edges import (
            check_validation_result,
        )
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state()
        state["validation_passed"] = False
        state["retry_count"] = 3

        assert check_validation_result(state) == "park_task"


class TestOrchestratorGraph:
    """Tests for graph construction and full execution."""

    def test_build_graph_has_all_nodes(self):
        from governance.workflows.orchestrator.graph import (
            build_orchestrator_graph,
        )
        graph = build_orchestrator_graph()

        expected = [
            "gate", "backlog", "spec", "implement", "validate",
            "inject", "complete_cycle", "park_task", "certify", "complete",
        ]
        for node in expected:
            assert node in graph.nodes, f"Missing node: {node}"

    def test_run_orchestrator_empty_backlog(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(dry_run=True)

        result = run_orchestrator(state)

        assert result["status"] == "success"
        assert result["cycles_completed"] == 0

    def test_run_orchestrator_single_task(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        state = add_to_backlog(state, "GAP-001", "HIGH", "Test task")

        result = run_orchestrator(state)

        assert result["status"] == "success"
        assert result["cycles_completed"] == 1
        assert len(result["backlog"]) == 0

    def test_run_orchestrator_multiple_tasks(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True, max_cycles=5)
        state = add_to_backlog(state, "A", "HIGH", "Task A")
        state = add_to_backlog(state, "B", "CRITICAL", "Task B")
        state = add_to_backlog(state, "C", "MEDIUM", "Task C")

        result = run_orchestrator(state)

        assert result["status"] == "success"
        assert result["cycles_completed"] == 3
        # CRITICAL first
        assert result["cycle_history"][0]["task_id"] == "B"

    def test_run_orchestrator_respects_max_cycles(self):
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state, add_to_backlog,
        )
        state = create_initial_state(dry_run=True, max_cycles=2)
        for i in range(5):
            state = add_to_backlog(state, f"T-{i}", "HIGH", f"Task {i}")

        result = run_orchestrator(state)

        assert result["cycles_completed"] == 2
        assert len(result["backlog"]) == 3
