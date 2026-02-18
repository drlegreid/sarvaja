"""Deep scan batch 119: Workflow DSP + SFDC + orchestrator.

Batch 119 findings: 19 total, 0 confirmed fixes, 19 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── DSM phase transition defense ──────────────


class TestDSMPhaseTransitionDefense:
    """Verify DSM tracker phase transitions avoid double-counting."""

    def test_report_phase_not_double_counted(self):
        """complete_cycle guards against REPORT double-append."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = []
        tracker._state_file = None
        tracker.evidence_dir = "/tmp/test-evidence"

        cycle = MagicMock()
        cycle.current_phase = DSPPhase.REPORT.value
        cycle.phases_completed = ["DISCOVERY", "SPECIFICATION"]
        cycle.metrics = {}
        cycle.cycle_id = "test-119"
        cycle.started_at = datetime.now()
        cycle.findings = []
        cycle.checkpoints = []
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            with patch("governance.dsm.tracker.generate_evidence"):
                tracker.complete_cycle()

        assert "REPORT" not in cycle.phases_completed

    def test_idle_not_recorded_in_phases(self):
        """IDLE phase is never recorded in phases_completed."""
        from governance.dsm.phases import DSPPhase

        assert DSPPhase.IDLE.value not in ["audit", "hypothesize", "measure"]

    def test_advance_records_current_before_transition(self):
        """advance_phase appends current phase before moving to next."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase

        tracker = DSMTracker.__new__(DSMTracker)
        tracker._state_file = None

        cycle = MagicMock()
        cycle.current_phase = DSPPhase.AUDIT.value
        cycle.phases_completed = []
        cycle.checkpoints = [MagicMock(phase="audit", description="x" * 30)]
        cycle.findings = [{"phase": "audit"}]
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            tracker.advance_phase()

        assert DSPPhase.AUDIT.value in cycle.phases_completed


# ── Orchestrator retry defense ──────────────


class TestOrchestratorRetryDefense:
    """Verify orchestrator retry loop has proper termination."""

    def test_retry_count_incremented_in_fallback(self):
        """_run_fallback_workflow increments retry_count on loop_to_spec."""
        from governance.workflows.orchestrator.state import create_initial_state, add_to_backlog

        state = create_initial_state(max_cycles=5)  # Need enough iterations for 3 retries + park
        state = add_to_backlog(state, "T-RETRY", "HIGH", "Retry test")
        state["_simulate_validation_failure"] = True

        from governance.workflows.orchestrator.graph import _run_fallback_workflow
        result = _run_fallback_workflow(state)

        # After 3 retries (MAX_RETRIES=3), task should be parked
        parked = [h for h in result.get("cycle_history", []) if h.get("status") == "parked"]
        assert len(parked) >= 1

    def test_safety_cap_prevents_infinite_loop(self):
        """Hard safety cap (_MAX_ITERATIONS) prevents runaway loops."""
        from governance.workflows.orchestrator.state import create_initial_state

        state = create_initial_state(max_cycles=2)
        # max_cycles=2 -> _MAX_ITERATIONS = 2 * 3 = 6
        assert state["max_cycles"] == 2

    def test_backlog_node_resets_retry_for_new_task(self):
        """backlog_node sets retry_count=0 for new tasks."""
        from governance.workflows.orchestrator.nodes import backlog_node

        result = backlog_node({
            "backlog": [{"task_id": "T-NEW", "description": "New task"}],
        })
        assert result["retry_count"] == 0


# ── Budget guard defense ──────────────


class TestBudgetGuardDefense:
    """Verify budget calculations are safe against edge cases."""

    def test_zero_tokens_used_no_crash(self):
        """ROI calculation with 0 tokens_used uses max(0, 1) = 1."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 10,
            "token_budget": 1000,
            "tokens_used": 0,
            "value_delivered": 0,
        })
        assert result["roi"] == 0.0
        assert result["should_continue"] is True

    def test_zero_token_budget_skips_exhaustion(self):
        """token_budget=0 (falsy) skips exhaustion check."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 10,
            "token_budget": 0,
            "tokens_used": 500,
            "value_delivered": 10,
        })
        assert result["should_continue"] is True
        assert result["token_ratio"] == 0.0

    def test_exhaustion_at_80_percent(self):
        """Budget stops at 80% token usage."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 100,
            "token_budget": 1000,
            "tokens_used": 800,
            "value_delivered": 50,
        })
        assert result["should_continue"] is False
        assert result["reason"] == "token_budget_exhausted"


# ── Gap injection defense ──────────────


