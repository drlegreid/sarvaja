"""
Agent Trust Dashboard Functions (GAP-FILE-006)
===============================================
Agent trust dashboard for P9.5 - RULE-011.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

# Trust score weights per RULE-011
TRUST_WEIGHTS = {
    'compliance': 0.4,
    'accuracy': 0.3,
    'consistency': 0.2,
    'tenure': 0.1,
}

# Max tenure days for normalization
MAX_TENURE_DAYS = 365


def get_agents() -> List[Dict[str, Any]]:
    """
    Get all registered agents.

    Returns:
        List of agent dicts with trust metrics
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        agents = client.list_agents()
        return agents if agents else []
    finally:
        client.close()


def get_agent_trust_score(agent_id: str) -> Optional[float]:
    """
    Get trust score for a specific agent.

    Args:
        agent_id: Agent ID

    Returns:
        Trust score (0.0-1.0) or None if not found
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return None
        trust = client.get_agent_trust(agent_id)
        return trust
    finally:
        client.close()


def calculate_trust_score(
    compliance_rate: float,
    accuracy_rate: float,
    consistency_rate: float,
    tenure_days: int
) -> float:
    """
    Calculate trust score using RULE-011 formula.

    Formula: Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

    Pure function: same inputs -> same output.

    Args:
        compliance_rate: 0.0-1.0 compliance percentage
        accuracy_rate: 0.0-1.0 accuracy percentage
        consistency_rate: 0.0-1.0 consistency percentage
        tenure_days: Days agent has been active

    Returns:
        Trust score 0.0-1.0
    """
    # Normalize tenure to 0-1 scale (365 days = 1.0)
    normalized_tenure = min(tenure_days / MAX_TENURE_DAYS, 1.0)

    # Calculate weighted sum
    trust = (
        (compliance_rate * TRUST_WEIGHTS['compliance']) +
        (accuracy_rate * TRUST_WEIGHTS['accuracy']) +
        (consistency_rate * TRUST_WEIGHTS['consistency']) +
        (normalized_tenure * TRUST_WEIGHTS['tenure'])
    )

    # Clamp to 0.0-1.0
    return max(0.0, min(1.0, trust))


def get_agent_actions(agent_id: str) -> List[Dict[str, Any]]:
    """
    Get action history for an agent.

    Args:
        agent_id: Agent ID

    Returns:
        List of action dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        actions = client.get_agent_actions(agent_id)
        return actions if actions else []
    finally:
        client.close()


def get_proposals(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get governance proposals.

    Args:
        status: Optional filter by status (pending, approved, rejected, disputed)

    Returns:
        List of proposal dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        proposals = client.list_proposals(status=status)
        return proposals if proposals else []
    finally:
        client.close()


def get_proposal_votes(proposal_id: str) -> List[Dict[str, Any]]:
    """
    Get votes for a proposal.

    Args:
        proposal_id: Proposal ID

    Returns:
        List of vote dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        votes = client.get_proposal_votes(proposal_id)
        return votes if votes else []
    finally:
        client.close()


def get_escalated_proposals() -> List[Dict[str, Any]]:
    """
    Get proposals that require human escalation.

    Returns:
        List of escalated proposal dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        escalated = client.get_escalated_proposals()
        return escalated if escalated else []
    finally:
        client.close()


def build_trust_leaderboard(agents: List[Dict]) -> List[Dict[str, Any]]:
    """
    Build trust leaderboard from agents list.

    Pure function: sorts and ranks agents by trust score.

    Args:
        agents: List of agent dicts

    Returns:
        Sorted and ranked leaderboard
    """
    # Sort by trust score descending
    sorted_agents = sorted(
        agents,
        key=lambda a: a.get('trust_score', 0.0),
        reverse=True
    )

    # Add rank and trust level
    leaderboard = []
    for i, agent in enumerate(sorted_agents, start=1):
        trust_score = agent.get('trust_score', 0.0)
        leaderboard.append({
            **agent,
            'rank': i,
            'trust_level': _get_trust_level(trust_score),
        })

    return leaderboard


def _get_trust_level(score: float) -> str:
    """Get trust level category from score."""
    if score >= 0.8:
        return 'HIGH'
    elif score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def calculate_consensus_score(votes: List[Dict]) -> float:
    """
    Calculate consensus score from weighted votes.

    Pure function: computes consensus from vote list.

    Args:
        votes: List of vote dicts with vote_value and vote_weight

    Returns:
        Consensus score 0.0-1.0 (1.0 = unanimous)
    """
    if not votes:
        return 0.0

    total_weight = 0.0
    approve_weight = 0.0
    reject_weight = 0.0

    for vote in votes:
        weight = vote.get('vote_weight', 1.0)
        value = vote.get('vote_value', 'abstain')
        total_weight += weight

        if value == 'approve':
            approve_weight += weight
        elif value == 'reject':
            reject_weight += weight

    if total_weight == 0:
        return 0.0

    # Consensus = majority weight / total weight
    majority_weight = max(approve_weight, reject_weight)
    return majority_weight / total_weight


def get_governance_stats(
    agents: List[Dict],
    proposals: List[Dict]
) -> Dict[str, Any]:
    """
    Calculate governance statistics.

    Pure function: aggregates metrics from agents and proposals.

    Args:
        agents: List of agent dicts
        proposals: List of proposal dicts

    Returns:
        Stats dict with governance metrics
    """
    # Calculate averages
    trust_scores = [a.get('trust_score', 0.0) for a in agents]
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

    # Count proposals by status
    pending = len([p for p in proposals if p.get('proposal_status') == 'pending'])
    approved = len([p for p in proposals if p.get('proposal_status') == 'approved'])
    rejected = len([p for p in proposals if p.get('proposal_status') == 'rejected'])

    total_resolved = approved + rejected
    approval_rate = approved / total_resolved if total_resolved > 0 else 0.0

    return {
        'total_agents': len(agents),
        'avg_trust_score': avg_trust,
        'high_trust_agents': len([a for a in agents if a.get('trust_score', 0) >= 0.8]),
        'low_trust_agents': len([a for a in agents if a.get('trust_score', 0) < 0.5]),
        'total_proposals': len(proposals),
        'pending_proposals': pending,
        'approved_proposals': approved,
        'rejected_proposals': rejected,
        'approval_rate': approval_rate,
    }
