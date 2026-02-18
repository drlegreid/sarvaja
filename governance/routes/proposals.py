"""
Governance Proposal Workflow API.

Per GOV-BICAM-01-v1: Multi-Agent Governance Protocol
Per LangGraph workflow: SUBMIT → VALIDATE → ASSESS → VOTE → DECIDE → IMPLEMENT → COMPLETE

Exposes the LangGraph governance proposal workflow as REST API endpoints.
Created: 2026-01-31
"""

import logging
from datetime import datetime
from typing import Optional, List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from governance.langgraph.graph import run_proposal_workflow, LANGGRAPH_AVAILABLE
from governance.langgraph.state import (
    QUORUM_THRESHOLD, APPROVAL_THRESHOLD, DISPUTE_THRESHOLD,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposals", tags=["proposals"])

# In-memory proposal history (per session, survives until restart)
_proposal_history: list = []


class ProposalRequest(BaseModel):
    """Request body for submitting a governance proposal."""
    action: Literal["create", "modify", "deprecate"]
    hypothesis: str = Field(..., min_length=10)
    evidence: List[str] = Field(..., min_length=1)
    submitter_id: str = "AGENT-001"
    rule_id: Optional[str] = None
    directive: Optional[str] = None
    dry_run: bool = True


class ProposalResponse(BaseModel):
    """Response from proposal workflow execution."""
    proposal_id: str
    action: str
    decision: str
    status: str
    phases_completed: List[str]
    impact_score: float
    risk_level: str
    votes_for: float
    votes_against: float
    quorum_reached: bool
    threshold_met: bool
    decision_reasoning: str
    error_message: Optional[str] = None
    dry_run: bool
    submitted_at: str


@router.post("/submit", response_model=ProposalResponse)
async def submit_proposal(req: ProposalRequest):
    """
    Submit a governance proposal through the LangGraph workflow.

    The proposal goes through: SUBMIT → VALIDATE → ASSESS → VOTE → DECIDE → IMPLEMENT → COMPLETE.
    Use dry_run=true (default) to simulate without applying changes.
    """
    try:
        result = run_proposal_workflow(
            action=req.action,
            hypothesis=req.hypothesis,
            evidence=req.evidence,
            submitter_id=req.submitter_id,
            rule_id=req.rule_id,
            directive=req.directive,
            dry_run=req.dry_run,
        )

        response = ProposalResponse(
            proposal_id=result.get("proposal_id", ""),
            action=result.get("action", req.action),
            decision=result.get("decision", "pending"),
            status=result.get("status", "unknown"),
            phases_completed=result.get("phases_completed", []),
            impact_score=result.get("impact_score", 0.0),
            risk_level=result.get("risk_level", "LOW"),
            votes_for=result.get("votes_for", 0.0),
            votes_against=result.get("votes_against", 0.0),
            quorum_reached=result.get("quorum_reached", False),
            threshold_met=result.get("threshold_met", False),
            decision_reasoning=result.get("decision_reasoning", ""),
            error_message=result.get("error_message"),
            dry_run=req.dry_run,
            submitted_at=datetime.now().isoformat(),
        )

        _proposal_history.append(response.model_dump())
        return response

    except Exception as e:
        # BUG-470-PRP-001: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Proposal workflow failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Proposal workflow failed: {type(e).__name__}")


@router.get("/history")
async def list_proposals(limit: int = 20):
    """List recent proposal submissions (most recent first)."""
    return {
        "items": list(reversed(_proposal_history[-limit:])),
        "total": len(_proposal_history),
    }


@router.get("/workflow-info")
async def get_workflow_info():
    """Get workflow configuration and graph structure."""
    return {
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "phases": [
            {"id": "submit", "name": "Submit", "icon": "mdi-send"},
            {"id": "validate", "name": "Validate", "icon": "mdi-check-decagram"},
            {"id": "assess", "name": "Assess Impact", "icon": "mdi-chart-bar"},
            {"id": "vote", "name": "Vote", "icon": "mdi-vote"},
            {"id": "decide", "name": "Decide", "icon": "mdi-gavel"},
            {"id": "implement", "name": "Implement", "icon": "mdi-cog"},
            {"id": "complete", "name": "Complete", "icon": "mdi-flag-checkered"},
        ],
        "thresholds": {
            "quorum": QUORUM_THRESHOLD,
            "approval": APPROVAL_THRESHOLD,
            "dispute": DISPUTE_THRESHOLD,
        },
        "edges": [
            {"from": "START", "to": "submit"},
            {"from": "submit", "to": "validate", "condition": "status != failed"},
            {"from": "submit", "to": "reject", "condition": "status == failed"},
            {"from": "validate", "to": "assess", "condition": "validation_passed"},
            {"from": "validate", "to": "reject", "condition": "!validation_passed"},
            {"from": "assess", "to": "vote"},
            {"from": "vote", "to": "decide"},
            {"from": "decide", "to": "implement", "condition": "approved"},
            {"from": "decide", "to": "reject", "condition": "rejected"},
            {"from": "implement", "to": "complete"},
            {"from": "reject", "to": "complete"},
            {"from": "complete", "to": "END"},
        ],
    }
