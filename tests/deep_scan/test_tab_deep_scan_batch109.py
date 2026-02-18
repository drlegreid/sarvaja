"""Deep scan batch 109: Workflow DSP/SFDC + models/validators.

Batch 109 findings: 17 total, 0 confirmed fixes, 17 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Orchestrator graph ordering defense ──────────────


class TestOrchestratorGraphOrdering:
    """Verify orchestrator graph enforces correct phase ordering."""

    def test_spec_node_sets_specification(self):
        """spec_node always sets specification in state."""
        from governance.workflows.orchestrator.nodes import spec_node

        state = {"current_task": {"task_id": "T-001", "description": "Test"}}
        result = spec_node(state)
        assert "specification" in result
        assert result["specification"]["task_id"] == "T-001"

    def test_implement_node_uses_specification(self):
        """implement_node reads specification set by spec_node."""
        from governance.workflows.orchestrator.nodes import spec_node, implement_node

        state = {"current_task": {"task_id": "T-001", "description": "Test"}}
        spec_result = spec_node(state)
        state.update(spec_result)
        impl_result = implement_node(state)
        assert impl_result["current_phase"] == "implemented"
        assert impl_result["implementation"]["task_id"] == "T-001"

    def test_validate_node_generates_specs(self):
        """validate_node generates 3-tier specs per TEST-SPEC-01-v1."""
        from governance.workflows.orchestrator.nodes import validate_node

        state = {
            "current_task": {"task_id": "T-001", "description": "Test"},
        }
        result = validate_node(state)
        assert result["current_phase"] == "validated"
        assert "validation_specs" in result

    def test_complete_cycle_clears_state(self):
        """complete_cycle_node clears task state for next iteration."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        state = {
            "current_task": {"task_id": "T-001", "description": "Test", "priority": "HIGH"},
            "specification": {"task_id": "T-001"},
            "implementation": {"task_id": "T-001"},
            "validation_results": {"tests_passed": True},
            "cycles_completed": 0,
            "cycle_history": [],
        }
        result = complete_cycle_node(state)
        assert result["current_task"] is None
        assert result["specification"] is None
        assert result["implementation"] is None
        assert result["validation_results"] is None
        assert result["cycles_completed"] == 1

    def test_gate_decision_routing(self):
        """check_gate_decision routes based on gate_decision."""
        from governance.workflows.orchestrator.edges import check_gate_decision

        assert check_gate_decision({"gate_decision": "continue"}) == "backlog"
        assert check_gate_decision({"gate_decision": "stop"}) == "complete"
        assert check_gate_decision({}) == "complete"  # Default


# ── DSM tracker lifecycle defense ──────────────


class TestDSMTrackerLifecycle:
    """Verify DSM tracker handles lifecycle correctly."""

    def test_completed_cycles_capped_at_50(self):
        """completed_cycles list is capped at 50."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = list(range(50))  # Already at cap
        tracker.current_cycle = MagicMock()
        tracker.current_cycle.current_phase = DSPPhase.REPORT.value
        tracker.current_cycle.metrics = {}
        tracker.current_cycle.cycle_id = "test"
        tracker.current_cycle.started_at = datetime.now()
        tracker.current_cycle.phases_completed = []
        tracker.current_cycle.findings = []
        tracker.current_cycle.checkpoints = []
        tracker._state_file = None
        tracker.evidence_dir = "/tmp/test-evidence"

        with patch.object(tracker, "_save_state"):
            with patch("governance.dsm.tracker.generate_evidence"):
                tracker.complete_cycle()

        assert len(tracker.completed_cycles) <= 50


# ── Pydantic model defense ──────────────


class TestPydanticModelDefense:
    """Verify Pydantic models handle defaults correctly."""

    def test_pydantic_list_defaults_are_independent(self):
        """Pydantic v2 creates independent copies of list defaults."""
        from governance.models import AgentCreate

        a1 = AgentCreate(agent_id="agent-1", name="A1", agent_type="code")
        a2 = AgentCreate(agent_id="agent-2", name="A2", agent_type="code")

        a1.capabilities.append("code-review")

        # Pydantic v2 creates independent copies — a2 is unaffected
        assert "code-review" not in a2.capabilities

    def test_agent_response_list_independence(self):
        """AgentResponse list defaults are independent per instance."""
        from governance.models import AgentResponse

        r1 = AgentResponse(
            agent_id="a1", name="A1", agent_type="code",
            trust_score=0.8, status="ACTIVE",
        )
        r2 = AgentResponse(
            agent_id="a2", name="A2", agent_type="code",
            trust_score=0.9, status="ACTIVE",
        )

        r1.capabilities.append("test")
        assert "test" not in r2.capabilities

    def test_task_response_datetime_as_string(self):
        """TaskResponse accepts ISO string for datetime fields."""
        from governance.models import TaskResponse

        tr = TaskResponse(
            task_id="TASK-001",
            description="Test",
            phase="implementation",
            status="TODO",
            created_at="2026-02-15T10:00:00",
        )
        assert tr.created_at == "2026-02-15T10:00:00"

    def test_task_to_dict_converts_datetime_to_string(self):
        """_task_to_dict converts datetime to ISO string."""
        from governance.stores.typedb_access import _task_to_dict

        task = MagicMock()
        task.id = "TASK-001"
        task.name = "Test"
        task.description = "Desc"
        task.body = None
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = None
        task.agent_id = None
        task.created_at = datetime(2026, 2, 15, 10, 0, 0)
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        assert isinstance(result["created_at"], str)
        assert "2026-02-15" in result["created_at"]


# ── Orchestrator budget defense ──────────────


class TestOrchestratorBudgetTokenTracking:
    """Verify budget tracking across complete and park paths."""

    def test_complete_cycle_tracks_value(self):
        """complete_cycle_node increments value_delivered."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        state = {
            "current_task": {"task_id": "T-001", "description": "Test", "priority": "HIGH"},
            "cycles_completed": 0,
            "cycle_history": [],
            "value_delivered": 0,
            "tokens_used": 0,
        }
        result = complete_cycle_node(state)
        assert result["value_delivered"] > 0
        assert result["tokens_used"] > 0

    def test_park_task_tracks_tokens_when_present(self):
        """park_task_node tracks tokens only when tokens_used in state."""
        from governance.workflows.orchestrator.nodes import park_task_node

        state = {
            "current_task": {"task_id": "T-001", "description": "Test"},
            "cycles_completed": 0,
            "cycle_history": [],
            "tokens_used": 100,
        }
        result = park_task_node(state)
        assert result["tokens_used"] > 100

    def test_park_task_no_tokens_when_absent(self):
        """park_task_node does NOT add tokens_used when not in state."""
        from governance.workflows.orchestrator.nodes import park_task_node

        state = {
            "current_task": {"task_id": "T-001", "description": "Test"},
            "cycles_completed": 0,
            "cycle_history": [],
        }
        result = park_task_node(state)
        assert "tokens_used" not in result
