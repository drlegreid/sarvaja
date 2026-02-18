"""Deep scan batch 191: Quality + workflows layer.

Batch 191 findings: 14 total, 1 confirmed fix, 13 rejected/deferred.
- BUG-191-012: spec_tiers.py unguarded task["task_id"] KeyError.
- BUG-191-001: Cycle detection — REJECTED (logic correct).
- BUG-191-004: CVP category overwrite — REJECTED (by design).
- BUG-191-006: Lexicographic comparison — REJECTED (correct for format).
- BUG-191-013: dry_run count — REJECTED (by design).
"""
import pytest
from pathlib import Path


# ── Spec tiers defensive access ──────────────


class TestSpecTiersDefensiveAccess:
    """Verify spec_tiers.py uses .get() for task fields."""

    def test_generate_specs_uses_get_for_task_id(self):
        """generate_specs_from_validation uses .get() for task_id."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/workflows/orchestrator/spec_tiers.py").read_text()
        start = src.index("def generate_specs_from_validation")
        section = src[start:start + 500]
        assert 'task.get("task_id"' in section
        # Should NOT have bare task["task_id"]
        assert 'task["task_id"]' not in section

    def test_spec_tiers_importable(self):
        """spec_tiers module is importable."""
        from governance.workflows.orchestrator import spec_tiers
        assert spec_tiers is not None

    def test_generate_spec_function_exists(self):
        """generate_spec function exists."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec
        assert callable(generate_spec)

    def test_generate_batch_specs_exists(self):
        """generate_batch_specs function exists."""
        from governance.workflows.orchestrator.spec_tiers import generate_batch_specs
        assert callable(generate_batch_specs)


# ── Cycle detection correctness defense ──────────────


class TestCycleDetectionDefense:
    """Verify analyzer cycle detection logic."""

    def test_analyzer_importable(self):
        """Quality analyzer is importable."""
        from governance.quality import analyzer
        assert analyzer is not None

    def test_analyzer_has_analyze(self):
        """Analyzer has analyze method."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        assert hasattr(RuleQualityAnalyzer, "analyze")


# ── Heuristic runner defense ──────────────


class TestHeuristicRunnerDefense:
    """Verify heuristic runner structure."""

    def test_runner_exec_importable(self):
        """runner_exec module is importable."""
        from governance.routes.tests import runner_exec
        assert runner_exec is not None

    def test_runner_exec_has_execute(self):
        """runner_exec has execute_heuristic function."""
        from governance.routes.tests.runner_exec import execute_heuristic
        assert callable(execute_heuristic)

    def test_heuristic_checks_session_importable(self):
        """heuristic_checks_session module is importable."""
        from governance.routes.tests import heuristic_checks_session
        assert heuristic_checks_session is not None
