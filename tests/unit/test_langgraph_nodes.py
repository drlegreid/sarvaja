"""
Unit tests for LangGraph Workflow Nodes.

Per DOC-SIZE-01-v1: Tests for langgraph/nodes.py module.
Tests: submit_node, validate_node, assess_node, vote_node,
       decide_node, implement_node, complete_node, reject_node.
"""

import pytest

from governance.langgraph.nodes import (
    submit_node,
    validate_node,
    assess_node,
    vote_node,
    decide_node,
    implement_node,
    complete_node,
    reject_node,
)


def _base_state(**overrides):
    state = {
        "proposal_id": "PROP-TEST",
        "action": "create",
        "submitter_id": "AGENT-001",
        "submitter_trust_score": 0.8,
        "hypothesis": "We need a new rule for testing",
        "evidence": ["evidence1"],
        "rule_id": None,
        "directive": "Do something",
        "dry_run": True,
        "phases_completed": [],
        "status": "running",
        "current_phase": "init",
        "votes": [],
        "votes_for": 0,
        "votes_against": 0,
        "quorum_reached": True,
        "threshold_met": True,
        "decision": "approved",
        "decision_reasoning": "",
        "error_message": None,
        "validation_passed": True,
        "validation_errors": [],
        "impact_score": 0,
        "risk_level": "LOW",
        "affected_rules": [],
        "recommendations": [],
        "changes_applied": [],
        "rollback_available": False,
        "started_at": None,
        "completed_at": None,
    }
    state.update(overrides)
    return state


class TestSubmitNode:
    def test_success(self):
        result = submit_node(_base_state())
        assert result["current_phase"] == "submitted"
        assert result["status"] == "running"
        assert "submit" in result["phases_completed"]

    def test_low_trust_rejected(self):
        result = submit_node(_base_state(submitter_trust_score=0.2))
        assert result["current_phase"] == "submit_failed"
        assert result["status"] == "failed"
        assert "trust score too low" in result["error_message"].lower()

    def test_generates_proposal_id(self):
        result = submit_node(_base_state(proposal_id=None))
        assert result["proposal_id"].startswith("PROP-")

    def test_uses_existing_proposal_id(self):
        result = submit_node(_base_state(proposal_id="PROP-CUSTOM"))
        assert result["proposal_id"] == "PROP-CUSTOM"

    def test_trust_boundary(self):
        result = submit_node(_base_state(submitter_trust_score=0.3))
        assert result["status"] == "running"


class TestValidateNode:
    def test_valid_create(self):
        result = validate_node(_base_state())
        assert result["validation_passed"] is True
        assert result["current_phase"] == "validated"

    def test_missing_hypothesis(self):
        result = validate_node(_base_state(hypothesis=None))
        assert result["validation_passed"] is False
        assert "Hypothesis" in result["validation_errors"][0]

    def test_short_hypothesis(self):
        result = validate_node(_base_state(hypothesis="short"))
        assert result["validation_passed"] is False

    def test_no_evidence(self):
        result = validate_node(_base_state(evidence=[]))
        assert result["validation_passed"] is False

    def test_modify_no_rule_id(self):
        result = validate_node(_base_state(action="modify", rule_id=None))
        assert result["validation_passed"] is False
        assert any("rule_id" in e for e in result["validation_errors"])

    def test_deprecate_no_rule_id(self):
        result = validate_node(_base_state(action="deprecate", rule_id=None))
        assert result["validation_passed"] is False

    def test_create_no_directive(self):
        result = validate_node(_base_state(directive=None))
        assert result["validation_passed"] is False

    def test_modify_with_rule_and_directive(self):
        result = validate_node(_base_state(action="modify", rule_id="RULE-001",
                                           directive="Updated directive"))
        assert result["validation_passed"] is True

    def test_phases_appended(self):
        result = validate_node(_base_state(phases_completed=["submit"]))
        assert result["phases_completed"] == ["submit", "validate"]


