"""
Unit tests for DSP LangGraph Analysis Nodes.

Per DOC-SIZE-01-v1: Tests for governance/dsm/langgraph/nodes_analysis.py.
Tests: audit_node, hypothesize_node, measure_node.
"""

from unittest.mock import patch

import pytest

from governance.dsm.langgraph.nodes_analysis import (
    audit_node,
    hypothesize_node,
    measure_node,
)


def _base_state(**overrides) -> dict:
    """Create a base DSPState dict for testing."""
    state = {
        "cycle_id": "DSP-TEST-001",
        "phases_completed": [],
        "findings": [],
        "checkpoints": [],
        "phase_results": [],
        "dry_run": True,
        "audit_gaps": [],
        "audit_orphans": [],
        "hypotheses": [],
        "measurements": {},
    }
    state.update(overrides)
    return state


# ── audit_node ────────────────────────────────────────────────


class TestAuditNode:
    def test_dry_run_produces_gaps(self):
        state = _base_state(dry_run=True)
        result = audit_node(state)
        assert result["current_phase"] == "audited"
        assert "audit" in result["phases_completed"]
        assert len(result["audit_gaps"]) == 2
        assert len(result["audit_orphans"]) == 1

    def test_dry_run_no_critical(self):
        state = _base_state(dry_run=True)
        result = audit_node(state)
        assert result["has_critical_gaps"] is False

    def test_findings_created(self):
        state = _base_state(dry_run=True)
        result = audit_node(state)
        assert len(result["findings"]) > 0
        assert result["findings"][0]["type"] == "gap"
        assert result["findings"][0]["phase"] == "audit"

    def test_checkpoints_created(self):
        state = _base_state(dry_run=True)
        result = audit_node(state)
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "audit"

    def test_phase_results_appended(self):
        state = _base_state(dry_run=True)
        result = audit_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "audit"

    def test_preserves_existing_findings(self):
        existing = [{"id": "F-OLD", "type": "existing"}]
        state = _base_state(dry_run=True, findings=existing)
        result = audit_node(state)
        assert any(f["id"] == "F-OLD" for f in result["findings"])

    def test_production_mode_failure_handled(self):
        state = _base_state(dry_run=False)
        with patch("governance.dsm.langgraph.nodes_analysis._get_gap_summary",
                    side_effect=Exception("MCP unavailable"), create=True):
            result = audit_node(state)
        assert "failed" in result["current_phase"]
        assert result["status"] == "failed"


# ── hypothesize_node ──────────────────────────────────────────


class TestHypothesizeNode:
    def test_generates_hypotheses_from_gaps(self):
        state = _base_state(
            audit_gaps=["GAP-001", "GAP-002", "GAP-003", "GAP-004"],
        )
        result = hypothesize_node(state)
        assert result["current_phase"] == "hypothesized"
        assert "hypothesize" in result["phases_completed"]
        assert len(result["hypotheses"]) == 3  # max 3

    def test_no_gaps_produces_healthy_message(self):
        state = _base_state(audit_gaps=[])
        result = hypothesize_node(state)
        assert len(result["hypotheses"]) == 1
        assert "healthy" in result["hypotheses"][0].lower()

    def test_checkpoints_created(self):
        state = _base_state(audit_gaps=["GAP-001"])
        result = hypothesize_node(state)
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "hypothesize"

    def test_phase_results_appended(self):
        state = _base_state(audit_gaps=[])
        result = hypothesize_node(state)
        assert len(result["phase_results"]) == 1

    def test_preserves_existing_checkpoints(self):
        existing = [{"phase": "audit", "description": "done"}]
        state = _base_state(audit_gaps=[], checkpoints=existing)
        result = hypothesize_node(state)
        assert len(result["checkpoints"]) == 2


# ── measure_node ──────────────────────────────────────────────


class TestMeasureNode:
    def test_collects_measurements(self):
        state = _base_state(
            audit_gaps=["G1", "G2"],
            audit_orphans=["O1"],
            hypotheses=["H1"],
        )
        result = measure_node(state)
        assert result["current_phase"] == "measured"
        assert "measure" in result["phases_completed"]
        assert result["measurements"]["gaps_count"] == 2
        assert result["measurements"]["orphans_count"] == 1
        assert result["measurements"]["hypotheses_count"] == 1

    def test_checkpoints_created(self):
        state = _base_state()
        result = measure_node(state)
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "measure"

    def test_phase_results_appended(self):
        state = _base_state()
        result = measure_node(state)
        assert len(result["phase_results"]) == 1

    def test_timestamp_in_measurements(self):
        state = _base_state()
        result = measure_node(state)
        assert "timestamp" in result["measurements"]

    def test_empty_state_zero_counts(self):
        state = _base_state()
        result = measure_node(state)
        assert result["measurements"]["gaps_count"] == 0
        assert result["measurements"]["orphans_count"] == 0
        assert result["measurements"]["hypotheses_count"] == 0
