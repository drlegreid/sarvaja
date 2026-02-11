"""
Unit tests for Orchestrator Phase Nodes.

Per WORKFLOW-ORCH-01-v1: Tests for all 10 node functions that transform
orchestrator state through the continuous Spec -> Impl -> Validate loop.
"""

import pytest
from unittest.mock import patch, MagicMock

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


def _make_task(task_id="T-1", priority="HIGH", description="Fix bug"):
    return {"task_id": task_id, "priority": priority, "description": description}


def _base_state(**overrides):
    """Minimal valid orchestrator state."""
    s = {
        "backlog": [_make_task()],
        "current_task": _make_task(),
        "current_phase": "idle",
        "cycles_completed": 0,
        "max_cycles": 10,
        "specification": None,
        "implementation": None,
        "validation_results": None,
        "validation_passed": None,
        "gaps_discovered": [],
        "cycle_history": [],
        "retry_count": 0,
        "dry_run": False,
    }
    s.update(overrides)
    return s


# ---------------------------------------------------------------------------
# gate_node
# ---------------------------------------------------------------------------
class TestGateNode:
    """Tests for gate_node() — controls loop continuation."""

    def test_empty_backlog_stops(self):
        state = _base_state(backlog=[])
        result = gate_node(state)
        assert result["gate_decision"] == "stop"
        assert result["current_phase"] == "backlog_empty"

    def test_max_cycles_reached_stops(self):
        state = _base_state(cycles_completed=10, max_cycles=10)
        result = gate_node(state)
        assert result["gate_decision"] == "stop"
        assert result["current_phase"] == "max_cycles_reached"

    def test_under_max_cycles_continues(self):
        state = _base_state(cycles_completed=3, max_cycles=10)
        result = gate_node(state)
        assert result["gate_decision"] == "continue"

    def test_dynamic_budget_stop(self):
        state = _base_state(
            token_budget=100,
            tokens_used=90,
            value_delivered=5,
        )
        with patch(
            "governance.workflows.orchestrator.budget.compute_budget",
            return_value={"should_continue": False, "reason": "token_budget_exhausted"},
        ):
            result = gate_node(state)
        assert result["gate_decision"] == "stop"
        assert "budget_token_budget_exhausted" in result["current_phase"]
        assert "budget" in result

    def test_dynamic_budget_continue(self):
        state = _base_state(
            token_budget=100,
            tokens_used=10,
            value_delivered=5,
        )
        with patch(
            "governance.workflows.orchestrator.budget.compute_budget",
            return_value={"should_continue": True, "reason": "budget_available"},
        ):
            result = gate_node(state)
        assert result["gate_decision"] == "continue"

    def test_no_token_budget_skips_dynamic(self):
        """Without token_budget key, dynamic budget is never checked."""
        state = _base_state(cycles_completed=0)
        # No "token_budget" key — should not call compute_budget
        result = gate_node(state)
        assert result["gate_decision"] == "continue"


# ---------------------------------------------------------------------------
# backlog_node
# ---------------------------------------------------------------------------
class TestBacklogNode:
    """Tests for backlog_node() — picks highest priority task."""

    def test_picks_first_task(self):
        t1 = _make_task("T-1", "HIGH", "First")
        t2 = _make_task("T-2", "LOW", "Second")
        state = _base_state(backlog=[t1, t2])
        result = backlog_node(state)
        assert result["current_task"] == t1
        assert result["backlog"] == [t2]
        assert result["current_phase"] == "task_selected"
        assert result["retry_count"] == 0

    def test_single_task_empties_backlog(self):
        t1 = _make_task("T-1")
        state = _base_state(backlog=[t1])
        result = backlog_node(state)
        assert result["current_task"] == t1
        assert result["backlog"] == []

    def test_does_not_mutate_original_backlog(self):
        t1 = _make_task("T-1")
        t2 = _make_task("T-2")
        original_backlog = [t1, t2]
        state = _base_state(backlog=original_backlog)
        backlog_node(state)
        assert len(original_backlog) == 2


