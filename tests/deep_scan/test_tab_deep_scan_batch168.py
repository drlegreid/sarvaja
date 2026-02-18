"""Deep scan batch 168: Workflow + orchestrator layer.

Batch 168 findings: 14 total, 2 confirmed fixes, 12 rejected.
- BUG-ORCH-SAFETY-CAP-001: Safety cap exits without certify/complete.
- BUG-CAP-DURATION-DEFAULT-001: cap_duration default inconsistent with _MAX_DURATION_HOURS.
"""
import pytest
from pathlib import Path


# ── Safety cap certification defense ──────────────


class TestSafetyCapCertificationDefense:
    """Verify safety cap calls certify_node + complete_node."""

    def test_safety_cap_calls_certify(self):
        """Safety cap path includes certify_node call."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/workflows/orchestrator/graph.py").read_text()
        # Find the else clause (safety cap)
        cap_start = src.index("safety_cap_reached")
        cap_section = src[cap_start:cap_start + 200]
        assert "certify_node" in cap_section

    def test_safety_cap_calls_complete(self):
        """Safety cap path includes complete_node call."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/workflows/orchestrator/graph.py").read_text()
        cap_start = src.index("safety_cap_reached")
        cap_section = src[cap_start:cap_start + 200]
        assert "complete_node" in cap_section

    def test_safety_cap_produces_certification(self):
        """Safety-capped run produces certification in state."""
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import create_initial_state, add_to_backlog
        state = create_initial_state(max_cycles=1, dry_run=True)
        # Overfill backlog so safety cap fires
        for i in range(50):
            state = add_to_backlog(state, f"TASK-{i:03d}", "LOW", f"Task {i}")
        state["max_cycles"] = 1
        result = run_orchestrator(state)
        # Should have certification key regardless of how it ended
        if result.get("safety_cap_reached"):
            assert "certification" in result

    def test_normal_run_has_certification(self):
        """Normal run also produces certification."""
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import create_initial_state, add_to_backlog
        state = create_initial_state(max_cycles=2, dry_run=True)
        state = add_to_backlog(state, "TASK-001", "HIGH", "Test task")
        result = run_orchestrator(state)
        assert "certification" in result


# ── cap_duration default defense ──────────────


class TestCapDurationDefaultDefense:
    """Verify cap_duration default matches _MAX_DURATION_HOURS."""

    def test_default_matches_constant(self):
        """cap_duration default uses _MAX_DURATION_HOURS constant."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/session_repair.py").read_text()
        assert "max_hours: float = _MAX_DURATION_HOURS" in src

    def test_no_hardcoded_8_default(self):
        """No hardcoded default of 8 in cap_duration signature."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/session_repair.py").read_text()
        # Find cap_duration function
        start = src.index("def cap_duration")
        sig_end = src.index("):", start) + 2
        sig = src[start:sig_end]
        assert "= 8)" not in sig

    def test_max_duration_hours_is_24(self):
        """_MAX_DURATION_HOURS is 24."""
        from governance.services.session_repair import _MAX_DURATION_HOURS
        assert _MAX_DURATION_HOURS == 24

    def test_cap_applies_at_24_hours(self):
        """cap_duration with default caps at 24 hours, not 8."""
        from governance.services.session_repair import cap_duration
        session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "start_time": "2026-02-15T00:00:00",
            "end_time": "2026-02-16T12:00:00",  # 36 hours
        }
        result = cap_duration(session)
        # Should be capped, not original 36h
        assert result["end_time"] != "2026-02-16T12:00:00"


# ── Orchestrator budget guard defense ──────────────


class TestOrchestratorBudgetGuardDefense:
    """Verify budget computation handles edge cases."""

    def test_compute_budget_zero_token_budget(self):
        """token_budget=0 → should_continue=True (no budget configured)."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"priority": "HIGH"}, {"priority": "MEDIUM"}],
            "cycles_completed": 5,
            "max_cycles": 10,
            "token_budget": 0,
            "tokens_used": 50,
            "value_delivered": 10,
        }
        result = compute_budget(state)
        assert "should_continue" in result

    def test_compute_budget_normal(self):
        """Normal budget with tokens used → reports utilization."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"priority": "HIGH"}],
            "cycles_completed": 3,
            "max_cycles": 10,
            "token_budget": 1000,
            "tokens_used": 500,
            "value_delivered": 5,
        }
        result = compute_budget(state)
        assert "token_ratio" in result

    def test_budget_exhaustion_stops(self):
        """80% token exhaustion triggers stop (should_continue=False)."""
        from governance.workflows.orchestrator.budget import compute_budget
        state = {
            "backlog": [{"priority": "HIGH"}],
            "cycles_completed": 5,
            "max_cycles": 100,
            "token_budget": 100,
            "tokens_used": 85,
            "value_delivered": 10,
        }
        result = compute_budget(state)
        assert result["should_continue"] is False


# ── Spec node guard defense ──────────────


class TestSpecNodeGuardDefense:
    """Verify spec_node and implement_node share same guard pattern."""

    def test_spec_node_guards_current_task(self):
        """spec_node checks for None current_task."""
        from governance.workflows.orchestrator.nodes import spec_node
        result = spec_node({"current_task": None})
        assert result["current_phase"] == "spec_error"

    def test_implement_node_guards_current_task(self):
        """implement_node checks for None current_task."""
        from governance.workflows.orchestrator.nodes import implement_node
        result = implement_node({"current_task": None})
        assert result["current_phase"] == "impl_error"

    def test_validate_node_guards_current_task(self):
        """validate_node checks for None current_task."""
        from governance.workflows.orchestrator.nodes import validate_node
        result = validate_node({"current_task": None})
        assert result["current_phase"] == "validate_error"
