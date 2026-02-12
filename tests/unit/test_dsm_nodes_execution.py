"""
Unit tests for DSP LangGraph Execution Nodes.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/nodes_execution.py module.
Tests: optimize_node, validate_node, dream_node, report_node.
"""

from governance.dsm.langgraph.nodes_execution import (
    optimize_node,
    validate_node,
    dream_node,
    report_node,
)


def _base_state(**kw):
    defaults = {
        "cycle_id": "DSP-TEST-001",
        "phases_completed": [],
        "phase_results": [],
        "checkpoints": [],
        "dry_run": True,
        "hypotheses": ["Fix X", "Improve Y"],
        "audit_gaps": [],
        "optimizations_applied": [],
        "validation_passed": False,
        "evidence_files": [],
    }
    defaults.update(kw)
    return defaults


class TestOptimizeNode:
    def test_dry_run(self):
        result = optimize_node(_base_state())
        assert result["current_phase"] == "optimized"
        assert "optimize" in result["phases_completed"]
        assert len(result["optimizations_applied"]) == 2
        assert "[DRY-RUN]" in result["optimizations_applied"][0]

    def test_production(self):
        result = optimize_node(_base_state(dry_run=False))
        assert result["current_phase"] == "optimized"
        assert len(result["optimizations_applied"]) == 2

    def test_no_hypotheses(self):
        result = optimize_node(_base_state(dry_run=False, hypotheses=[]))
        assert result["current_phase"] == "optimized"
        assert len(result["optimizations_applied"]) == 0

    def test_checkpoints_appended(self):
        result = optimize_node(_base_state())
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "optimize"

    def test_phase_results(self):
        result = optimize_node(_base_state())
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "optimize"


class TestValidateNode:
    def test_dry_run(self):
        result = validate_node(_base_state())
        assert result["current_phase"] == "validated"
        assert "validate" in result["phases_completed"]
        assert result["validation_results"]["tests_run"] == 10
        assert result["validation_passed"] is False  # 1 test failed

    def test_production(self):
        result = validate_node(_base_state(dry_run=False))
        assert result["current_phase"] == "validated"
        assert result["validation_passed"] is True  # 0 tests failed

    def test_checkpoints(self):
        result = validate_node(_base_state())
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "validate"


class TestDreamNode:
    def test_basic(self):
        result = dream_node(_base_state(
            audit_gaps=["G-1", "G-2"],
            optimizations_applied=["O-1"],
            validation_passed=True,
        ))
        assert result["current_phase"] == "dreamed"
        assert "dream" in result["phases_completed"]
        assert len(result["dream_insights"]) == 3
        assert "2 gaps" in result["dream_insights"][0]

    def test_checkpoints(self):
        result = dream_node(_base_state())
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "dream"


class TestReportNode:
    def test_dry_run(self):
        result = report_node(_base_state())
        assert result["current_phase"] == "reported"
        assert "report" in result["phases_completed"]
        assert len(result["evidence_files"]) == 1
        assert "[DRY-RUN]" in result["evidence_files"][0]

    def test_checkpoints(self):
        result = report_node(_base_state())
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["phase"] == "report"

    def test_existing_evidence_preserved(self):
        result = report_node(_base_state(evidence_files=["existing.md"]))
        assert len(result["evidence_files"]) == 2
        assert "existing.md" in result["evidence_files"]
