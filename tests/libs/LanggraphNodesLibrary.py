"""
LangGraph Nodes Library for Robot Framework
Tests for node functions, submit, validate, and assess nodes.
Migrated from tests/test_langgraph_workflow.py
Per: RF-007 Robot Framework Migration
"""
from robot.api.deco import keyword


class LanggraphNodesLibrary:
    """Robot Framework keywords for LangGraph node tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Node Functions Existence Tests
    # =========================================================================

    @keyword("Submit Node Exists")
    def submit_node_exists(self):
        """Test that submit_node function exists."""
        try:
            from governance.langgraph_workflow import submit_node
            return {"exists": submit_node is not None, "callable": callable(submit_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Node Exists")
    def validate_node_exists(self):
        """Test that validate_node function exists."""
        try:
            from governance.langgraph_workflow import validate_node
            return {"exists": validate_node is not None, "callable": callable(validate_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Assess Node Exists")
    def assess_node_exists(self):
        """Test that assess_node function exists."""
        try:
            from governance.langgraph_workflow import assess_node
            return {"exists": assess_node is not None, "callable": callable(assess_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Vote Node Exists")
    def vote_node_exists(self):
        """Test that vote_node function exists."""
        try:
            from governance.langgraph_workflow import vote_node
            return {"exists": vote_node is not None, "callable": callable(vote_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decide Node Exists")
    def decide_node_exists(self):
        """Test that decide_node function exists."""
        try:
            from governance.langgraph_workflow import decide_node
            return {"exists": decide_node is not None, "callable": callable(decide_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Implement Node Exists")
    def implement_node_exists(self):
        """Test that implement_node function exists."""
        try:
            from governance.langgraph_workflow import implement_node
            return {"exists": implement_node is not None, "callable": callable(implement_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Complete Node Exists")
    def complete_node_exists(self):
        """Test that complete_node function exists."""
        try:
            from governance.langgraph_workflow import complete_node
            return {"exists": complete_node is not None, "callable": callable(complete_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Reject Node Exists")
    def reject_node_exists(self):
        """Test that reject_node function exists."""
        try:
            from governance.langgraph_workflow import reject_node
            return {"exists": reject_node is not None, "callable": callable(reject_node)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Submit Node Logic Tests
    # =========================================================================

    @keyword("Submit Generates Proposal Id")
    def submit_generates_proposal_id(self):
        """Test that submit generates proposal ID if not set."""
        try:
            from governance.langgraph_workflow import submit_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )

            result = submit_node(state)

            return {
                "has_proposal_id": "proposal_id" in result,
                "id_prefix_correct": result["proposal_id"].startswith("PROP-")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Submit Rejects Low Trust Submitter")
    def submit_rejects_low_trust_submitter(self):
        """Test that submit rejects submitters with low trust score."""
        try:
            from governance.langgraph_workflow import submit_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"],
                submitter_trust_score=0.2  # Below 0.3 threshold
            )

            result = submit_node(state)

            return {
                "status_failed": result["status"] == "failed",
                "has_trust_error": "trust score too low" in result.get("error_message", "")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Submit Accepts Valid Submitter")
    def submit_accepts_valid_submitter(self):
        """Test that submit accepts submitters with sufficient trust score."""
        try:
            from governance.langgraph_workflow import submit_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"],
                submitter_trust_score=0.8
            )

            result = submit_node(state)

            return {
                "status_running": result["status"] == "running",
                "submit_completed": "submit" in result["phases_completed"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Validate Node Logic Tests
    # =========================================================================

    @keyword("Validate Requires Hypothesis")
    def validate_requires_hypothesis(self):
        """Test that validation fails without hypothesis."""
        try:
            from governance.langgraph_workflow import validate_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="",  # Empty
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit"]

            result = validate_node(state)

            return {
                "validation_failed": not result["validation_passed"],
                "has_hypothesis_error": any("Hypothesis" in e for e in result["validation_errors"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Requires Evidence")
    def validate_requires_evidence(self):
        """Test that validation fails without evidence."""
        try:
            from governance.langgraph_workflow import validate_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Valid hypothesis here",
                evidence=[]  # Empty
            )
            state["phases_completed"] = ["submit"]

            result = validate_node(state)

            return {
                "validation_failed": not result["validation_passed"],
                "has_evidence_error": any("evidence" in e.lower() for e in result["validation_errors"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Modify Requires Rule Id")
    def validate_modify_requires_rule_id(self):
        """Test that validation fails for modify without rule_id."""
        try:
            from governance.langgraph_workflow import validate_node, create_initial_state

            state = create_initial_state(
                action="modify",
                hypothesis="Valid hypothesis here",
                evidence=["Evidence"],
                directive="New directive"
                # Missing rule_id
            )
            state["phases_completed"] = ["submit"]

            result = validate_node(state)

            return {
                "validation_failed": not result["validation_passed"],
                "has_rule_id_error": any("rule_id" in e for e in result["validation_errors"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Create Requires Directive")
    def validate_create_requires_directive(self):
        """Test that validation fails for create without directive."""
        try:
            from governance.langgraph_workflow import validate_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Valid hypothesis here",
                evidence=["Evidence"]
                # Missing directive
            )
            state["phases_completed"] = ["submit"]

            result = validate_node(state)

            return {
                "validation_failed": not result["validation_passed"],
                "has_directive_error": any("directive" in e for e in result["validation_errors"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Passes Valid Create")
    def validate_passes_valid_create(self):
        """Test that validation passes for valid create proposal."""
        try:
            from governance.langgraph_workflow import validate_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Valid hypothesis here",
                evidence=["Evidence 1", "Evidence 2"],
                directive="New rule directive"
            )
            state["phases_completed"] = ["submit"]

            result = validate_node(state)

            return {
                "validation_passed": result["validation_passed"],
                "no_errors": len(result["validation_errors"]) == 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Assess Node Logic Tests
    # =========================================================================

    @keyword("Assess Returns Impact Score")
    def assess_returns_impact_score(self):
        """Test that assessment returns impact score."""
        try:
            from governance.langgraph_workflow import assess_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit", "validate"]

            result = assess_node(state)

            return {
                "has_impact_score": "impact_score" in result,
                "score_non_negative": result["impact_score"] >= 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Assess Returns Risk Level")
    def assess_returns_risk_level(self):
        """Test that assessment returns risk level."""
        try:
            from governance.langgraph_workflow import assess_node, create_initial_state

            state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            state["phases_completed"] = ["submit", "validate"]

            result = assess_node(state)

            valid_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            return {"risk_level_valid": result["risk_level"] in valid_levels}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Deprecate Has Higher Impact")
    def deprecate_has_higher_impact(self):
        """Test that deprecate action has higher impact score."""
        try:
            from governance.langgraph_workflow import assess_node, create_initial_state

            create_state = create_initial_state(
                action="create",
                hypothesis="Test hypothesis",
                evidence=["Evidence"]
            )
            deprecate_state = create_initial_state(
                action="deprecate",
                hypothesis="Test hypothesis",
                evidence=["Evidence"],
                rule_id="RULE-001"
            )

            create_result = assess_node(create_state)
            deprecate_result = assess_node(deprecate_state)

            return {
                "deprecate_higher": deprecate_result["impact_score"] > create_result["impact_score"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
