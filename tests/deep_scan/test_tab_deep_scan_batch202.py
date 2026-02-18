"""Batch 202 — Orchestrator graph + spec_tiers defense tests.

Validates fixes for:
- BUG-202-GRAPH-001: Missing continue after park_task in graph loop
- BUG-202-SPEC-001: generate_batch_specs bare subscript task["task_id"]
- BUG-202-ROBOT-001: export_to_robot bare subscript spec["task_id"]
"""
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-202-GRAPH-001: park_task continue ────────────────────────────

class TestGraphParkTaskContinue:
    """park_task branch must have continue to skip spec/impl/validate."""

    def test_park_task_branch_has_continue(self):
        """After park_task, loop must continue back to gate."""
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        # Find the park_task branch in _run_fallback_workflow
        in_func = False
        found_park = False
        found_continue_after_park = False
        for i, line in enumerate(src.splitlines()):
            if "def _run_fallback_workflow" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and 'route == "park_task"' in line:
                found_park = True
            elif found_park and "continue" in line.strip():
                found_continue_after_park = True
                break
            elif found_park and line.strip() and not line.strip().startswith("#"):
                # Hit a non-comment, non-continue line — check if it's the else
                if line.strip().startswith("else:") or line.strip().startswith("elif"):
                    break
        assert found_park, "park_task branch not found in _run_fallback_workflow"
        assert found_continue_after_park, "park_task branch must have continue statement"

    def test_park_task_then_gate_stops_on_empty_backlog(self):
        """After parking last task, orchestrator should stop cleanly."""
        from governance.workflows.orchestrator.graph import run_single_cycle
        result = run_single_cycle(
            "TEST-PARK-202", "test park continue",
            _simulate_validation_failure=True,
        )
        # Should complete (parked or safety cap) without infinite loop
        assert result.get("status") == "success" or result.get("safety_cap_reached")


# ── BUG-202-SPEC-001: generate_batch_specs safe access ───────────────

class TestGenerateBatchSpecsSafe:
    """generate_batch_specs must use .get() for task_id."""

    def test_generate_batch_specs_no_bare_subscript(self):
        """generate_batch_specs should not use task['task_id'] bare subscript."""
        src = (SRC / "governance/workflows/orchestrator/spec_tiers.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def generate_batch_specs" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and 'task["task_id"]' in line:
                assert False, f"Bare subscript task['task_id'] found: {line.strip()}"

    def test_generate_batch_specs_handles_missing_task_id(self):
        """generate_batch_specs should not crash on tasks without task_id."""
        from governance.workflows.orchestrator.spec_tiers import generate_batch_specs
        backlog = [{"description": "Test gap", "priority": "MEDIUM"}]
        result = generate_batch_specs(backlog)
        assert len(result) == 1
        assert result[0]["task_id"] == "unknown"


# ── BUG-202-ROBOT-001: export_to_robot safe access ──────────────────

class TestExportToRobotSafe:
    """export_to_robot must use .get() for task_id."""

    def test_export_to_robot_no_bare_subscript(self):
        """export_to_robot should not use spec['task_id'] bare subscript."""
        src = (SRC / "governance/workflows/orchestrator/spec_tiers.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def export_to_robot" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and 'spec["task_id"]' in line:
                assert False, f"Bare subscript spec['task_id'] found: {line.strip()}"

    def test_export_to_robot_handles_missing_task_id(self):
        """export_to_robot should not crash on spec without task_id."""
        from governance.workflows.orchestrator.spec_tiers import export_to_robot
        spec = {"endpoint": "/api/health", "method": "GET", "spec_type": "api",
                "tier_1": "Feature: test", "tier_2": "Scenario: test"}
        result = export_to_robot(spec)
        assert "unknown" in result


# ── Spec tiers functional tests ──────────────────────────────────────

class TestSpecTiersFunctional:
    """Functional tests for spec tier generation."""

    def test_generate_spec_returns_all_tiers(self):
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        result = generate_spec("TASK-1", "test", "/api/health")
        assert "tier_1" in result
        assert "tier_2" in result
        assert "tier_3" in result
        assert result["task_id"] == "TASK-1"

    def test_generate_spec_ui_type(self):
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        result = generate_spec("TASK-UI", "ui test", "/dashboard", spec_type="ui")
        assert result["mcp_tool"] == "playwright"

    def test_generate_specs_from_validation_default(self):
        from governance.workflows.orchestrator.spec_tiers import generate_specs_from_validation
        result = generate_specs_from_validation(
            {"tests_passed": True, "task_id": "T-1"},
            {"task_id": "T-1", "description": "test"},
        )
        assert len(result) >= 1
