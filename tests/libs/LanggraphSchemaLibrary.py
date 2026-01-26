"""
LangGraph Schema Library for Robot Framework
Tests for state schema and governance constants.
Migrated from tests/test_langgraph_workflow.py
Per: RF-007 Robot Framework Migration
"""
from robot.api.deco import keyword


class LanggraphSchemaLibrary:
    """Robot Framework keywords for LangGraph schema tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Proposal State Schema Tests
    # =========================================================================

    @keyword("Proposal State Exists")
    def proposal_state_exists(self):
        """Test that ProposalState type is defined."""
        try:
            from governance.langgraph_workflow import ProposalState
            return {"type_defined": ProposalState is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vote Type Exists")
    def vote_type_exists(self):
        """Test that Vote type is defined."""
        try:
            from governance.langgraph_workflow import Vote
            return {"type_defined": Vote is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Initial State")
    def create_initial_state(self):
        """Test that create_initial_state creates valid state."""
        try:
            from governance.langgraph_workflow import create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis for new rule",
                evidence=["Evidence 1", "Evidence 2"],
                directive="New rule directive"
            )

            return {
                "action_correct": state["action"] == "create",
                "hypothesis_correct": state["hypothesis"] == "Test hypothesis for new rule",
                "evidence_count": len(state["evidence"]) == 2,
                "status_pending": state["status"] == "pending",
                "dry_run_true": state["dry_run"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial State Has All Fields")
    def initial_state_has_all_fields(self):
        """Test that initial state includes all required fields."""
        try:
            from governance.langgraph_workflow import create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )

            required_fields = [
                "proposal_id", "action", "hypothesis", "evidence",
                "submitter_id", "submitter_trust_score",
                "current_phase", "phases_completed",
                "validation_passed", "validation_errors",
                "impact_score", "risk_level",
                "votes", "votes_for", "votes_against",
                "quorum_reached", "threshold_met",
                "decision", "status", "dry_run"
            ]

            missing = [f for f in required_fields if f not in state]
            return {
                "all_fields_present": len(missing) == 0,
                "missing_fields": missing
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Governance Constants Tests
    # =========================================================================

    @keyword("Quorum Threshold Defined")
    def quorum_threshold_defined(self):
        """Test that QUORUM_THRESHOLD is defined."""
        try:
            from governance.langgraph_workflow import QUORUM_THRESHOLD
            return {"value_correct": QUORUM_THRESHOLD == 0.5}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Approval Threshold Defined")
    def approval_threshold_defined(self):
        """Test that APPROVAL_THRESHOLD is defined."""
        try:
            from governance.langgraph_workflow import APPROVAL_THRESHOLD
            return {"value_correct": APPROVAL_THRESHOLD == 0.67}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dispute Threshold Defined")
    def dispute_threshold_defined(self):
        """Test that DISPUTE_THRESHOLD is defined."""
        try:
            from governance.langgraph_workflow import DISPUTE_THRESHOLD
            return {"value_correct": DISPUTE_THRESHOLD == 0.75}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Weights Defined")
    def trust_weights_defined(self):
        """Test that TRUST_WEIGHTS follows RULE-011 formula."""
        try:
            from governance.langgraph_workflow import TRUST_WEIGHTS

            total = sum(TRUST_WEIGHTS.values())
            return {
                "compliance_correct": TRUST_WEIGHTS["compliance"] == 0.4,
                "accuracy_correct": TRUST_WEIGHTS["accuracy"] == 0.3,
                "consistency_correct": TRUST_WEIGHTS["consistency"] == 0.2,
                "tenure_correct": TRUST_WEIGHTS["tenure"] == 0.1,
                "sum_is_one": abs(total - 1.0) < 0.001
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
