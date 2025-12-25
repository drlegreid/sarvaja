"""
Proposal MCP Tools
==================
Proposal, voting, and dispute operations (RULE-011).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Proposal entity module
"""

import json
from datetime import datetime
from typing import Optional


def register_proposal_tools(mcp) -> None:
    """Register proposal-related MCP tools."""

    @mcp.tool()
    def governance_propose_rule(
        action: str,
        hypothesis: str,
        evidence: list[str],
        rule_id: Optional[str] = None,
        directive: Optional[str] = None
    ) -> str:
        """
        Propose a new rule or modification (RULE-011).

        Args:
            action: "create", "modify", or "deprecate"
            hypothesis: Why this change is needed
            evidence: List of evidence items supporting the proposal
            rule_id: Required for modify/deprecate actions
            directive: Required for create/modify actions

        Returns:
            JSON object with proposal ID and status
        """
        # Validate inputs
        if action not in ["create", "modify", "deprecate"]:
            return json.dumps({"error": f"Invalid action: {action}"})

        if action in ["modify", "deprecate"] and not rule_id:
            return json.dumps({"error": f"rule_id required for {action} action"})

        if action in ["create", "modify"] and not directive:
            return json.dumps({"error": f"directive required for {action} action"})

        # Generate proposal ID
        proposal_id = f"PROPOSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Note: Full implementation would insert into TypeDB
        proposal = {
            "proposal_id": proposal_id,
            "action": action,
            "hypothesis": hypothesis,
            "evidence": evidence,
            "rule_id": rule_id,
            "directive": directive,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "message": "Proposal created. Awaiting votes from agents."
        }

        return json.dumps(proposal, indent=2)

    @mcp.tool()
    def governance_vote(
        proposal_id: str,
        agent_id: str,
        vote: str,
        reason: Optional[str] = None
    ) -> str:
        """
        Vote on a proposal (RULE-011).

        Args:
            proposal_id: The proposal to vote on
            agent_id: The voting agent's ID
            vote: "approve", "reject", or "abstain"
            reason: Optional reason for the vote

        Returns:
            JSON object with vote confirmation and weighted score
        """
        if vote not in ["approve", "reject", "abstain"]:
            return json.dumps({"error": f"Invalid vote: {vote}"})

        # Import here to avoid circular dependency
        from governance.mcp_tools.trust import governance_get_trust_score

        # Get agent's trust score for vote weighting
        trust_result = governance_get_trust_score(agent_id)
        trust_data = json.loads(trust_result)

        if "error" in trust_data:
            return json.dumps({"error": f"Cannot get trust score: {trust_data['error']}"})

        vote_weight = trust_data["vote_weight"]

        vote_record = {
            "proposal_id": proposal_id,
            "agent_id": agent_id,
            "vote": vote,
            "reason": reason,
            "vote_weight": vote_weight,
            "timestamp": datetime.now().isoformat(),
            "message": f"Vote recorded with weight {vote_weight:.2f}"
        }

        return json.dumps(vote_record, indent=2)

    @mcp.tool()
    def governance_dispute(
        proposal_id: str,
        agent_id: str,
        reason: str,
        resolution_method: str = "evidence"
    ) -> str:
        """
        Dispute a proposal (RULE-011).

        Args:
            proposal_id: The proposal to dispute
            agent_id: The disputing agent's ID
            reason: Why the proposal is disputed
            resolution_method: "consensus", "evidence", "authority", or "escalate"

        Returns:
            JSON object with dispute status
        """
        if resolution_method not in ["consensus", "evidence", "authority", "escalate"]:
            return json.dumps({"error": f"Invalid resolution method: {resolution_method}"})

        dispute = {
            "dispute_id": f"DISPUTE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "proposal_id": proposal_id,
            "agent_id": agent_id,
            "reason": reason,
            "resolution_method": resolution_method,
            "status": "active",
            "escalation_required": resolution_method == "escalate",
            "timestamp": datetime.now().isoformat()
        }

        if resolution_method == "escalate":
            dispute["message"] = "ESCALATION: Human oversight required (RULE-011 bicameral model)"
        else:
            dispute["message"] = f"Dispute filed. Resolution method: {resolution_method}"

        return json.dumps(dispute, indent=2)