class TestAssessNode:
    def test_create_action(self):
        result = assess_node(_base_state(action="create"))
        assert result["impact_score"] == 20.0
        assert result["risk_level"] == "LOW"

    def test_modify_action(self):
        result = assess_node(_base_state(action="modify"))
        assert result["impact_score"] == 40.0
        assert result["risk_level"] == "MEDIUM"

    def test_deprecate_action(self):
        result = assess_node(_base_state(action="deprecate"))
        assert result["impact_score"] == 60.0
        assert result["affected_rules"] == ["RULE-001"]

    def test_recommendations_generated(self):
        result = assess_node(_base_state())
        assert len(result["recommendations"]) >= 1

    def test_phases_appended(self):
        result = assess_node(_base_state(phases_completed=["submit", "validate"]))
        assert "assess" in result["phases_completed"]


class TestVoteNode:
    def test_dry_run_simulates_votes(self):
        result = vote_node(_base_state(dry_run=True))
        assert len(result["votes"]) == 3
        assert result["votes_for"] > 0

    def test_non_dry_run_uses_existing(self):
        votes = [{"agent_id": "A-1", "vote": "approve", "weight": 0.9,
                  "reasoning": "Yes", "timestamp": "2026-01-01"}]
        result = vote_node(_base_state(dry_run=False, votes=votes))
        assert len(result["votes"]) == 1

    def test_quorum_calculation(self):
        result = vote_node(_base_state(dry_run=True))
        # 3 votes, quorum = 5 * 0.5 = 2.5, so 3 >= 2.5 = True
        assert result["quorum_reached"] is True

    def test_threshold_calculation(self):
        result = vote_node(_base_state(dry_run=True))
        # 2 approve (0.85 + 0.72 = 1.57) / total (0.85 + 0.72 + 0.65 = 2.22) ≈ 70.7%
        assert result["threshold_met"] is True  # > 67%


class TestDecideNode:
    def test_approved(self):
        result = decide_node(_base_state(quorum_reached=True, threshold_met=True))
        assert result["decision"] == "approved"

    def test_rejected_no_quorum(self):
        result = decide_node(_base_state(quorum_reached=False, threshold_met=True))
        assert result["decision"] == "rejected"
        assert "Quorum" in result["decision_reasoning"]

    def test_rejected_threshold_not_met(self):
        result = decide_node(_base_state(quorum_reached=True, threshold_met=False))
        assert result["decision"] == "rejected"
        assert "threshold" in result["decision_reasoning"].lower()


class TestImplementNode:
    def test_approved_dry_run(self):
        result = implement_node(_base_state(decision="approved", dry_run=True))
        assert result["current_phase"] == "implemented"
        assert any("DRY-RUN" in c for c in result["changes_applied"])

    def test_not_approved_skipped(self):
        result = implement_node(_base_state(decision="rejected"))
        assert result["current_phase"] == "skipped_implement"
        assert result["changes_applied"] == []

    def test_rollback_available(self):
        result = implement_node(_base_state(decision="approved"))
        assert result["rollback_available"] is True


class TestCompleteNode:
    def test_success(self):
        result = complete_node(_base_state(decision="approved", error_message=None))
        assert result["status"] == "success"
        assert result["current_phase"] == "complete"

    def test_failed_with_error(self):
        result = complete_node(_base_state(decision="approved",
                                           error_message="validation failed"))
        assert result["status"] == "failed"

    def test_rejected_decision(self):
        result = complete_node(_base_state(decision="rejected", error_message=None))
        assert result["status"] == "failed"


class TestRejectNode:
    def test_basic(self):
        result = reject_node(_base_state(
            error_message="Trust too low",
            phases_completed=["submit"],
        ))
        assert result["current_phase"] == "rejected"
        assert result["status"] == "failed"
        assert "reject" in result["phases_completed"]