# ---------------------------------------------------------------------------
# spec_node
# ---------------------------------------------------------------------------
class TestSpecNode:
    """Tests for spec_node() — generates specification."""

    def test_basic_spec(self):
        task = _make_task("T-42", "HIGH", "Fix auth bug")
        state = _base_state(current_task=task)
        result = spec_node(state)
        assert result["current_phase"] == "specified"
        spec = result["specification"]
        assert spec["task_id"] == "T-42"
        assert spec["description"] == "Fix auth bug"
        assert len(spec["acceptance_criteria"]) == 3
        assert "T-42" in spec["acceptance_criteria"][0]

    def test_files_to_modify(self):
        task = _make_task("T-99")
        state = _base_state(current_task=task)
        result = spec_node(state)
        spec = result["specification"]
        assert len(spec["files_to_modify"]) == 1
        assert "t-99" in spec["files_to_modify"][0]


# ---------------------------------------------------------------------------
# implement_node
# ---------------------------------------------------------------------------
class TestImplementNode:
    """Tests for implement_node() — records implementation."""

    def test_basic_implementation(self):
        task = _make_task("T-1", "HIGH", "Fix bug")
        spec = {"files_to_modify": ["file1.py", "file2.py"]}
        state = _base_state(current_task=task, specification=spec)
        result = implement_node(state)
        assert result["current_phase"] == "implemented"
        impl = result["implementation"]
        assert impl["task_id"] == "T-1"
        assert impl["files_changed"] == ["file1.py", "file2.py"]
        assert "T-1" in impl["summary"]
        assert impl["dry_run"] is False

    def test_dry_run_flag(self):
        task = _make_task("T-1")
        spec = {"files_to_modify": []}
        state = _base_state(current_task=task, specification=spec, dry_run=True)
        result = implement_node(state)
        assert result["implementation"]["dry_run"] is True

    def test_missing_files_to_modify(self):
        task = _make_task("T-1")
        spec = {}
        state = _base_state(current_task=task, specification=spec)
        result = implement_node(state)
        assert result["implementation"]["files_changed"] == []


# ---------------------------------------------------------------------------
# validate_node
# ---------------------------------------------------------------------------
class TestValidateNode:
    """Tests for validate_node() — runs validation checks."""

    @patch("governance.workflows.orchestrator.spec_tiers.generate_specs_from_validation")
    def test_passes_no_gaps(self, mock_specs):
        mock_specs.return_value = [{"tier": 1}]
        task = _make_task("T-1")
        state = _base_state(current_task=task)
        result = validate_node(state)
        assert result["validation_passed"] is True
        assert result["gaps_discovered"] == []
        assert result["current_phase"] == "validated"
        assert result["validation_specs"] == [{"tier": 1}]

    @patch("governance.workflows.orchestrator.spec_tiers.generate_specs_from_validation")
    def test_simulated_gap_discovery(self, mock_specs):
        mock_specs.return_value = []
        task = _make_task("T-1")
        state = _base_state(current_task=task, _simulate_gap_discovery=True)
        result = validate_node(state)
        assert result["validation_passed"] is True
        assert len(result["gaps_discovered"]) == 1
        assert "T-1" in result["gaps_discovered"][0]["gap_id"]

    @patch("governance.workflows.orchestrator.spec_tiers.generate_specs_from_validation")
    def test_simulated_failure(self, mock_specs):
        mock_specs.return_value = []
        task = _make_task("T-1")
        state = _base_state(current_task=task, _simulate_validation_failure=True)
        result = validate_node(state)
        assert result["validation_passed"] is False

    @patch("governance.workflows.orchestrator.spec_tiers.generate_specs_from_validation")
    def test_calls_generate_specs(self, mock_specs):
        mock_specs.return_value = [{"tier": 1}, {"tier": 2}]
        task = _make_task("T-1")
        state = _base_state(current_task=task)
        validate_node(state)
        mock_specs.assert_called_once()
        call_args = mock_specs.call_args
        assert call_args[0][1] == task  # second arg is task


