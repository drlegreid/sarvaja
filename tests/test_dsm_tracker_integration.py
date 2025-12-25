"""
Integration Tests for DSMTracker - MCP Tools and State Persistence

Tests:
- State persistence (save/load)
- Evidence file generation
- MCP tool integration
- Full cycle workflow

Per: RULE-004 (Exploratory Testing), RULE-012 (DSP)
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock


class TestStatePersistence:
    """Tests for state persistence."""

    def test_state_saved_on_start_cycle(self):
        """State file created on start_cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            tracker.start_cycle("TEST")

            assert state_file.exists()

            with open(state_file) as f:
                state = json.load(f)

            assert state["current_cycle"]["batch_id"] == "TEST"

    def test_state_saved_on_advance_phase(self):
        """State updated on advance_phase."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            tracker.start_cycle()
            tracker.advance_phase()

            with open(state_file) as f:
                state = json.load(f)

            assert state["current_cycle"]["current_phase"] == "audit"

    def test_state_saved_on_checkpoint(self):
        """State updated on checkpoint."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.checkpoint("Test checkpoint")

            with open(state_file) as f:
                state = json.load(f)

            assert len(state["current_cycle"]["checkpoints"]) == 1

    def test_state_loaded_on_init(self):
        """State loaded from file on init."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"

            # Create first tracker and start cycle
            tracker1 = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )
            tracker1.start_cycle("PERSIST-TEST")
            tracker1.advance_phase()
            cycle_id = tracker1.current_cycle.cycle_id

            # Create second tracker - should load state
            tracker2 = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            assert tracker2.current_cycle is not None
            assert tracker2.current_cycle.cycle_id == cycle_id
            assert tracker2.current_cycle.batch_id == "PERSIST-TEST"

    def test_state_cleared_on_complete(self):
        """State cleared on complete_cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.complete_cycle()

            with open(state_file) as f:
                state = json.load(f)

            assert state["current_cycle"] is None


class TestEvidenceGeneration:
    """Tests for evidence file generation."""

    def test_evidence_file_created(self):
        """Evidence markdown file created on complete."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle("EVIDENCE-TEST")
            tracker.advance_phase()
            evidence_path = tracker.complete_cycle()

            assert Path(evidence_path).exists()

    def test_evidence_contains_summary(self):
        """Evidence file contains summary section."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle("SUMMARY-TEST")
            tracker.advance_phase()
            evidence_path = tracker.complete_cycle()

            with open(evidence_path, encoding="utf-8") as f:
                content = f.read()

            assert "## Summary" in content
            assert "SUMMARY-TEST" in content

    def test_evidence_contains_findings(self):
        """Evidence file contains findings."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.add_finding("gap", "Missing coverage for X")
            evidence_path = tracker.complete_cycle()

            with open(evidence_path, encoding="utf-8") as f:
                content = f.read()

            assert "## Findings" in content
            assert "Missing coverage" in content

    def test_evidence_contains_checkpoints(self):
        """Evidence file contains checkpoints."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.checkpoint("Audited 5 modules")
            evidence_path = tracker.complete_cycle()

            with open(evidence_path, encoding="utf-8") as f:
                content = f.read()

            assert "## Checkpoints" in content
            assert "Audited 5 modules" in content

    def test_evidence_contains_metrics(self):
        """Evidence file contains metrics."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.update_metrics({"tests_passed": 150, "coverage": 85})
            evidence_path = tracker.complete_cycle()

            with open(evidence_path, encoding="utf-8") as f:
                content = f.read()

            assert "## Metrics" in content
            assert "tests_passed" in content
            assert "150" in content


class TestFullCycleWorkflow:
    """Tests for complete cycle workflow."""

    def test_full_cycle_workflow(self):
        """Full DSP cycle from start to complete."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            # Start
            tracker.start_cycle("FULL-CYCLE-TEST")
            assert tracker.get_current_phase() == DSPPhase.IDLE

            # AUDIT
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.AUDIT
            tracker.add_finding("gap", "Missing tests")
            tracker.checkpoint("Audit complete")

            # HYPOTHESIZE
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.HYPOTHESIZE
            tracker.checkpoint("Hypothesis formed")

            # MEASURE
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.MEASURE
            tracker.update_metrics({"baseline_coverage": 75})

            # OPTIMIZE
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.OPTIMIZE
            tracker.checkpoint("Optimizations applied")

            # VALIDATE
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.VALIDATE
            tracker.update_metrics({"new_coverage": 85})

            # DREAM
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.DREAM
            tracker.add_finding("improvement", "Consider new pattern")

            # REPORT
            tracker.advance_phase()
            assert tracker.get_current_phase() == DSPPhase.REPORT

            # COMPLETE
            evidence_path = tracker.complete_cycle()

            # Verify
            assert Path(evidence_path).exists()
            assert len(tracker.completed_cycles) == 1
            assert tracker.current_cycle is None

    def test_resume_interrupted_cycle(self):
        """Resume cycle after interruption."""
        from governance.dsm_tracker import DSMTracker, DSPPhase

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".dsm_state.json"

            # Start cycle and advance
            tracker1 = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )
            tracker1.start_cycle("RESUME-TEST")
            tracker1.advance_phase()  # AUDIT
            tracker1.advance_phase()  # HYPOTHESIZE
            tracker1.checkpoint("Before interruption")

            # Simulate interruption - create new tracker
            tracker2 = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(state_file)
            )

            # Should resume at HYPOTHESIZE
            assert tracker2.current_cycle is not None
            assert tracker2.get_current_phase() == DSPPhase.HYPOTHESIZE
            assert len(tracker2.current_cycle.checkpoints) == 1

            # Can continue
            tracker2.advance_phase()  # MEASURE
            assert tracker2.get_current_phase() == DSPPhase.MEASURE


