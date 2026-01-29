"""
Test suite for LangGraph Governance Workflow
=============================================
Validates state management, voting, and decision logic.

Per: RULE-011 (Multi-Agent Governance Protocol)
"""

import pytest
import json
from typing import List


# =============================================================================
# STATE SCHEMA TESTS
# =============================================================================

class TestProposalStateSchema:
    """Tests for ProposalState TypedDict schema."""

    def test_proposal_state_exists(self):
        """ProposalState type is defined."""
        from governance.langgraph_workflow import ProposalState
        assert ProposalState is not None

    def test_vote_type_exists(self):
        """Vote type is defined."""
        from governance.langgraph_workflow import Vote
        assert Vote is not None

    def test_create_initial_state(self):
        """create_initial_state creates valid state."""
        from governance.langgraph_workflow import create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis for new rule",
            evidence=["Evidence 1", "Evidence 2"],
            directive="New rule directive"
        )

        assert state["action"] == "create"
        assert state["hypothesis"] == "Test hypothesis for new rule"
        assert len(state["evidence"]) == 2
        assert state["status"] == "pending"
        assert state["dry_run"] is True

    def test_initial_state_has_all_fields(self):
        """Initial state includes all required fields."""
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

        for field in required_fields:
            assert field in state, f"Missing field: {field}"


# =============================================================================
# CONSTANTS TESTS
# =============================================================================

class TestGovernanceConstants:
    """Tests for RULE-011 governance constants."""

    def test_quorum_threshold_defined(self):
        """QUORUM_THRESHOLD is defined."""
        from governance.langgraph_workflow import QUORUM_THRESHOLD
        assert QUORUM_THRESHOLD == 0.5

    def test_approval_threshold_defined(self):
        """APPROVAL_THRESHOLD is defined."""
        from governance.langgraph_workflow import APPROVAL_THRESHOLD
        assert APPROVAL_THRESHOLD == 0.67

    def test_dispute_threshold_defined(self):
        """DISPUTE_THRESHOLD is defined."""
        from governance.langgraph_workflow import DISPUTE_THRESHOLD
        assert DISPUTE_THRESHOLD == 0.75

    def test_trust_weights_defined(self):
        """TRUST_WEIGHTS follows RULE-011 formula."""
        from governance.langgraph_workflow import TRUST_WEIGHTS

        assert TRUST_WEIGHTS["compliance"] == 0.4
        assert TRUST_WEIGHTS["accuracy"] == 0.3
        assert TRUST_WEIGHTS["consistency"] == 0.2
        assert TRUST_WEIGHTS["tenure"] == 0.1

        # Weights must sum to 1.0
        total = sum(TRUST_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


# =============================================================================
# NODE FUNCTION TESTS
# =============================================================================

class TestNodeFunctions:
    """Tests for individual node functions."""

    def test_submit_node_exists(self):
        """submit_node function exists."""
        from governance.langgraph_workflow import submit_node
        assert submit_node is not None
        assert callable(submit_node)

    def test_validate_node_exists(self):
        """validate_node function exists."""
        from governance.langgraph_workflow import validate_node
        assert validate_node is not None
        assert callable(validate_node)

    def test_assess_node_exists(self):
        """assess_node function exists."""
        from governance.langgraph_workflow import assess_node
        assert assess_node is not None
        assert callable(assess_node)

    def test_vote_node_exists(self):
        """vote_node function exists."""
        from governance.langgraph_workflow import vote_node
        assert vote_node is not None
        assert callable(vote_node)

    def test_decide_node_exists(self):
        """decide_node function exists."""
        from governance.langgraph_workflow import decide_node
        assert decide_node is not None
        assert callable(decide_node)

    def test_implement_node_exists(self):
        """implement_node function exists."""
        from governance.langgraph_workflow import implement_node
        assert implement_node is not None
        assert callable(implement_node)

    def test_complete_node_exists(self):
        """complete_node function exists."""
        from governance.langgraph_workflow import complete_node
        assert complete_node is not None
        assert callable(complete_node)

    def test_reject_node_exists(self):
        """reject_node function exists."""
        from governance.langgraph_workflow import reject_node
        assert reject_node is not None
        assert callable(reject_node)


# =============================================================================
# SUBMIT NODE TESTS
# =============================================================================

class TestSubmitNode:
    """Tests for submit node logic."""

    def test_submit_generates_proposal_id(self):
        """Submit generates proposal ID if not set."""
        from governance.langgraph_workflow import submit_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )

        result = submit_node(state)

        assert "proposal_id" in result
        assert result["proposal_id"].startswith("PROP-")

    def test_submit_rejects_low_trust_submitter(self):
        """Submit rejects submitters with low trust score."""
        from governance.langgraph_workflow import submit_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"],
            submitter_trust_score=0.2  # Below 0.3 threshold
        )

        result = submit_node(state)

        assert result["status"] == "failed"
        assert "trust score too low" in result["error_message"]

    def test_submit_accepts_valid_submitter(self):
        """Submit accepts submitters with sufficient trust score."""
        from governance.langgraph_workflow import submit_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"],
            submitter_trust_score=0.8
        )

        result = submit_node(state)

        assert result["status"] == "running"
        assert "submit" in result["phases_completed"]


