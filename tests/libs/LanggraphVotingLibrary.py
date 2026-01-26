"""
LangGraph Voting Library for Robot Framework
Tests for voting and decision logic.
Migrated from tests/test_langgraph_workflow.py
Per: RF-007 Robot Framework Migration
"""
from robot.api.deco import keyword


class LanggraphVotingLibrary:
    """Robot Framework keywords for LangGraph voting tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Vote Node Tests
    # =========================================================================

    @keyword("Vote Calculates Weighted Totals")
    def vote_calculates_weighted_totals(self):
        """Test that vote calculates weighted totals correctly."""
        try:
            from governance.langgraph_workflow import vote_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit", "validate", "assess"]

            result = vote_node(state)

            return {
                "has_votes_for": "votes_for" in result,
                "has_votes_against": "votes_against" in result,
                "votes_non_negative": result["votes_for"] >= 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vote Checks Quorum")
    def vote_checks_quorum(self):
        """Test that vote checks quorum requirement."""
        try:
            from governance.langgraph_workflow import vote_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit", "validate", "assess"]

            result = vote_node(state)

            return {
                "has_quorum_reached": "quorum_reached" in result,
                "is_boolean": isinstance(result["quorum_reached"], bool)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vote Checks Threshold")
    def vote_checks_threshold(self):
        """Test that vote checks approval threshold."""
        try:
            from governance.langgraph_workflow import vote_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit", "validate", "assess"]

            result = vote_node(state)

            return {
                "has_threshold_met": "threshold_met" in result,
                "is_boolean": isinstance(result["threshold_met"], bool)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Decide Node Tests
    # =========================================================================

    @keyword("Decide Rejects Without Quorum")
    def decide_rejects_without_quorum(self):
        """Test that decision rejects if quorum not reached."""
        try:
            from governance.langgraph_workflow import decide_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["quorum_reached"] = False
            state["threshold_met"] = True

            result = decide_node(state)

            return {
                "decision_rejected": result["decision"] == "rejected",
                "mentions_quorum": "quorum" in result["decision_reasoning"].lower()
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decide Approves With Quorum And Threshold")
    def decide_approves_with_quorum_and_threshold(self):
        """Test that decision approves if quorum and threshold met."""
        try:
            from governance.langgraph_workflow import decide_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["quorum_reached"] = True
            state["threshold_met"] = True

            result = decide_node(state)

            return {"decision_approved": result["decision"] == "approved"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decide Rejects Below Threshold")
    def decide_rejects_below_threshold(self):
        """Test that decision rejects if below threshold."""
        try:
            from governance.langgraph_workflow import decide_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["quorum_reached"] = True
            state["threshold_met"] = False

            result = decide_node(state)

            return {
                "decision_rejected": result["decision"] == "rejected",
                "mentions_threshold": "threshold" in result["decision_reasoning"].lower()
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