class TestMCPToolsExistence:
    """Tests for MCP tool existence."""

    def test_dsm_start_tool_exists(self):
        """dsm_start MCP tool exists."""
        from governance.mcp_server import dsm_start
        assert dsm_start is not None
        assert callable(dsm_start)

    def test_dsm_advance_tool_exists(self):
        """dsm_advance MCP tool exists."""
        from governance.mcp_server import dsm_advance
        assert dsm_advance is not None
        assert callable(dsm_advance)

    def test_dsm_checkpoint_tool_exists(self):
        """dsm_checkpoint MCP tool exists."""
        from governance.mcp_server import dsm_checkpoint
        assert dsm_checkpoint is not None
        assert callable(dsm_checkpoint)

    def test_dsm_status_tool_exists(self):
        """dsm_status MCP tool exists."""
        from governance.mcp_server import dsm_status
        assert dsm_status is not None
        assert callable(dsm_status)

    def test_dsm_complete_tool_exists(self):
        """dsm_complete MCP tool exists."""
        from governance.mcp_server import dsm_complete
        assert dsm_complete is not None
        assert callable(dsm_complete)

    def test_dsm_finding_tool_exists(self):
        """dsm_finding MCP tool exists."""
        from governance.mcp_server import dsm_finding
        assert dsm_finding is not None
        assert callable(dsm_finding)

    def test_dsm_metrics_tool_exists(self):
        """dsm_metrics MCP tool exists."""
        from governance.mcp_server import dsm_metrics
        assert dsm_metrics is not None
        assert callable(dsm_metrics)


