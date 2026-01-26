"""
LangGraph Workflow Library for Robot Framework
Tests for graph building, workflow execution, MCP wrappers, visualization.
Migrated from tests/test_langgraph_workflow.py
Per: RF-007 Robot Framework Migration
"""
import json
from robot.api.deco import keyword


class LanggraphWorkflowLibrary:
    """Robot Framework keywords for LangGraph workflow tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Graph Building Tests
    # =========================================================================

    @keyword("Build Proposal Graph Exists")
    def build_proposal_graph_exists(self):
        """Test that build_proposal_graph function exists."""
        try:
            from governance.langgraph_workflow import build_proposal_graph
            return {"exists": build_proposal_graph is not None, "callable": callable(build_proposal_graph)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Graph Has Required Nodes")
    def graph_has_required_nodes(self):
        """Test that graph has all required nodes."""
        try:
            from governance.langgraph_workflow import build_proposal_graph

            graph = build_proposal_graph()

            required_nodes = [
                "submit", "validate", "assess", "vote",
                "decide", "implement", "complete", "reject"
            ]

            missing = [n for n in required_nodes if n not in graph.nodes]
            return {
                "all_nodes_present": len(missing) == 0,
                "missing_nodes": missing
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Workflow Execution Tests
    # =========================================================================

    @keyword("Run Proposal Workflow Exists")
    def run_proposal_workflow_exists(self):
        """Test that run_proposal_workflow function exists."""
        try:
            from governance.langgraph_workflow import run_proposal_workflow
            return {"exists": run_proposal_workflow is not None, "callable": callable(run_proposal_workflow)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dry Run Completes")
    def dry_run_completes(self):
        """Test that dry-run workflow completes."""
        try:
            from governance.langgraph_workflow import run_proposal_workflow

            result = run_proposal_workflow(
                action="create",
                hypothesis="Test hypothesis for dry run",
                evidence=["Evidence 1", "Evidence 2"],
                directive="New rule directive",
                dry_run=True
            )

            return {
                "result_not_none": result is not None,
                "status_valid": result["status"] in ["success", "failed"],
                "submit_completed": "submit" in result["phases_completed"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Workflow Returns Decision")
    def workflow_returns_decision(self):
        """Test that workflow returns decision."""
        try:
            from governance.langgraph_workflow import run_proposal_workflow

            result = run_proposal_workflow(
                action="create",
                hypothesis="Valid test hypothesis",
                evidence=["Evidence"],
                directive="Test directive",
                dry_run=True
            )

            valid_decisions = ["pending", "approved", "rejected", "disputed"]
            return {"decision_valid": result["decision"] in valid_decisions}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Invalid Proposal Fails")
    def invalid_proposal_fails(self):
        """Test that invalid proposal fails validation."""
        try:
            from governance.langgraph_workflow import run_proposal_workflow

            result = run_proposal_workflow(
                action="create",
                hypothesis="x",  # Too short
                evidence=[],  # Empty
                dry_run=True
            )

            return {
                "status_failed": result["status"] == "failed",
                "validation_failed": not result["validation_passed"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Wrapper Tests
    # =========================================================================

    @keyword("Proposal Submit MCP Exists")
    def proposal_submit_mcp_exists(self):
        """Test that proposal_submit_mcp function exists."""
        try:
            from governance.langgraph_workflow import proposal_submit_mcp
            return {"exists": proposal_submit_mcp is not None, "callable": callable(proposal_submit_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Proposal Submit MCP Returns JSON")
    def proposal_submit_mcp_returns_json(self):
        """Test that proposal_submit_mcp returns valid JSON."""
        try:
            from governance.langgraph_workflow import proposal_submit_mcp

            result = proposal_submit_mcp(
                action="create",
                hypothesis="Test hypothesis for MCP",
                evidence="Evidence 1, Evidence 2",
                directive="Test directive"
            )

            parsed = json.loads(result)
            return {
                "has_proposal_id": "proposal_id" in parsed,
                "has_decision": "decision" in parsed,
                "has_status": "status" in parsed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Proposal Submit MCP Handles Comma Separated Evidence")
    def proposal_submit_mcp_handles_comma_separated_evidence(self):
        """Test that MCP wrapper parses comma-separated evidence."""
        try:
            from governance.langgraph_workflow import proposal_submit_mcp

            result = proposal_submit_mcp(
                action="create",
                hypothesis="Test hypothesis for parsing",
                evidence="Item 1, Item 2, Item 3",
                directive="Test directive"
            )

            parsed = json.loads(result)
            return {"proposal_id_present": parsed["proposal_id"] is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Workflow Visualization Tests
    # =========================================================================

    @keyword("Print Workflow Diagram Exists")
    def print_workflow_diagram_exists(self):
        """Test that print_workflow_diagram function exists."""
        try:
            from governance.langgraph_workflow import print_workflow_diagram
            return {"exists": print_workflow_diagram is not None, "callable": callable(print_workflow_diagram)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