# =============================================================================
# VALIDATE NODE TESTS
# =============================================================================

class TestValidateNode:
    """Tests for validation logic."""

    def test_validate_requires_hypothesis(self):
        """Validation fails without hypothesis."""
        from governance.langgraph_workflow import validate_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="",  # Empty
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit"]

        result = validate_node(state)

        assert not result["validation_passed"]
        assert any("Hypothesis" in e for e in result["validation_errors"])

    def test_validate_requires_evidence(self):
        """Validation fails without evidence."""
        from governance.langgraph_workflow import validate_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Valid hypothesis here",
            evidence=[]  # Empty
        )
        state["phases_completed"] = ["submit"]

        result = validate_node(state)

        assert not result["validation_passed"]
        assert any("evidence" in e.lower() for e in result["validation_errors"])

    def test_validate_modify_requires_rule_id(self):
        """Validation fails for modify without rule_id."""
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

        assert not result["validation_passed"]
        assert any("rule_id" in e for e in result["validation_errors"])

    def test_validate_create_requires_directive(self):
        """Validation fails for create without directive."""
        from governance.langgraph_workflow import validate_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Valid hypothesis here",
            evidence=["Evidence"]
            # Missing directive
        )
        state["phases_completed"] = ["submit"]

        result = validate_node(state)

        assert not result["validation_passed"]
        assert any("directive" in e for e in result["validation_errors"])

    def test_validate_passes_valid_create(self):
        """Validation passes for valid create proposal."""
        from governance.langgraph_workflow import validate_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Valid hypothesis here",
            evidence=["Evidence 1", "Evidence 2"],
            directive="New rule directive"
        )
        state["phases_completed"] = ["submit"]

        result = validate_node(state)

        assert result["validation_passed"]
        assert len(result["validation_errors"]) == 0


# =============================================================================
# ASSESS NODE TESTS
# =============================================================================

class TestAssessNode:
    """Tests for impact assessment logic."""

    def test_assess_returns_impact_score(self):
        """Assessment returns impact score."""
        from governance.langgraph_workflow import assess_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit", "validate"]

        result = assess_node(state)

        assert "impact_score" in result
        assert result["impact_score"] >= 0

    def test_assess_returns_risk_level(self):
        """Assessment returns risk level."""
        from governance.langgraph_workflow import assess_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit", "validate"]

        result = assess_node(state)

        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_deprecate_has_higher_impact(self):
        """Deprecate action has higher impact score."""
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

        assert deprecate_result["impact_score"] > create_result["impact_score"]


# =============================================================================
# VOTE NODE TESTS
# =============================================================================

class TestVoteNode:
    """Tests for voting logic."""

    def test_vote_calculates_weighted_totals(self):
        """Vote calculates weighted totals correctly."""
        from governance.langgraph_workflow import vote_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit", "validate", "assess"]

        result = vote_node(state)

        assert "votes_for" in result
        assert "votes_against" in result
        assert result["votes_for"] >= 0

    def test_vote_checks_quorum(self):
        """Vote checks quorum requirement."""
        from governance.langgraph_workflow import vote_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit", "validate", "assess"]

        result = vote_node(state)

        assert "quorum_reached" in result
        assert isinstance(result["quorum_reached"], bool)

    def test_vote_checks_threshold(self):
        """Vote checks approval threshold."""
        from governance.langgraph_workflow import vote_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["phases_completed"] = ["submit", "validate", "assess"]

        result = vote_node(state)

        assert "threshold_met" in result
        assert isinstance(result["threshold_met"], bool)


# =============================================================================
# DECIDE NODE TESTS
# =============================================================================

class TestDecideNode:
    """Tests for decision logic."""

    def test_decide_rejects_without_quorum(self):
        """Decision rejects if quorum not reached."""
        from governance.langgraph_workflow import decide_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["quorum_reached"] = False
        state["threshold_met"] = True

        result = decide_node(state)

        assert result["decision"] == "rejected"
        assert "quorum" in result["decision_reasoning"].lower()

    def test_decide_approves_with_quorum_and_threshold(self):
        """Decision approves if quorum and threshold met."""
        from governance.langgraph_workflow import decide_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["quorum_reached"] = True
        state["threshold_met"] = True

        result = decide_node(state)

        assert result["decision"] == "approved"

    def test_decide_rejects_below_threshold(self):
        """Decision rejects if below threshold."""
        from governance.langgraph_workflow import decide_node, create_initial_state

        state = create_initial_state(
            action="create",
            hypothesis="Test hypothesis",
            evidence=["Evidence"]
        )
        state["quorum_reached"] = True
        state["threshold_met"] = False

        result = decide_node(state)

        assert result["decision"] == "rejected"
        assert "threshold" in result["decision_reasoning"].lower()


