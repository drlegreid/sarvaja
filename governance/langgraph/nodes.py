"""
LangGraph Workflow Nodes
========================
Node functions for governance proposal workflow.

Per RULE-011: Multi-Agent Governance Protocol
Per GAP-FILE-009: Extracted from langgraph_workflow.py

Nodes:
- submit_node: Submit proposal and validate submitter
- validate_node: Validate proposal format and dependencies
- assess_node: Assess impact on existing rules
- vote_node: Collect votes from agents
- decide_node: Make final decision based on votes
- implement_node: Implement approved changes
- complete_node: Complete workflow and generate evidence
- reject_node: Handle rejected proposal

Created: 2024-12-28
"""

from datetime import datetime
from typing import List

from .state import (
    ProposalState,
    Vote,
    QUORUM_THRESHOLD,
    APPROVAL_THRESHOLD,
)


def submit_node(state: ProposalState) -> dict:
    """Submit proposal and validate submitter."""
    print("\n" + "="*60)
    print("📝 PHASE 1: SUBMIT")
    print("="*60)

    # Generate proposal ID if not set
    proposal_id = state.get("proposal_id") or f"PROP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"Proposal ID: {proposal_id}")
    print(f"Action: {state['action']}")
    print(f"Submitter: {state['submitter_id']}")
    print(f"Trust Score: {state['submitter_trust_score']:.2f}")

    # Validate submitter has sufficient trust
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
    print("\n" + "="*60)
    print("🔍 PHASE 2: VALIDATE")
    print("="*60)

    errors = []

    # Check required fields
    if not state.get("hypothesis"):
        errors.append("Hypothesis is required")
    elif len(state["hypothesis"]) < 10:
        errors.append("Hypothesis must be at least 10 characters")

    if not state.get("evidence") or len(state["evidence"]) < 1:
        errors.append("At least one evidence item is required")

    # Action-specific validation
    if state["action"] in ["modify", "deprecate"]:
        if not state.get("rule_id"):
            errors.append(f"rule_id is required for {state['action']} action")

    if state["action"] in ["create", "modify"]:
        if not state.get("directive"):
            errors.append(f"directive is required for {state['action']} action")

    if state["dry_run"]:
        print("[DRY-RUN] Validation checks performed")

    validation_passed = len(errors) == 0

    print(f"Validation: {'PASSED' if validation_passed else 'FAILED'}")
    for error in errors:
        print(f"  ❌ {error}")

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
    print("\n" + "="*60)
    print("📊 PHASE 3: ASSESS IMPACT")
    print("="*60)

    # Simulated impact assessment (would integrate with rule_quality.py)
    affected_rules = []
    impact_score = 25.0
    risk_level = "LOW"
    recommendations = []

    if state["action"] == "deprecate":
        # Deprecating has higher impact
        impact_score = 60.0
        risk_level = "MEDIUM"
        affected_rules = ["RULE-001"]  # Simulated
        recommendations.append("Review dependent rules before deprecation")
    elif state["action"] == "modify":
        impact_score = 40.0
        risk_level = "MEDIUM"
        recommendations.append("Run integration tests after modification")
    else:  # create
        impact_score = 20.0
        risk_level = "LOW"
        recommendations.append("Document new rule in RULES-DIRECTIVES.md")

    if state["dry_run"]:
        print("[DRY-RUN] Impact assessment simulated")

    print(f"Impact Score: {impact_score}")
    print(f"Risk Level: {risk_level}")
    print(f"Affected Rules: {affected_rules or 'None'}")

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
    print("\n" + "="*60)
    print("🗳️ PHASE 4: VOTE")
    print("="*60)

    # Simulated voting (would integrate with real agent registry)
    votes: List[Vote] = []

    if state["dry_run"]:
        # Simulate votes in dry-run
        votes = [
            {
                "agent_id": "AGENT-001",
                "vote": "approve",
                "weight": 0.85,
                "reasoning": "Aligns with project goals",
                "timestamp": datetime.now().isoformat()
            },
            {
                "agent_id": "AGENT-002",
                "vote": "approve",
                "weight": 0.72,
                "reasoning": "Evidence is compelling",
                "timestamp": datetime.now().isoformat()
            },
            {
                "agent_id": "AGENT-003",
                "vote": "abstain",
                "weight": 0.65,
                "reasoning": "Need more information",
                "timestamp": datetime.now().isoformat()
            }
        ]
        print("[DRY-RUN] Simulated voting with 3 agents")
    else:
        # In production, would query agent registry
        votes = state.get("votes", [])

    # Calculate weighted totals (RULE-011 formula)
    votes_for = sum(v["weight"] for v in votes if v["vote"] == "approve")
    votes_against = sum(v["weight"] for v in votes if v["vote"] == "reject")
    total_weight = sum(v["weight"] for v in votes)

    # Check quorum (50% participation)
    eligible_agents = 5  # Simulated total eligible agents
    quorum_reached = len(votes) >= (eligible_agents * QUORUM_THRESHOLD)

    # Check approval threshold (67% of votes)
    if total_weight > 0:
        approval_rate = votes_for / total_weight
        threshold_met = approval_rate >= APPROVAL_THRESHOLD
    else:
        approval_rate = 0
        threshold_met = False

    print(f"Votes For: {votes_for:.2f}")
    print(f"Votes Against: {votes_against:.2f}")
    print(f"Approval Rate: {approval_rate:.1%}")
    print(f"Quorum Reached: {quorum_reached}")
    print(f"Threshold Met: {threshold_met}")

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
    print("\n" + "="*60)
    print("⚖️ PHASE 5: DECIDE")
    print("="*60)

    decision = "pending"
    reasoning = ""

    if not state["quorum_reached"]:
        decision = "rejected"
        reasoning = f"Quorum not reached (need {QUORUM_THRESHOLD:.0%} participation)"
    elif state["threshold_met"]:
        decision = "approved"
        reasoning = f"Approval threshold met ({APPROVAL_THRESHOLD:.0%} required)"
    else:
        decision = "rejected"
        reasoning = f"Approval threshold not met ({APPROVAL_THRESHOLD:.0%} required)"

    print(f"Decision: {decision.upper()}")
    print(f"Reasoning: {reasoning}")

    return {
        "current_phase": "decided",
        "phases_completed": state["phases_completed"] + ["decide"],
        "decision": decision,
        "decision_reasoning": reasoning
    }