class TestMCPToolsFunctionality:
    """Tests for MCP tool functionality."""

    def test_dsm_start_returns_json(self):
        """dsm_start returns valid JSON."""
        from governance.mcp_server import dsm_start
        from governance.dsm_tracker import reset_tracker, get_tracker, DSMTracker

        # Full reset: clear global and create fresh tracker with temp state
        reset_tracker()
        # Force a fresh tracker with no state file
        import governance.dsm_tracker as dt
        dt._tracker = DSMTracker(state_file=str(Path(tempfile.gettempdir()) / f".dsm_state_test_{id(self)}.json"))

        result = dsm_start("MCP-TEST")

        parsed = json.loads(result)
        assert "cycle_id" in parsed
        assert parsed["batch_id"] == "MCP-TEST"

    def test_dsm_advance_returns_json(self):
        """dsm_advance returns valid JSON."""
        from governance.mcp_server import dsm_start, dsm_advance
        from governance.dsm_tracker import reset_tracker, DSMTracker

        # Full reset with temp state file
        reset_tracker()
        import governance.dsm_tracker as dt
        dt._tracker = DSMTracker(state_file=str(Path(tempfile.gettempdir()) / f".dsm_state_test_adv_{id(self)}.json"))

        dsm_start("MCP-TEST")
        result = dsm_advance()

        parsed = json.loads(result)
        assert parsed["new_phase"] == "audit"
        assert "required_mcps" in parsed

    def test_dsm_status_returns_json(self):
        """dsm_status returns valid JSON."""
        from governance.mcp_server import dsm_start, dsm_status
        from governance.dsm_tracker import reset_tracker, DSMTracker

        reset_tracker()
        import governance.dsm_tracker as dt
        dt._tracker = DSMTracker(state_file=str(Path(tempfile.gettempdir()) / f".dsm_state_test_status_{id(self)}.json"))

        dsm_start("STATUS-TEST")
        result = dsm_status()

        parsed = json.loads(result)
        assert "active" in parsed
        assert parsed["active"] is True

    def test_dsm_checkpoint_returns_json(self):
        """dsm_checkpoint returns valid JSON."""
        from governance.mcp_server import dsm_start, dsm_advance, dsm_checkpoint
        from governance.dsm_tracker import reset_tracker, DSMTracker

        reset_tracker()
        import governance.dsm_tracker as dt
        dt._tracker = DSMTracker(state_file=str(Path(tempfile.gettempdir()) / f".dsm_state_test_cp_{id(self)}.json"))

        dsm_start("CHECKPOINT-TEST")
        dsm_advance()
        result = dsm_checkpoint("Test checkpoint")

        parsed = json.loads(result)
        assert parsed["description"] == "Test checkpoint"
        assert "timestamp" in parsed

    def test_dsm_finding_returns_json(self):
        """dsm_finding returns valid JSON."""
        from governance.mcp_server import dsm_start, dsm_advance, dsm_finding
        from governance.dsm_tracker import reset_tracker, DSMTracker

        reset_tracker()
        import governance.dsm_tracker as dt
        dt._tracker = DSMTracker(state_file=str(Path(tempfile.gettempdir()) / f".dsm_state_test_find_{id(self)}.json"))

        dsm_start("FINDING-TEST")
        dsm_advance()
        result = dsm_finding("gap", "Missing tests", "HIGH", "RULE-004")

        parsed = json.loads(result)
        assert "finding_id" in parsed
        assert parsed["finding_type"] == "gap"
        assert "RULE-004" in parsed["related_rules"]


class TestMetricsUpdate:
    """Tests for metrics update functionality."""

    def test_update_metrics_adds_to_cycle(self):
        """update_metrics adds metrics to cycle."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.update_metrics({"tests": 100, "coverage": 80})

            assert tracker.current_cycle.metrics["tests"] == 100
            assert tracker.current_cycle.metrics["coverage"] == 80

    def test_update_metrics_merges_with_existing(self):
        """update_metrics merges with existing metrics."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            tracker.update_metrics({"tests": 100})
            tracker.update_metrics({"coverage": 80})

            assert tracker.current_cycle.metrics["tests"] == 100
            assert tracker.current_cycle.metrics["coverage"] == 80

    def test_update_metrics_no_cycle_raises(self):
        """update_metrics without cycle raises ValueError."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            with pytest.raises(ValueError, match="No cycle in progress"):
                tracker.update_metrics({"key": "value"})


class TestRuleCompliance:
    """Tests for RULE-012 compliance."""

    def test_phases_match_rule_012(self):
        """DSP phases match RULE-012 specification."""
        from governance.dsm_tracker import DSPPhase

        # Per RULE-012: AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
        order = DSPPhase.phase_order()

        assert order[0] == DSPPhase.AUDIT
        assert order[1] == DSPPhase.HYPOTHESIZE
        assert order[2] == DSPPhase.MEASURE
        assert order[3] == DSPPhase.OPTIMIZE
        assert order[4] == DSPPhase.VALIDATE
        assert order[5] == DSPPhase.DREAM
        assert order[6] == DSPPhase.REPORT

    def test_evidence_references_rule_012(self):
        """Evidence file references RULE-012."""
        from governance.dsm_tracker import DSMTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = DSMTracker(
                evidence_dir=tmpdir,
                state_file=str(Path(tmpdir) / ".dsm_state.json")
            )

            tracker.start_cycle()
            tracker.advance_phase()
            evidence_path = tracker.complete_cycle()

            with open(evidence_path, encoding="utf-8") as f:
                content = f.read()

            assert "RULE-012" in content

    def test_mcps_per_phase_per_rule_012(self):
        """MCP requirements match RULE-012 specification."""
        from governance.dsm_tracker import DSPPhase

        # Per RULE-012 table
        expected = {
            DSPPhase.AUDIT: ["claude-mem", "governance"],
            DSPPhase.HYPOTHESIZE: ["sequential-thinking"],
            DSPPhase.MEASURE: ["powershell", "llm-sandbox"],
            DSPPhase.VALIDATE: ["pytest", "llm-sandbox"],
        }

        for phase, expected_mcps in expected.items():
            for mcp in expected_mcps:
                assert mcp in phase.required_mcps, f"{mcp} not in {phase.value}"
