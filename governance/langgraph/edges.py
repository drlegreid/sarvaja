"""
LangGraph Conditional Edges
===========================
Router functions for workflow conditional edges.

Per RULE-011: Multi-Agent Governance Protocol
Per GAP-FILE-009: Extracted from langgraph_workflow.py

Created: 2024-12-28
"""

from .state import ProposalState


def check_validation(state: ProposalState) -> str:
    """Route based on validation result."""
    if state["validation_passed"]:
        return "assess"
    return "reject"


def check_decision(state: ProposalState) -> str:
    """Route based on decision."""
    if state["decision"] == "approved":
        return "implement"
    return "reject"


def check_status(state: ProposalState) -> str:
    """Route based on current status."""
    if state.get("status") == "failed":
        return "reject"
    return "continue"
