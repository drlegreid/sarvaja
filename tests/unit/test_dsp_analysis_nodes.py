"""
Unit tests for DSP LangGraph Analysis Nodes.

Per DOC-SIZE-01-v1: Tests for extracted nodes_analysis.py module.
Tests: audit_node, hypothesize_node, measure_node.
"""

import pytest
from unittest.mock import patch

from governance.dsm.langgraph.state import create_initial_state


def _base_state(**overrides):
    """Create a base DSP state for testing."""
    state = create_initial_state(dry_run=True, force_advance=True)
    state.update(overrides)
    return state


class TestAuditNode:
    """Tests for audit_node()."""

    def test_dry_run_returns_gaps(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        assert result["current_phase"] == "audited"
        assert "audit" in result["phases_completed"]
        assert len(result["audit_gaps"]) == 2
        assert "GAP-TEST-001" in result["audit_gaps"]

    def test_dry_run_returns_orphans(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        assert len(result["audit_orphans"]) == 1
        assert "ORPHAN-TASK-001" in result["audit_orphans"]

    def test_creates_findings(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        assert len(result["findings"]) > 0
        finding = result["findings"][0]
        assert finding["type"] == "gap"
        assert finding["phase"] == "audit"
        assert finding["id"].startswith("FINDING-AUDIT-")

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        audit_cp = [c for c in result["checkpoints"] if c["phase"] == "audit"]
        assert len(audit_cp) == 1
        assert "gaps" in audit_cp[0]["metrics"]
        assert "orphans" in audit_cp[0]["metrics"]

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        assert len(result["phase_results"]) == 1
        pr = result["phase_results"][0]
        assert pr["phase"] == "audit"
        assert pr["status"] == "success"

    def test_preserves_existing_findings(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        existing = [{"id": "EXISTING-001", "type": "manual", "description": "existing", "severity": "LOW", "phase": "manual", "timestamp": "t"}]
        state = _base_state(findings=existing)
        result = audit_node(state)
        assert result["findings"][0]["id"] == "EXISTING-001"
        assert len(result["findings"]) > 1

    def test_has_critical_gaps_false_by_default(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        state = _base_state()
        result = audit_node(state)
        assert result["has_critical_gaps"] is False

    def test_failure_returns_error(self):
        from governance.dsm.langgraph.nodes_analysis import audit_node

        # dry_run=False triggers lazy import of _get_gap_summary which
        # doesn't exist, causing ImportError → caught by except clause
        state = _base_state(dry_run=False)
        result = audit_node(state)
        assert result["current_phase"] == "audit_failed"
        assert result["status"] == "failed"
        assert "AUDIT phase failed" in result["error_message"]


class TestHypothesizeNode:
    """Tests for hypothesize_node()."""

    def test_generates_hypotheses_from_gaps(self):
        from governance.dsm.langgraph.nodes_analysis import hypothesize_node

        state = _base_state(
            audit_gaps=["GAP-001", "GAP-002", "GAP-003"],
            phases_completed=["audit"],
        )
        result = hypothesize_node(state)
        assert result["current_phase"] == "hypothesized"
        assert "hypothesize" in result["phases_completed"]
        assert len(result["hypotheses"]) == 3

    def test_no_gaps_generates_healthy_message(self):
        from governance.dsm.langgraph.nodes_analysis import hypothesize_node

        state = _base_state(audit_gaps=[], phases_completed=["audit"])
        result = hypothesize_node(state)
        assert len(result["hypotheses"]) == 1
        assert "healthy" in result["hypotheses"][0].lower()

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_analysis import hypothesize_node

        state = _base_state(
            audit_gaps=["GAP-001"],
            phases_completed=["audit"],
        )
        result = hypothesize_node(state)
        hyp_cp = [c for c in result["checkpoints"] if c["phase"] == "hypothesize"]
        assert len(hyp_cp) == 1
        assert "hypotheses" in hyp_cp[0]["metrics"]

    def test_caps_at_3_gaps(self):
        from governance.dsm.langgraph.nodes_analysis import hypothesize_node

        state = _base_state(
            audit_gaps=["G1", "G2", "G3", "G4", "G5"],
            phases_completed=["audit"],
        )
        result = hypothesize_node(state)
        assert len(result["hypotheses"]) == 3

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_analysis import hypothesize_node

        state = _base_state(
            audit_gaps=["GAP-001"],
            phases_completed=["audit"],
        )
        result = hypothesize_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "hypothesize"


class TestMeasureNode:
    """Tests for measure_node()."""

    def test_collects_measurements(self):
        from governance.dsm.langgraph.nodes_analysis import measure_node

        state = _base_state(
            audit_gaps=["G1", "G2"],
            audit_orphans=["O1"],
            hypotheses=["H1"],
            phases_completed=["audit", "hypothesize"],
        )
        result = measure_node(state)
        assert result["current_phase"] == "measured"
        assert "measure" in result["phases_completed"]
        assert result["measurements"]["gaps_count"] == 2
        assert result["measurements"]["orphans_count"] == 1
        assert result["measurements"]["hypotheses_count"] == 1

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_analysis import measure_node

        state = _base_state(
            audit_gaps=[], audit_orphans=[], hypotheses=[],
            phases_completed=["audit", "hypothesize"],
        )
        result = measure_node(state)
        meas_cp = [c for c in result["checkpoints"] if c["phase"] == "measure"]
        assert len(meas_cp) == 1
        assert "gaps_count" in meas_cp[0]["metrics"]

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_analysis import measure_node

        state = _base_state(
            audit_gaps=[], audit_orphans=[], hypotheses=[],
            phases_completed=["audit", "hypothesize"],
        )
        result = measure_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "measure"
        assert result["phase_results"][0]["status"] == "success"

    def test_measurements_include_timestamp(self):
        from governance.dsm.langgraph.nodes_analysis import measure_node

        state = _base_state(
            audit_gaps=[], audit_orphans=[], hypotheses=[],
            phases_completed=["audit", "hypothesize"],
        )
        result = measure_node(state)
        assert "timestamp" in result["measurements"]