# ---------------------------------------------------------------------------
# inject_node
# ---------------------------------------------------------------------------
class TestInjectNode:
    """Tests for inject_node() — injects gaps into backlog."""

    def test_no_gaps(self):
        state = _base_state(gaps_discovered=[])
        result = inject_node(state)
        assert result["current_phase"] == "no_gaps_to_inject"
        assert "backlog" not in result

    def test_injects_gap(self):
        gap = {"gap_id": "GAP-1", "priority": "MEDIUM", "description": "New gap"}
        state = _base_state(backlog=[], gaps_discovered=[gap])
        result = inject_node(state)
        assert result["current_phase"] == "gaps_injected"
        assert len(result["backlog"]) == 1
        assert result["backlog"][0]["task_id"] == "GAP-1"

    def test_deduplicates_gaps(self):
        existing = _make_task("GAP-1", "MEDIUM", "Existing")
        gap = {"gap_id": "GAP-1", "priority": "HIGH", "description": "Duplicate"}
        state = _base_state(backlog=[existing], gaps_discovered=[gap])
        result = inject_node(state)
        assert len(result["backlog"]) == 1

    def test_sorts_by_priority(self):
        gap1 = {"gap_id": "GAP-LOW", "priority": "LOW", "description": "Low"}
        gap2 = {"gap_id": "GAP-CRIT", "priority": "CRITICAL", "description": "Critical"}
        state = _base_state(backlog=[], gaps_discovered=[gap1, gap2])
        result = inject_node(state)
        assert result["backlog"][0]["task_id"] == "GAP-CRIT"
        assert result["backlog"][1]["task_id"] == "GAP-LOW"

    def test_gap_with_task_id_key(self):
        """Gaps can use task_id instead of gap_id."""
        gap = {"task_id": "T-GAP-1", "priority": "HIGH", "description": "From task"}
        state = _base_state(backlog=[], gaps_discovered=[gap])
        result = inject_node(state)
        assert result["backlog"][0]["task_id"] == "T-GAP-1"

    def test_default_description(self):
        gap = {"gap_id": "GAP-X"}
        state = _base_state(backlog=[], gaps_discovered=[gap])
        result = inject_node(state)
        assert "GAP-X" in result["backlog"][0]["description"]


# ---------------------------------------------------------------------------
# complete_cycle_node
# ---------------------------------------------------------------------------
class TestCompleteCycleNode:
    """Tests for complete_cycle_node() — records cycle completion."""

    def test_basic_completion(self):
        task = _make_task("T-1")
        state = _base_state(current_task=task, cycles_completed=2)
        result = complete_cycle_node(state)
        assert result["cycles_completed"] == 3
        assert result["current_task"] is None
        assert result["specification"] is None
        assert result["implementation"] is None
        assert result["validation_results"] is None
        assert result["validation_passed"] is None
        assert result["gaps_discovered"] == []
        assert result["current_phase"] == "cycle_complete"

    def test_appends_to_history(self):
        task = _make_task("T-1")
        existing_history = [{"task_id": "T-0"}]
        state = _base_state(
            current_task=task,
            cycle_history=existing_history,
            specification={"spec": True},
            implementation={"impl": True},
            validation_results={"val": True},
        )
        result = complete_cycle_node(state)
        assert len(result["cycle_history"]) == 2
        latest = result["cycle_history"][1]
        assert latest["task_id"] == "T-1"
        assert latest["specification"] == {"spec": True}
        assert latest["implementation"] == {"impl": True}
        assert latest["validation"] == {"val": True}

    def test_budget_tracking(self):
        task = _make_task("T-1", "HIGH")
        state = _base_state(
            current_task=task,
            value_delivered=10,
            tokens_used=50,
        )
        result = complete_cycle_node(state)
        # HIGH = 3 value
        assert result["value_delivered"] == 13
        assert result["tokens_used"] == 60  # 50 + TOKEN_COST_PER_CYCLE(10)

    def test_no_budget_tracking_without_key(self):
        task = _make_task("T-1")
        state = _base_state(current_task=task)
        # No "value_delivered" key
        result = complete_cycle_node(state)
        assert "value_delivered" not in result

    def test_does_not_mutate_original_history(self):
        task = _make_task("T-1")
        original_history = [{"task_id": "T-0"}]
        state = _base_state(current_task=task, cycle_history=original_history)
        complete_cycle_node(state)
        assert len(original_history) == 1


