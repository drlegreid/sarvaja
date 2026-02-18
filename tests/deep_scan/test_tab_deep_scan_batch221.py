"""Batch 221 — DSM + heuristics defense tests.

Validates fixes for:
- BUG-221-VALIDATE-001: DSM validate_node must require tests_run > 0
- BUG-221-EVIDENCE-001: report_node must pass evidence_dir to generate_evidence
- BUG-221-TAUTOLOGY-001: H-EXPLR-002 tautological count check
- BUG-221-EVICT-001: runner_store eviction must sort by timestamp
"""
from pathlib import Path
import re

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-221-VALIDATE-001: validate_node zero tests = fail ────────────

class TestDSMValidateZeroTests:
    """validate_node must NOT pass when zero tests run."""

    def test_zero_tests_not_passed_in_source(self):
        """Source must check tests_run > 0."""
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        assert "tests_run" in src and "> 0" in src

    def test_validate_node_dry_run_has_failures(self):
        """Dry-run mode has tests_failed=1, so passed should be False."""
        from governance.dsm.langgraph.nodes_execution import validate_node
        state = {
            "cycle_id": "TEST-001",
            "dry_run": True,
            "phases_completed": [],
            "checkpoints": [],
            "phase_results": [],
        }
        result = validate_node(state)
        assert result["validation_passed"] is False

    def test_validate_node_production_zero_tests_fails(self):
        """Production mode with 0 tests run must NOT pass."""
        from governance.dsm.langgraph.nodes_execution import validate_node
        state = {
            "cycle_id": "TEST-002",
            "dry_run": False,
            "phases_completed": [],
            "checkpoints": [],
            "phase_results": [],
        }
        result = validate_node(state)
        assert result["validation_passed"] is False


# ── BUG-221-EVIDENCE-001: generate_evidence needs evidence_dir ───────

class TestDSMEvidenceArgs:
    """report_node must pass evidence_dir to generate_evidence."""

    def test_evidence_dir_in_source(self):
        """Source must pass evidence_dir argument."""
        src = (SRC / "governance/dsm/langgraph/nodes_execution.py").read_text()
        # Should have generate_evidence(cycle, ...) with two args
        assert "generate_evidence(cycle," in src


# ── BUG-221-TAUTOLOGY-001: H-EXPLR-002 fix ──────────────────────────

class TestHeuristicTautologyFix:
    """H-EXPLR-002 must compare header total vs actual, not self."""

    def test_no_tautological_check_in_source(self):
        """Source must NOT have count = actual followed by count != actual."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        # Old pattern: count = actual; if count != actual:
        assert "count = actual" not in src

    def test_uses_data_total_field(self):
        """Source must extract total from data dict."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        assert 'data.get("total"' in src


# ── BUG-221-EVICT-001: timestamp-based eviction ─────────────────────

class TestRunnerStoreEviction:
    """Test result eviction must use timestamp ordering."""

    def test_eviction_uses_timestamp(self):
        """Source must sort by timestamp, not alphabetically."""
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        assert "timestamp" in src and "sorted" in src

    def test_cap_function_callable(self):
        from governance.routes.tests.runner_store import _cap_test_results
        assert callable(_cap_test_results)


# ── DSM nodes defense ────────────────────────────────────────────────

class TestDSMNodesDefense:
    """Defense tests for DSM LangGraph nodes."""

    def test_optimize_node_callable(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node
        assert callable(optimize_node)

    def test_validate_node_callable(self):
        from governance.dsm.langgraph.nodes_execution import validate_node
        assert callable(validate_node)

    def test_dream_node_callable(self):
        from governance.dsm.langgraph.nodes_execution import dream_node
        assert callable(dream_node)

    def test_report_node_callable(self):
        from governance.dsm.langgraph.nodes_execution import report_node
        assert callable(report_node)

    def test_optimize_dry_run(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node
        state = {
            "cycle_id": "TEST-001",
            "dry_run": True,
            "phases_completed": [],
            "checkpoints": [],
            "phase_results": [],
        }
        result = optimize_node(state)
        assert result["current_phase"] == "optimized"
        assert len(result["optimizations_applied"]) == 2

    def test_dream_node_generates_insights(self):
        from governance.dsm.langgraph.nodes_execution import dream_node
        state = {
            "cycle_id": "TEST-001",
            "dry_run": True,
            "phases_completed": [],
            "checkpoints": [],
            "phase_results": [],
            "audit_gaps": [],
            "optimizations_applied": [],
            "validation_passed": True,
        }
        result = dream_node(state)
        assert result["current_phase"] == "dreamed"
        assert len(result["dream_insights"]) > 0


# ── DSM tracker defense ──────────────────────────────────────────────

class TestDSMTrackerDefense:
    """Defense tests for DSM tracker module."""

    def test_tracker_importable(self):
        from governance.dsm.tracker import DSMTracker
        assert DSMTracker is not None

    def test_tracker_create_cycle(self):
        from governance.dsm.tracker import DSMTracker
        tracker = DSMTracker()
        # Abort any stale cycle from shared state
        if tracker.current_cycle:
            tracker.abort_cycle("test cleanup")
        cycle = tracker.start_cycle()
        assert cycle is not None
        assert hasattr(cycle, "cycle_id")
        assert cycle.cycle_id.startswith("DSM-")
        tracker.abort_cycle("test cleanup")


# ── DSM validation defense ───────────────────────────────────────────

class TestDSMValidationDefense:
    """Defense tests for DSM validation module."""

    def test_validation_importable(self):
        import governance.dsm.validation
        assert governance.dsm.validation is not None


# ── Heuristic checks defense ────────────────────────────────────────

class TestHeuristicChecksDefense:
    """Defense tests for heuristic check modules."""

    def test_exploratory_registry_exists(self):
        from governance.routes.tests.heuristic_checks_exploratory import EXPLORATORY_CHECKS
        assert len(EXPLORATORY_CHECKS) >= 5

    def test_check_functions_callable(self):
        from governance.routes.tests.heuristic_checks_exploratory import EXPLORATORY_CHECKS
        for check in EXPLORATORY_CHECKS:
            assert callable(check["check_fn"]), f"{check['id']} check_fn not callable"

    def test_runner_store_importable(self):
        import governance.routes.tests.runner_store
        assert governance.routes.tests.runner_store is not None

    def test_persist_result_callable(self):
        from governance.routes.tests.runner_store import _persist_result
        assert callable(_persist_result)

    def test_load_persisted_callable(self):
        from governance.routes.tests.runner_store import _load_persisted_results
        assert callable(_load_persisted_results)


# ── DSM evidence defense ─────────────────────────────────────────────

class TestDSMEvidenceDefense:
    """Defense tests for DSM evidence module."""

    def test_generate_evidence_callable(self):
        from governance.dsm.evidence import generate_evidence
        assert callable(generate_evidence)

    def test_generate_evidence_signature(self):
        """generate_evidence must require both cycle and evidence_dir."""
        import inspect
        from governance.dsm.evidence import generate_evidence
        sig = inspect.signature(generate_evidence)
        params = list(sig.parameters.keys())
        assert "cycle" in params
        assert "evidence_dir" in params


# ── DSM edges defense ────────────────────────────────────────────────

class TestDSMEdgesDefense:
    """Defense tests for DSM LangGraph edge functions."""

    def test_edges_module_importable(self):
        import governance.dsm.langgraph.edges
        assert governance.dsm.langgraph.edges is not None

    def test_check_validation_result_callable(self):
        from governance.dsm.langgraph.edges import check_validation_result
        assert callable(check_validation_result)