def implement_node(state: ProposalState) -> dict:
    """Implement approved changes."""
    print("\n" + "="*60)
    print("🔧 PHASE 6: IMPLEMENT")
    print("="*60)

    if state["decision"] != "approved":
        print("Skipping implementation (proposal not approved)")
        return {
            "current_phase": "skipped_implement",
            "phases_completed": state["phases_completed"] + ["implement"],
            "changes_applied": []
        }

    changes = []

    if state["dry_run"]:
        print("[DRY-RUN] Would apply changes:")
        print(f"  - Action: {state['action']}")
        if state.get("rule_id"):
            print(f"  - Rule: {state['rule_id']}")
        if state.get("directive"):
            print(f"  - Directive: {state['directive'][:50]}...")
        changes = [f"[DRY-RUN] {state['action']} operation"]
    else:
        # Real implementation would update TypeDB
        changes = [f"Applied {state['action']} to {state.get('rule_id', 'new rule')}"]

    print(f"Changes Applied: {len(changes)}")

    return {
        "current_phase": "implemented",
        "phases_completed": state["phases_completed"] + ["implement"],
        "changes_applied": changes,
        "rollback_available": True
    }


def complete_node(state: ProposalState) -> dict:
    """Complete workflow and generate evidence."""
    print("\n" + "="*60)
    print("✅ PHASE 7: COMPLETE")
    print("="*60)

    final_status = "success" if state["decision"] == "approved" else "failed"
    if state.get("error_message"):
        final_status = "failed"

    print(f"\n📋 Proposal Summary:")
    print(f"   ID: {state['proposal_id']}")
    print(f"   Action: {state['action']}")
    print(f"   Decision: {state['decision']}")
    print(f"   Phases: {' → '.join(state['phases_completed'])}")
    print(f"   Status: {final_status}")

    if state["dry_run"]:
        print("\n🧪 DRY-RUN MODE - No actual changes were made")

    return {
        "current_phase": "complete",
        "status": final_status,
        "completed_at": datetime.now().isoformat()
    }


def reject_node(state: ProposalState) -> dict:
    """Handle rejected proposal."""
    print("\n" + "="*60)
    print("❌ REJECTED")
    print("="*60)

    print(f"Reason: {state.get('error_message') or state.get('decision_reasoning') or 'Unknown'}")

    return {
        "current_phase": "rejected",
        "phases_completed": state["phases_completed"] + ["reject"],
        "status": "failed"
    }
