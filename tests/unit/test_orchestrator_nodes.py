"""
Unit tests for Orchestrator Phase Nodes.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/nodes.py module.
Tests: gate_node, backlog_node, spec_node, implement_node, validate_node,
       inject_node, complete_cycle_node, park_task_node, certify_node, complete_node.
"""

from governance.workflows.orchestrator.nodes import (
    gate_node,
    backlog_node,
    spec_node,
    implement_node,
    validate_node,
    inject_node,
    complete_cycle_node,
    park_task_node,
    certify_node,
    complete_node,
)
from governance.workflows.orchestrator.state import create_initial_state, add_to_backlog


def _state_with_task(**extra):
    state = create_initial_state()
    state = add_to_backlog(state, "T-1", "HIGH", "Fix bug")
    state.update(extra)
    return state


class TestGateNode:
    def test_empty_backlog_stops(self):
        state = create_initial_state()
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_max_cycles_stops(self):
        state = _state_with_task(cycles_completed=10, max_cycles=10)
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_continues(self):
        state = _state_with_task()
        result = gate_node(state)
        assert result["gate_decision"] == "continue"

    def test_budget_exhausted(self):
        state = _state_with_task(token_budget=100, tokens_used=85)
        result = gate_node(state)
        assert result["gate_decision"] == "stop"

    def test_budget_available(self):
        state = _state_with_task(token_budget=100, tokens_used=10)
        result = gate_node(state)
        assert result["gate_decision"] == "continue"


class TestBacklogNode:
    def test_picks_first(self):
        state = _state_with_task()
        add_to_backlog(state, "T-2", "LOW", "Other")
        result = backlog_node(state)
        assert result["current_task"]["task_id"] == "T-1"
        assert len(result["backlog"]) == 1
        assert result["retry_count"] == 0

    def test_resets_retry(self):
        state = _state_with_task(retry_count=5)
        result = backlog_node(state)
        assert result["retry_count"] == 0


class TestSpecNode:
    def test_produces_spec(self):
        state = {"current_task": {"task_id": "T-1", "description": "Fix bug"}}
        result = spec_node(state)
        assert result["current_phase"] == "specified"
        assert result["specification"]["task_id"] == "T-1"
        assert len(result["specification"]["acceptance_criteria"]) == 3


class TestImplementNode:
    def test_produces_implementation(self):
        state = {
            "current_task": {"task_id": "T-1", "description": "Fix bug"},
            "specification": {"files_to_modify": ["a.py"]},
            "dry_run": True,
        }
        result = implement_node(state)
        assert result["current_phase"] == "implemented"
        assert result["implementation"]["dry_run"] is True
        assert result["implementation"]["files_changed"] == ["a.py"]


class TestValidateNode:
    def test_passes_by_default(self):
        state = {"current_task": {"task_id": "T-1", "description": "Fix bug"}}
        result = validate_node(state)
        assert result["validation_passed"] is True
        assert result["gaps_discovered"] == []

    def test_simulated_failure(self):
        state = {
            "current_task": {"task_id": "T-1", "description": "Fix bug"},
            "_simulate_validation_failure": True,
        }
        result = validate_node(state)
        assert result["validation_passed"] is False

    def test_gap_discovery(self):
        state = {
            "current_task": {"task_id": "T-1", "description": "Fix bug"},
            "_simulate_gap_discovery": True,
        }
        result = validate_node(state)
        assert len(result["gaps_discovered"]) == 1
        assert "GAP-DISC-T-1" in result["gaps_discovered"][0]["gap_id"]

    def test_generates_specs(self):
        state = {"current_task": {"task_id": "T-1", "description": "Fix bug"}}
        result = validate_node(state)
        assert "validation_specs" in result
        assert len(result["validation_specs"]) >= 1


class TestInjectNode:
    def test_no_gaps(self):
        state = {"gaps_discovered": [], "backlog": []}
        result = inject_node(state)
        assert result["current_phase"] == "no_gaps_to_inject"

    def test_injects_gaps(self):
        state = {
            "gaps_discovered": [
                {"gap_id": "GAP-1", "priority": "HIGH", "description": "New gap"},
            ],
            "backlog": [],
        }
        result = inject_node(state)
        assert len(result["backlog"]) == 1
        assert result["backlog"][0]["task_id"] == "GAP-1"

    def test_deduplicates(self):
        state = {
            "gaps_discovered": [
                {"gap_id": "GAP-1", "priority": "HIGH", "description": "Gap"},
            ],
            "backlog": [{"task_id": "GAP-1", "priority": "HIGH", "description": "Existing"}],
        }
        result = inject_node(state)
        assert len(result["backlog"]) == 1


class TestCompleteCycleNode:
    def test_increments_counter(self):
        state = {
            "current_task": {"task_id": "T-1"},
            "cycles_completed": 2,
            "cycle_history": [],
        }
        result = complete_cycle_node(state)
        assert result["cycles_completed"] == 3
        assert len(result["cycle_history"]) == 1
        assert result["current_task"] is None

    def test_budget_tracking(self):
        state = {
            "current_task": {"task_id": "T-1", "priority": "HIGH"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 0,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] == 3  # HIGH = 3
        assert result["tokens_used"] == 10     # TOKEN_COST_PER_CYCLE


class TestParkTaskNode:
    def test_parks_task(self):
        state = {
            "current_task": {"task_id": "T-1"},
            "cycles_completed": 5,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert result["current_phase"] == "task_parked"
        assert result["cycles_completed"] == 6
        assert result["current_task"] is None
        assert result["cycle_history"][0]["status"] == "parked"


class TestCertifyNode:
    def test_basic_certification(self):
        state = {
            "cycle_history": [
                {
                    "task_id": "T-1",
                    "implementation": {"files_changed": ["a.py"], "summary": "Fixed T-1"},
                },
            ],
            "backlog": [],
        }
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 1
        assert cert["cycles_parked"] == 0
        assert "T-1" in cert["tasks_completed"]
        assert "a.py" in cert["files_changed"]

    def test_with_parked(self):
        state = {
            "cycle_history": [
                {"task_id": "T-1", "implementation": {}},
                {"task_id": "T-2", "status": "parked"},
            ],
            "backlog": [],
        }
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 1
        assert cert["cycles_parked"] == 1
        assert "T-2" in cert["tasks_parked"]

    def test_budget_utilization(self):
        state = {
            "cycle_history": [],
            "backlog": [],
            "value_delivered": 10,
            "tokens_used": 50,
            "token_budget": 100,
        }
        result = certify_node(state)
        cert = result["certification"]
        assert cert["budget_utilization"] == 50.0


class TestCompleteNode:
    def test_marks_success(self):
        result = complete_node({})
        assert result["status"] == "success"
        assert result["current_phase"] == "complete"
