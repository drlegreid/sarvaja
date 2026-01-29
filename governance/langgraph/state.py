"""
LangGraph State Schema
======================
State types and constants for governance workflow.

Per GOV-BICAM-01-v1: Multi-Agent Governance Protocol
Per GAP-FILE-009: Extracted from langgraph_workflow.py

Created: 2024-12-28
"""

from typing import TypedDict, Literal, Optional, List


class Vote(TypedDict):
    """Single vote from an agent."""
    agent_id: str
    vote: Literal["approve", "reject", "abstain"]
    weight: float
    reasoning: Optional[str]
    timestamp: str


class ProposalState(TypedDict):
    """State that flows through the governance workflow."""

    # Proposal identity
    proposal_id: str
    action: Literal["create", "modify", "deprecate"]
    rule_id: Optional[str]  # Required for modify/deprecate

    # Content
    hypothesis: str
    evidence: List[str]
    directive: Optional[str]  # New directive for create/modify

    # Submitter
    submitter_id: str
    submitter_trust_score: float

    # Progress tracking
    current_phase: str
    phases_completed: List[str]

    # Validation
    validation_passed: bool
    validation_errors: List[str]

    # Impact assessment
    impact_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    affected_rules: List[str]
    recommendations: List[str]

    # Voting (GOV-BICAM-01-v1)
    votes: List[Vote]
    votes_for: float  # Weighted sum
    votes_against: float
    quorum_reached: bool
    threshold_met: bool

    # Decision
    decision: Literal["pending", "approved", "rejected", "disputed"]
    decision_reasoning: str

    # Execution
    dry_run: bool
    changes_applied: List[str]
    rollback_available: bool

    # Status
    status: Literal["pending", "running", "success", "failed", "cancelled"]
    error_message: Optional[str]

    # Timestamps
    started_at: Optional[str]
    completed_at: Optional[str]


# =============================================================================
# CONSTANTS (GOV-BICAM-01-v1)
# =============================================================================

# Voting thresholds per GOV-BICAM-01-v1
QUORUM_THRESHOLD = 0.5  # 50% of eligible agents must vote
APPROVAL_THRESHOLD = 0.67  # 67% weighted approval required
DISPUTE_THRESHOLD = 0.75  # Disputes require 75% to override

# Trust score formula components (GOV-BICAM-01-v1)
TRUST_WEIGHTS = {
    "compliance": 0.4,
    "accuracy": 0.3,
    "consistency": 0.2,
    "tenure": 0.1
}
