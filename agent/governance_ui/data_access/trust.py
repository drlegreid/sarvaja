"""
Agent Trust Dashboard Functions (GAP-FILE-006)
===============================================
Agent trust dashboard for P9.5 - RULE-011.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py
Per DOC-SIZE-01-v1: Calculations in trust_calculations.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

# Re-export for backward compatibility
from agent.governance_ui.data_access.trust_calculations import (  # noqa: F401
    TRUST_WEIGHTS,
    MAX_TENURE_DAYS,
    calculate_trust_score,
    build_trust_leaderboard,
    calculate_consensus_score,
    get_governance_stats,
)


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