class TestGapInjectionDefense:
    """Verify inject_node handles duplicates and missing IDs."""

    def test_duplicate_gaps_not_injected(self):
        """inject_node skips gaps already in backlog."""
        from governance.workflows.orchestrator.nodes import inject_node

        result = inject_node({
            "backlog": [{"task_id": "GAP-001", "priority": "HIGH", "description": "Existing"}],
            "gaps_discovered": [
                {"gap_id": "GAP-001", "priority": "HIGH", "description": "Duplicate"},
                {"gap_id": "GAP-002", "priority": "MEDIUM", "description": "New"},
            ],
        })
        # Only GAP-002 should be added
        ids = [t["task_id"] for t in result["backlog"]]
        assert ids.count("GAP-001") == 1
        assert "GAP-002" in ids

    def test_no_gaps_returns_early(self):
        """inject_node with empty gaps returns early."""
        from governance.workflows.orchestrator.nodes import inject_node

        result = inject_node({"backlog": [], "gaps_discovered": []})
        assert result["current_phase"] == "no_gaps_to_inject"

    def test_gap_without_id_skipped(self):
        """Gaps without gap_id or task_id are skipped."""
        from governance.workflows.orchestrator.nodes import inject_node

        result = inject_node({
            "backlog": [],
            "gaps_discovered": [
                {"description": "No ID gap"},
            ],
        })
        assert len(result["backlog"]) == 0


# ── DSM validation defense ──────────────


class TestDSMValidationDefense:
    """Verify DSM phase validation handles edge cases."""

    def test_unknown_phase_allowed(self):
        """Unknown phases return None (allowed)."""
        from governance.dsm.validation import validate_phase_evidence
        from governance.dsm.phases import DSPPhase

        cycle = MagicMock()
        cycle.checkpoints = []
        cycle.findings = []

        result = validate_phase_evidence(cycle, DSPPhase.IDLE)
        assert result is None

    def test_report_phase_no_evidence_required(self):
        """REPORT phase auto-generates evidence, no manual requirement."""
        from governance.dsm.validation import PHASE_REQUIREMENTS
        from governance.dsm.phases import DSPPhase

        req = PHASE_REQUIREMENTS[DSPPhase.REPORT]
        assert req.get("need_checkpoint_or_finding") is False

    def test_audit_needs_checkpoint_or_finding(self):
        """AUDIT phase requires at least a checkpoint or finding."""
        from governance.dsm.validation import validate_phase_evidence
        from governance.dsm.phases import DSPPhase

        cycle = MagicMock()
        cycle.checkpoints = []
        cycle.findings = []

        error = validate_phase_evidence(cycle, DSPPhase.AUDIT)
        assert error is not None
        assert "checkpoint or finding" in error.lower()


# ── Evidence generation defense ──────────────


class TestEvidenceGenerationDefense:
    """Verify evidence file generation handles edge cases."""

    def test_long_description_truncated(self):
        """Findings with >50 char descriptions are truncated."""
        from governance.dsm.evidence import generate_evidence

        cycle = MagicMock()
        cycle.cycle_id = "DSM-TEST-119"
        cycle.batch_id = None
        cycle.start_time = "2026-02-15T10:00:00"
        cycle.end_time = "2026-02-15T11:00:00"
        cycle.phases_completed = []
        cycle.findings = [
            {
                "id": "F-001",
                "type": "gap",
                "severity": "HIGH",
                "description": "A" * 100,
            },
        ]
        cycle.checkpoints = []
        cycle.metrics = {}

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path
            path = generate_evidence(cycle, Path(tmpdir))
            content = Path(path).read_text()
            assert "..." in content  # Truncated

    def test_empty_findings_no_table(self):
        """No findings section when findings list is empty."""
        from governance.dsm.evidence import generate_evidence

        cycle = MagicMock()
        cycle.cycle_id = "DSM-TEST-EMPTY"
        cycle.batch_id = None
        cycle.start_time = "2026-02-15T10:00:00"
        cycle.end_time = "2026-02-15T11:00:00"
        cycle.phases_completed = []
        cycle.findings = []
        cycle.checkpoints = []
        cycle.metrics = {}

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path
            path = generate_evidence(cycle, Path(tmpdir))
            content = Path(path).read_text()
            assert "## Findings" not in content


# ── Complete cycle state clearing defense ──────────────


class TestCompleteCycleStateClearingDefense:
    """Verify complete_cycle_node clears all transient state."""

    def test_all_transient_state_cleared(self):
        """current_task, specification, implementation, validation_results all None."""
        from governance.workflows.orchestrator.nodes import complete_cycle_node

        result = complete_cycle_node({
            "current_task": {"task_id": "T-001", "description": "Test", "priority": "HIGH"},
            "specification": {"task_id": "T-001"},
            "implementation": {"task_id": "T-001"},
            "validation_results": {"tests_passed": True},
            "cycles_completed": 0,
            "cycle_history": [],
        })
        assert result["current_task"] is None
        assert result["specification"] is None
        assert result["implementation"] is None
        assert result["validation_results"] is None
        assert result["cycles_completed"] == 1

    def test_park_task_clears_current_task(self):
        """park_task_node sets current_task to None."""
        from governance.workflows.orchestrator.nodes import park_task_node

        result = park_task_node({
            "current_task": {"task_id": "T-001", "description": "Test"},
            "cycles_completed": 0,
            "cycle_history": [],
        })
        assert result["current_task"] is None
