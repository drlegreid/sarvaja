"""Batch 200 — Orchestrator defense tests.

Validates fixes for:
- BUG-200-IMPL-001: implement_node guards against None specification
- Orchestrator node null-safety (pre-existing guards)
- Budget compute edge cases
"""
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-200-IMPL-001: implement_node spec guard ─────────────────────

class TestImplementNodeSpecGuard:
    """implement_node must guard against None specification."""

    def test_implement_node_uses_get_for_specification(self):
        """implement_node should use .get() or guard for specification."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        # Find implement_node function
        in_func = False
        found_bare_subscript = False
        found_guard = False
        for line in src.splitlines():
            if "def implement_node" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func:
                if 'state["specification"]' in line and ".get(" not in line:
                    found_bare_subscript = True
                if "impl_error" in line or "No specification" in line:
                    found_guard = True
        assert found_guard, "implement_node must guard against missing specification"

    def test_implement_node_returns_error_on_none_spec(self):
        """implement_node should return error phase when specification is None."""
        from governance.workflows.orchestrator.nodes import implement_node
        state = {
            "current_task": {"task_id": "TEST-1", "description": "test"},
            "specification": None,
            "dry_run": False,
        }
        result = implement_node(state)
        assert result["current_phase"] == "impl_error"

    def test_implement_node_returns_error_on_missing_spec(self):
        """implement_node should handle missing specification key."""
        from governance.workflows.orchestrator.nodes import implement_node
        state = {
            "current_task": {"task_id": "TEST-1", "description": "test"},
            "dry_run": False,
        }
        result = implement_node(state)
        assert result["current_phase"] == "impl_error"


# ── Orchestrator node guards ─────────────────────────────────────────

class TestOrchestratorNodeGuards:
    """All orchestrator nodes must guard against None current_task."""

    def test_spec_node_guards_none_task(self):
        from governance.workflows.orchestrator.nodes import spec_node
        result = spec_node({"current_task": None})
        assert "error" in result["current_phase"]

    def test_validate_node_guards_none_task(self):
        from governance.workflows.orchestrator.nodes import validate_node
        result = validate_node({"current_task": None})
        assert "error" in result["current_phase"]

    def test_complete_cycle_guards_none_task(self):
        from governance.workflows.orchestrator.nodes import complete_cycle_node
        result = complete_cycle_node({"current_task": None, "cycles_completed": 0})
        assert "error" in result["current_phase"]

    def test_park_task_guards_none_task(self):
        from governance.workflows.orchestrator.nodes import park_task_node
        result = park_task_node({"current_task": None, "cycles_completed": 0})
        assert "error" in result["current_phase"]


# ── Budget compute edge cases ────────────────────────────────────────

class TestBudgetComputeEdgeCases:
    """Budget computation must handle edge cases."""

    def test_compute_budget_empty_backlog(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {"backlog": [], "cycles_completed": 0, "max_cycles": 10,
                 "token_budget": 100, "tokens_used": 0, "value_delivered": 0}
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "backlog_empty"

    def test_compute_budget_max_cycles(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {"backlog": [{"priority": "HIGH"}], "cycles_completed": 10,
                 "max_cycles": 10, "token_budget": 100, "tokens_used": 0,
                 "value_delivered": 0}
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "max_cycles_reached"

    def test_compute_budget_token_exhaustion(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {"backlog": [{"priority": "HIGH"}], "cycles_completed": 1,
                 "max_cycles": 10, "token_budget": 100, "tokens_used": 85,
                 "value_delivered": 5}
        result = compute_budget(state)
        assert result["should_continue"] is False
        assert result["reason"] == "token_budget_exhausted"

    def test_compute_budget_available(self):
        from governance.workflows.orchestrator.budget import compute_budget
        state = {"backlog": [{"priority": "HIGH"}], "cycles_completed": 1,
                 "max_cycles": 10, "token_budget": 100, "tokens_used": 10,
                 "value_delivered": 3}
        result = compute_budget(state)
        assert result["should_continue"] is True
        assert result["reason"] == "budget_available"
