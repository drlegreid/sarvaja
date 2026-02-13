"""LangGraph Workflow Nodes for governance proposals. Per RULE-011, GAP-FILE-009."""

import logging
from datetime import datetime
from typing import List

from .state import (
    ProposalState,
    Vote,
    QUORUM_THRESHOLD,
    APPROVAL_THRESHOLD,
)

logger = logging.getLogger(__name__)

def submit_node(state: ProposalState) -> dict:
    """Submit proposal and validate submitter."""
    logger.info("PHASE 1: SUBMIT")
    proposal_id = state.get("proposal_id") or f"PROP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logger.info("Proposal: %s | Action: %s | Submitter: %s (trust=%.2f)",
                proposal_id, state['action'], state['submitter_id'], state['submitter_trust_score'])
    if state["submitter_trust_score"] < 0.3:
        return {
            "proposal_id": proposal_id,
            "current_phase": "submit_failed",
            "status": "failed",
            "error_message": "Submitter trust score too low (minimum 0.3 required)"
        }

    return {
        "proposal_id": proposal_id,
        "current_phase": "submitted",
        "phases_completed": ["submit"],
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

def validate_node(state: ProposalState) -> dict:
    """Validate proposal format and dependencies."""
    logger.info("PHASE 2: VALIDATE")
    errors = []
    if not state.get("hypothesis"):
        errors.append("Hypothesis is required")
    elif len(state["hypothesis"]) < 10:
        errors.append("Hypothesis must be at least 10 characters")
    if not state.get("evidence") or len(state["evidence"]) < 1:
        errors.append("At least one evidence item is required")
    if state["action"] in ["modify", "deprecate"] and not state.get("rule_id"):
        errors.append(f"rule_id is required for {state['action']} action")
    if state["action"] in ["create", "modify"] and not state.get("directive"):
        errors.append(f"directive is required for {state['action']} action")

    if state["dry_run"]:
        logger.debug("[DRY-RUN] Validation checks performed")

    validation_passed = len(errors) == 0

    logger.info("Validation: %s", 'PASSED' if validation_passed else 'FAILED')
    for error in errors:
        logger.info("  Validation error: %s", error)

    return {
        "current_phase": "validated" if validation_passed else "validation_failed",
        "phases_completed": state["phases_completed"] + ["validate"],
        "validation_passed": validation_passed,
        "validation_errors": errors,
        "status": "running" if validation_passed else "failed",
        "error_message": "; ".join(errors) if errors else None
    }

def assess_node(state: ProposalState) -> dict:
    """Assess impact on existing rules."""
    logger.info("PHASE 3: ASSESS IMPACT")
    affected_rules, recommendations = [], []
    if state["action"] == "deprecate":
        impact_score, risk_level, affected_rules = 60.0, "MEDIUM", ["RULE-001"]
        recommendations.append("Review dependent rules before deprecation")
    elif state["action"] == "modify":
        impact_score, risk_level = 40.0, "MEDIUM"
        recommendations.append("Run integration tests after modification")
    else:
        impact_score, risk_level = 20.0, "LOW"
        recommendations.append("Document new rule in RULES-DIRECTIVES.md")

    if state["dry_run"]:
        logger.debug("[DRY-RUN] Impact assessment simulated")

    logger.info("Impact Score: %s", impact_score)
    logger.info("Risk Level: %s", risk_level)
    logger.info("Affected Rules: %s", affected_rules or 'None')

    return {
        "current_phase": "assessed",
        "phases_completed": state["phases_completed"] + ["assess"],
        "impact_score": impact_score,
        "risk_level": risk_level,
        "affected_rules": affected_rules,
        "recommendations": recommendations
    }

def vote_node(state: ProposalState) -> dict:
    """Collect votes from agents (RULE-011 weighted voting)."""
    logger.info("PHASE 4: VOTE")
    votes: List[Vote] = []
    ts = datetime.now().isoformat()
    if state["dry_run"]:
        votes = [
            {"agent_id": "AGENT-001", "vote": "approve", "weight": 0.85, "reasoning": "Aligns with project goals", "timestamp": ts},
            {"agent_id": "AGENT-002", "vote": "approve", "weight": 0.72, "reasoning": "Evidence is compelling", "timestamp": ts},
            {"agent_id": "AGENT-003", "vote": "abstain", "weight": 0.65, "reasoning": "Need more information", "timestamp": ts}
        ]
        logger.debug("[DRY-RUN] Simulated voting with 3 agents")
    else:
        votes = state.get("votes", [])
    votes_for = sum(v["weight"] for v in votes if v["vote"] == "approve")
    votes_against = sum(v["weight"] for v in votes if v["vote"] == "reject")
    total_weight = sum(v["weight"] for v in votes)
    quorum_reached = len(votes) >= (5 * QUORUM_THRESHOLD)
    approval_rate = votes_for / total_weight if total_weight > 0 else 0
    threshold_met = approval_rate >= APPROVAL_THRESHOLD
    logger.info("For: %.2f | Against: %.2f | Rate: %.1f%% | Quorum: %s | Met: %s",
                votes_for, votes_against, approval_rate * 100, quorum_reached, threshold_met)

    return {
        "current_phase": "voted",
        "phases_completed": state["phases_completed"] + ["vote"],
        "votes": votes,
        "votes_for": votes_for,
        "votes_against": votes_against,
        "quorum_reached": quorum_reached,
        "threshold_met": threshold_met
    }

def decide_node(state: ProposalState) -> dict:
    """Make final decision based on votes."""
    logger.info("PHASE 5: DECIDE")
    if not state["quorum_reached"]:
        decision, reasoning = "rejected", f"Quorum not reached (need {QUORUM_THRESHOLD:.0%} participation)"
    elif state["threshold_met"]:
        decision, reasoning = "approved", f"Approval threshold met ({APPROVAL_THRESHOLD:.0%} required)"
    else:
        decision, reasoning = "rejected", f"Approval threshold not met ({APPROVAL_THRESHOLD:.0%} required)"
    logger.info("Decision: %s | %s", decision.upper(), reasoning)

    return {
        "current_phase": "decided",
        "phases_completed": state["phases_completed"] + ["decide"],
        "decision": decision,
        "decision_reasoning": reasoning
    }

def implement_node(state: ProposalState) -> dict:
    """Implement approved changes."""
    logger.info("PHASE 6: IMPLEMENT")
    if state["decision"] != "approved":
        logger.info("Skipping implementation (proposal not approved)")
        return {"current_phase": "skipped_implement", "phases_completed": state["phases_completed"] + ["implement"], "changes_applied": []}
    if state["dry_run"]:
        logger.debug("[DRY-RUN] Would: %s on %s", state['action'], state.get('rule_id', 'new rule'))
        changes = [f"[DRY-RUN] {state['action']} operation"]
    else:
        changes = [f"Applied {state['action']} to {state.get('rule_id', 'new rule')}"]
    logger.info("Changes Applied: %d", len(changes))

    return {
        "current_phase": "implemented",
        "phases_completed": state["phases_completed"] + ["implement"],
        "changes_applied": changes,
        "rollback_available": True
    }

def complete_node(state: ProposalState) -> dict:
    """Complete workflow and generate evidence."""
    logger.info("PHASE 7: COMPLETE")
    final_status = "failed" if state.get("error_message") else ("success" if state["decision"] == "approved" else "failed")
    logger.info("Summary: %s | %s | %s | %s | %s",
                state['proposal_id'], state['action'], state['decision'],
                ' -> '.join(state['phases_completed']), final_status)
    if state["dry_run"]:
        logger.info("DRY-RUN MODE - No actual changes were made")
    return {"current_phase": "complete", "status": final_status, "completed_at": datetime.now().isoformat()}

def reject_node(state: ProposalState) -> dict:
    """Handle rejected proposal."""
    logger.info("REJECTED")
    logger.info("Reason: %s", state.get('error_message') or state.get('decision_reasoning') or 'Unknown')
    return {"current_phase": "rejected", "phases_completed": state["phases_completed"] + ["reject"], "status": "failed"}
