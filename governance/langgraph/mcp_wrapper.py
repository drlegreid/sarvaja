"""
LangGraph MCP Tool Wrapper
==========================
MCP tool interface for governance workflow.

Per RULE-011: Multi-Agent Governance Protocol
Per GAP-FILE-009: Extracted from langgraph_workflow.py

Created: 2024-12-28
"""

import json
from typing import Optional

from .graph import run_proposal_workflow


def proposal_submit_mcp(
    action: str,
    hypothesis: str,
    evidence: str,  # Comma-separated
    submitter_id: str = "AGENT-001",
    rule_id: Optional[str] = None,
    directive: Optional[str] = None,
    dry_run: bool = True
) -> str:
    """
    MCP wrapper for proposal workflow.

    Args:
        action: create, modify, or deprecate
        hypothesis: The proposal hypothesis (min 10 chars)
        evidence: Comma-separated evidence items
        submitter_id: Agent submitting the proposal
        rule_id: Required for modify/deprecate
        directive: Required for create/modify
        dry_run: Whether to run in dry-run mode

    Returns:
        JSON result of workflow execution
    """
    evidence_list = [e.strip() for e in evidence.split(",")]

    result = run_proposal_workflow(
        action=action,
        hypothesis=hypothesis,
        evidence=evidence_list,
        submitter_id=submitter_id,
        rule_id=rule_id,
        directive=directive,
        dry_run=dry_run
    )

    # Convert to JSON-serializable format
    return json.dumps({
        "proposal_id": result["proposal_id"],
        "action": result["action"],
        "decision": result["decision"],
        "status": result["status"],
        "phases_completed": result["phases_completed"],
        "impact_score": result["impact_score"],
        "risk_level": result["risk_level"],
        "votes_for": result["votes_for"],
        "votes_against": result["votes_against"],
        "error_message": result.get("error_message")
    }, indent=2)
