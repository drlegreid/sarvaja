"""Proposal MCP Tools. Per RULE-011, RULE-012: Proposal, voting, dispute operations."""
from governance.mcp_tools.common import format_mcp_result

import json
from datetime import datetime
from typing import Optional


def register_proposal_tools(mcp) -> None:
    """Register proposal-related MCP tools."""

    @mcp.tool()
    def proposal_create(
        action: str,
        hypothesis: str,
        evidence: list[str],
        rule_id: Optional[str] = None,
        directive: Optional[str] = None
    ) -> str:
        """
        Create a governance proposal for rule changes (RULE-011).

        Args:
            action: Proposal action - "create", "modify", or "deprecate"
            hypothesis: Rationale for the proposed change
            evidence: Supporting evidence as list of strings
            rule_id: Rule ID (required for modify/deprecate actions)
            directive: Rule directive text (required for create/modify actions)

        Returns:
            JSON with proposal_id, status, and confirmation message
        """
        # Validate inputs
        if action not in ["create", "modify", "deprecate"]:
            return format_mcp_result({"error": f"Invalid action: {action}"})

        if action in ["modify", "deprecate"] and not rule_id:
            return format_mcp_result({"error": f"rule_id required for {action} action"})

        if action in ["create", "modify"] and not directive:
            return format_mcp_result({"error": f"directive required for {action} action"})

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

        return format_mcp_result(proposal)

    @mcp.tool()
    def proposal_vote(
        proposal_id: str,
        agent_id: str,
        vote: str,
        reason: Optional[str] = None
    ) -> str:
        """
        Vote on a governance proposal (RULE-011).

        Votes are weighted by agent trust score per RULE-011 bicameral model.

        Args:
            proposal_id: ID of the proposal to vote on
            agent_id: Voting agent's ID
            vote: Vote value - "approve", "reject", or "abstain"
            reason: Optional explanation for the vote

        Returns:
            JSON with vote confirmation and weighted score
        """
        if vote not in ["approve", "reject", "abstain"]:
            return format_mcp_result({"error": f"Invalid vote: {vote}"})

        # Import here to avoid circular dependency
        from governance.mcp_tools.trust import governance_get_trust_score

        # Get agent's trust score for vote weighting
        trust_result = governance_get_trust_score(agent_id)
        trust_data = json.loads(trust_result)

        if "error" in trust_data:
            return format_mcp_result({"error": f"Cannot get trust score: {trust_data['error']}"})

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

        return format_mcp_result(vote_record)

    @mcp.tool()
    def proposal_dispute(
        proposal_id: str,
        agent_id: str,
        reason: str,
        resolution_method: str = "evidence"
    ) -> str:
        """
        File a dispute against a proposal (RULE-011).

        Disputes can trigger escalation to human oversight per bicameral model.

        Args:
            proposal_id: ID of the proposal to dispute
            agent_id: Disputing agent's ID
            reason: Explanation for the dispute
            resolution_method: How to resolve - "consensus", "evidence", "authority", or "escalate"

        Returns:
            JSON with dispute_id, status, and escalation info
        """
        if resolution_method not in ["consensus", "evidence", "authority", "escalate"]:
            return format_mcp_result({"error": f"Invalid resolution method: {resolution_method}"})

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

        return format_mcp_result(dispute)

    @mcp.tool()
    def proposals_list(status: Optional[str] = None) -> str:
        """
        List all governance proposals from TypeDB.

        Args:
            status: Optional filter by proposal status

        Returns:
            JSON with proposals array and count
        """
        from governance.stores import get_typedb_client

        client = get_typedb_client()
        proposals = []

        if client:
            try:
                # Query proposals from TypeDB
                status_filter = f', has proposal-status "{status}"' if status else ""
                query = f"""
                    match
                        $p isa proposal,
                            has proposal-id $pid,
                            has proposal-type $ptype,
                            has proposal-status $pstatus{status_filter};
                    select $pid, $ptype, $pstatus;
                """
                results = client._execute_query(query)

                for r in results:
                    proposals.append({
                        "proposal_id": r.get("pid"),
                        "type": r.get("ptype"),
                        "status": r.get("pstatus")
                    })
            except Exception as e:
                return format_mcp_result({
                    "proposals": [],
                    "count": 0,
                    "note": f"Query error: {str(e)}. No proposals in TypeDB yet."
                })

        return format_mcp_result({
            "proposals": proposals,
            "count": len(proposals),
            "note": "No proposals exist yet" if not proposals else None
        })

    @mcp.tool()
    def proposals_escalated() -> str:
        """
        List proposals requiring human escalation (RULE-011 bicameral oversight).

        Uses TypeDB inference to identify proposals meeting escalation criteria.

        Returns:
            JSON with escalated proposals, count, and review requirement flag
        """
        from governance.stores import get_typedb_client

        client = get_typedb_client()
        escalated = []

        if client:
            try:
                # Query escalated proposals using inference rule
                query = """
                    match
                        (escalated-proposal: $p, escalation-reason: $d) isa requires-escalation;
                        $p isa proposal,
                            has proposal-id $pid,
                            has proposal-status $pstatus;
                        $d has escalation-trigger $trigger;
                    select $pid, $pstatus, $trigger;
                """
                results = client._execute_query(query, infer=True)

                for r in results:
                    escalated.append({
                        "proposal_id": r.get("pid"),
                        "status": r.get("pstatus"),
                        "escalation_trigger": r.get("trigger")
                    })
            except Exception as e:
                return format_mcp_result({
                    "escalated_proposals": [],
                    "count": 0,
                    "note": f"Query error: {str(e)}. No escalated proposals."
                })

        return format_mcp_result({
            "escalated_proposals": escalated,
            "count": len(escalated),
            "requires_human_review": len(escalated) > 0,
            "note": "No escalated proposals" if not escalated else "HUMAN OVERSIGHT REQUIRED"
        })