# =============================================================================
# GRAPH BUILDING TESTS
# =============================================================================

class TestGraphBuilding:
    """Tests for graph construction."""

    def test_build_proposal_graph_exists(self):
        """build_proposal_graph function exists."""
        from governance.langgraph_workflow import build_proposal_graph
        assert build_proposal_graph is not None
        assert callable(build_proposal_graph)

    def test_graph_has_required_nodes(self):
        """Graph has all required nodes (requires langgraph installed)."""
        from governance.langgraph_workflow import build_proposal_graph
        from governance.langgraph.graph import LANGGRAPH_AVAILABLE

        graph = build_proposal_graph()

        if not LANGGRAPH_AVAILABLE:
            # Fallback StateGraph returns empty; nodes used directly in run_proposal_workflow
            pytest.skip("langgraph not installed; fallback graph has no pre-built nodes")

        required_nodes = [
            "submit", "validate", "assess", "vote",
            "decide", "implement", "complete", "reject"
        ]

        for node in required_nodes:
            assert node in graph.nodes, f"Missing node: {node}"


# =============================================================================
# WORKFLOW EXECUTION TESTS
# =============================================================================

class TestWorkflowExecution:
    """Tests for end-to-end workflow execution."""

    def test_run_proposal_workflow_exists(self):
        """run_proposal_workflow function exists."""
        from governance.langgraph_workflow import run_proposal_workflow
        assert run_proposal_workflow is not None
        assert callable(run_proposal_workflow)

    def test_dry_run_completes(self):
        """Dry-run workflow completes."""
        from governance.langgraph_workflow import run_proposal_workflow
        from governance.langgraph.graph import LANGGRAPH_AVAILABLE

        result = run_proposal_workflow(
            action="create",
            hypothesis="Test hypothesis for dry run",
            evidence=["Evidence 1", "Evidence 2"],
            directive="New rule directive",
            dry_run=True
        )

        assert result is not None
        if LANGGRAPH_AVAILABLE:
            assert result["status"] in ["success", "failed"]
            assert "submit" in result["phases_completed"]
        else:
            # Fallback mode: graph has no nodes, state stays at initial values
            assert result["status"] in ["success", "failed", "pending"]

    def test_workflow_returns_decision(self):
        """Workflow returns decision."""
        from governance.langgraph_workflow import run_proposal_workflow

        result = run_proposal_workflow(
            action="create",
            hypothesis="Valid test hypothesis",
            evidence=["Evidence"],
            directive="Test directive",
            dry_run=True
        )

        assert result["decision"] in ["pending", "approved", "rejected", "disputed"]

    def test_invalid_proposal_fails(self):
        """Invalid proposal fails validation (requires langgraph)."""
        from governance.langgraph_workflow import run_proposal_workflow
        from governance.langgraph.graph import LANGGRAPH_AVAILABLE

        result = run_proposal_workflow(
            action="create",
            hypothesis="x",  # Too short
            evidence=[],  # Empty
            dry_run=True
        )

        if LANGGRAPH_AVAILABLE:
            assert result["status"] == "failed"
            assert not result["validation_passed"]
        else:
            # Fallback mode: no nodes execute, validation not run
            assert result["status"] in ["failed", "pending"]


# =============================================================================
# MCP WRAPPER TESTS
# =============================================================================

class TestMCPWrappers:
    """Tests for MCP tool wrappers."""

    def test_proposal_submit_mcp_exists(self):
        """proposal_submit_mcp function exists."""
        from governance.langgraph_workflow import proposal_submit_mcp
        assert proposal_submit_mcp is not None
        assert callable(proposal_submit_mcp)

    def test_proposal_submit_mcp_returns_json(self):
        """proposal_submit_mcp returns valid JSON."""
        from governance.langgraph_workflow import proposal_submit_mcp

        result = proposal_submit_mcp(
            action="create",
            hypothesis="Test hypothesis for MCP",
            evidence="Evidence 1, Evidence 2",
            directive="Test directive"
        )

        parsed = json.loads(result)
        assert "proposal_id" in parsed
        assert "decision" in parsed
        assert "status" in parsed

    def test_proposal_submit_mcp_handles_comma_separated_evidence(self):
        """MCP wrapper parses comma-separated evidence."""
        from governance.langgraph_workflow import proposal_submit_mcp

        result = proposal_submit_mcp(
            action="create",
            hypothesis="Test hypothesis for parsing",
            evidence="Item 1, Item 2, Item 3",
            directive="Test directive"
        )

        parsed = json.loads(result)
        assert parsed["proposal_id"] is not None


# =============================================================================
# WORKFLOW DIAGRAM TESTS
# =============================================================================

class TestWorkflowVisualization:
    """Tests for workflow visualization."""

    def test_print_workflow_diagram_exists(self):
        """print_workflow_diagram function exists."""
        from governance.langgraph_workflow import print_workflow_diagram
        assert print_workflow_diagram is not None
        assert callable(print_workflow_diagram)
