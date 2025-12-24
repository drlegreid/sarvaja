"""
Governance MCP Server - Multi-Agent Conflict Resolution
Implements Governance-as-a-Service (GaaS) pattern from DESIGN-Governance-MCP.md

Created: 2024-12-24 (RULE-011, DECISION-005)
Protocol: MCP (Model Context Protocol)
Backend: TypeDB 2.29.1

Usage:
    python governance/mcp_server.py

Or add to MCP config:
    {
        "governance": {
            "command": "python",
            "args": ["governance/mcp_server.py"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

import os
import json
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, asdict

from mcp.server.fastmcp import FastMCP

# Import TypeDB client
try:
    from governance.client import TypeDBClient
except ImportError:
    # When running as script
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from governance.client import TypeDBClient

# Initialize MCP server
mcp = FastMCP("governance")

# TypeDB configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"


@dataclass
class TrustScore:
    """Agent trust score calculation result."""
    agent_id: str
    agent_name: str
    trust_score: float
    compliance_rate: float
    accuracy_rate: float
    tenure_days: int
    vote_weight: float  # Derived from trust_score


def calculate_vote_weight(trust_score: float) -> float:
    """Calculate vote weight based on trust score (RULE-011)."""
    # Low trust agents (< 0.5) have vote-weight = trust-score
    # High trust agents (>= 0.5) have vote-weight = 1.0
    return 1.0 if trust_score >= 0.5 else trust_score


# =============================================================================
# MCP TOOLS - Query Operations
# =============================================================================

@mcp.tool()
def governance_query_rules(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> str:
    """
    Query rules from the governance database.

    Args:
        category: Filter by category (governance, architecture, testing, etc.)
        status: Filter by status (ACTIVE, DRAFT, DEPRECATED)
        priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

    Returns:
        JSON array of matching rules
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        # Build query based on filters
        if status == "ACTIVE":
            rules = client.get_active_rules()
        else:
            rules = client.get_all_rules()

        # Apply additional filters
        if category:
            rules = [r for r in rules if r.category == category]
        if priority:
            rules = [r for r in rules if r.priority == priority]
        if status and status != "ACTIVE":
            rules = [r for r in rules if r.status == status]

        return json.dumps([asdict(r) for r in rules], default=str, indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_get_rule(rule_id: str) -> str:
    """
    Get a specific rule by ID.

    Args:
        rule_id: The rule ID (e.g., "RULE-001")

    Returns:
        JSON object with rule details or error
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        rule = client.get_rule_by_id(rule_id)
        if rule:
            return json.dumps(asdict(rule), default=str, indent=2)
        else:
            return json.dumps({"error": f"Rule {rule_id} not found"})

    finally:
        client.close()


@mcp.tool()
def governance_get_dependencies(rule_id: str) -> str:
    """
    Get all dependencies for a rule (uses TypeDB inference for transitive deps).

    Args:
        rule_id: The rule ID to get dependencies for

    Returns:
        JSON array of dependency rule IDs
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        deps = client.get_rule_dependencies(rule_id)
        return json.dumps(deps, indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_find_conflicts() -> str:
    """
    Find conflicting rules using TypeDB inference.

    Returns:
        JSON array of conflict pairs with explanations
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        conflicts = client.find_conflicts()
        return json.dumps(conflicts, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Trust Score Operations
# =============================================================================

@mcp.tool()
def governance_get_trust_score(agent_id: str) -> str:
    """
    Get trust score for an agent (RULE-011).

    Trust Formula: (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

    Args:
        agent_id: The agent ID (e.g., "AGENT-001")

    Returns:
        JSON object with trust score details
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        # Query agent data from TypeDB
        query = f'''
            match
                $a isa agent, has agent-id "{agent_id}";
                $a has agent-name $name;
                $a has trust-score $trust;
                $a has compliance-rate $compliance;
                $a has accuracy-rate $accuracy;
                $a has tenure-days $tenure;
            get $name, $trust, $compliance, $accuracy, $tenure;
        '''

        results = client.execute_query(query)

        if not results:
            return json.dumps({"error": f"Agent {agent_id} not found"})

        result = results[0]
        trust_score = result.get('trust', 0.0)

        score = TrustScore(
            agent_id=agent_id,
            agent_name=result.get('name', 'Unknown'),
            trust_score=trust_score,
            compliance_rate=result.get('compliance', 0.0),
            accuracy_rate=result.get('accuracy', 0.0),
            tenure_days=result.get('tenure', 0),
            vote_weight=calculate_vote_weight(trust_score)
        )

        return json.dumps(asdict(score), indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_list_agents() -> str:
    """
    List all registered agents with their trust scores.

    Returns:
        JSON array of agents with trust information
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        query = '''
            match
                $a isa agent;
                $a has agent-id $id;
                $a has agent-name $name;
                $a has agent-type $type;
                $a has trust-score $trust;
            get $id, $name, $type, $trust;
        '''

        results = client.execute_query(query)

        agents = []
        for r in results:
            agents.append({
                "agent_id": r.get('id'),
                "agent_name": r.get('name'),
                "agent_type": r.get('type'),
                "trust_score": r.get('trust'),
                "vote_weight": calculate_vote_weight(r.get('trust', 0.0))
            })

        return json.dumps(agents, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Proposal Operations
# =============================================================================

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
    # For now, return the proposal structure
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


# =============================================================================
# MCP TOOLS - Decision Impact
# =============================================================================

@mcp.tool()
def governance_get_decision_impacts(decision_id: str) -> str:
    """
    Get all rules affected by a decision (uses TypeDB inference).

    Args:
        decision_id: The decision ID (e.g., "DECISION-003")

    Returns:
        JSON array of affected rule IDs
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        impacts = client.get_decision_impacts(decision_id)
        return json.dumps(impacts, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Health Check
# =============================================================================

@mcp.tool()
def governance_health() -> str:
    """
    Check governance system health.

    Returns:
        JSON object with health status and statistics
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        connected = client.connect()

        if not connected:
            return json.dumps({
                "status": "unhealthy",
                "typedb_connected": False,
                "error": "Cannot connect to TypeDB"
            })

        # Get counts
        rules = client.get_all_rules()

        return json.dumps({
            "status": "healthy",
            "typedb_connected": True,
            "typedb_host": f"{TYPEDB_HOST}:{TYPEDB_PORT}",
            "database": DATABASE_NAME,
            "statistics": {
                "rules_count": len(rules),
                "active_rules": len([r for r in rules if r.status == "ACTIVE"])
            },
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    finally:
        client.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Starting Governance MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    mcp.run()