# ---------------------------------------------------------------------------
# park_task_node
# ---------------------------------------------------------------------------
class TestParkTaskNode:
    """Tests for park_task_node() — parks exhausted tasks."""

    def test_parks_task(self):
        task = _make_task("T-1")
        state = _base_state(current_task=task, cycles_completed=5)
        result = park_task_node(state)
        assert result["current_phase"] == "task_parked"
        assert result["current_task"] is None
        assert result["cycles_completed"] == 6

    def test_appends_parked_to_history(self):
        task = _make_task("T-1")
        state = _base_state(current_task=task, cycle_history=[])
        result = park_task_node(state)
        assert len(result["cycle_history"]) == 1
        entry = result["cycle_history"][0]
        assert entry["task_id"] == "T-1"
        assert entry["status"] == "parked"
        assert entry["reason"] == "exhausted_retries"

    def test_preserves_existing_history(self):
        task = _make_task("T-2")
        existing = [{"task_id": "T-1", "status": "completed"}]
        state = _base_state(current_task=task, cycle_history=existing)
        result = park_task_node(state)
        assert len(result["cycle_history"]) == 2
        assert result["cycle_history"][0]["task_id"] == "T-1"
        assert result["cycle_history"][1]["task_id"] == "T-2"


# ---------------------------------------------------------------------------
# certify_node
# ---------------------------------------------------------------------------
class TestCertifyNode:
    """Tests for certify_node() — generates certification record."""

    def test_basic_certification(self):
        history = [
            {
                "task_id": "T-1",
                "implementation": {
                    "files_changed": ["file1.py"],
                    "summary": "Fixed T-1",
                },
            },
            {
                "task_id": "T-2",
                "implementation": {
                    "files_changed": ["file2.py", "file1.py"],
                    "summary": "Fixed T-2",
                },
            },
        ]
        state = _base_state(cycle_history=history, backlog=[_make_task("T-3")])
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 2
        assert cert["cycles_parked"] == 0
        assert cert["tasks_completed"] == ["T-1", "T-2"]
        assert cert["tasks_parked"] == []
        assert "file1.py" in cert["files_changed"]
        assert "file2.py" in cert["files_changed"]
        assert cert["remaining_backlog"] == 1
        assert "T-1" in cert["impact_summary"]
        assert "T-2" in cert["impact_summary"]

    def test_parked_tasks_separated(self):
        history = [
            {"task_id": "T-1", "implementation": {"summary": "Done"}},
            {"task_id": "T-2", "status": "parked", "reason": "exhausted_retries"},
        ]
        state = _base_state(cycle_history=history)
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 1
        assert cert["cycles_parked"] == 1
        assert "T-1" in cert["tasks_completed"]
        assert "T-2" in cert["tasks_parked"]

    def test_deduplicated_files(self):
        history = [
            {"task_id": "T-1", "implementation": {"files_changed": ["a.py", "b.py"]}},
            {"task_id": "T-2", "implementation": {"files_changed": ["b.py", "c.py"]}},
        ]
        state = _base_state(cycle_history=history)
        result = certify_node(state)
        assert result["certification"]["files_changed"] == ["a.py", "b.py", "c.py"]

    def test_empty_history(self):
        state = _base_state(cycle_history=[])
        result = certify_node(state)
        cert = result["certification"]
        assert cert["cycles_completed"] == 0
        assert cert["files_changed"] == []
        assert cert["impact_summary"] == ""

    def test_budget_metrics(self):
        history = [{"task_id": "T-1", "implementation": {"summary": "Done"}}]
        state = _base_state(
            cycle_history=history,
            value_delivered=15,
            tokens_used=40,
            token_budget=100,
        )
        result = certify_node(state)
        cert = result["certification"]
        assert cert["value_delivered"] == 15
        assert cert["tokens_used"] == 40
        assert cert["budget_utilization"] == 40.0

    def test_no_budget_metrics_without_key(self):
        history = [{"task_id": "T-1", "implementation": {"summary": "Done"}}]
        state = _base_state(cycle_history=history)
        result = certify_node(state)
        assert "value_delivered" not in result["certification"]

    def test_missing_implementation(self):
        """Tasks with None implementation handled gracefully."""
        history = [{"task_id": "T-1", "implementation": None}]
        state = _base_state(cycle_history=history)
        result = certify_node(state)
        cert = result["certification"]
        assert cert["files_changed"] == []
        assert "Completed T-1" in cert["impact_summary"]


# ---------------------------------------------------------------------------
# complete_node
# ---------------------------------------------------------------------------
class TestCompleteNode:
    """Tests for complete_node() — marks run complete."""

    def test_marks_complete(self):
        state = _base_state()
        result = complete_node(state)
        assert result["status"] == "success"
        assert result["current_phase"] == "complete"
