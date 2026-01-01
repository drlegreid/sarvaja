"""
Trust Dashboard State (P9.5 - RULE-011)
=======================================
State transforms and helpers for Agent Trust Dashboard.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

from .constants import TRUST_LEVEL_COLORS, PROPOSAL_STATUS_COLORS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_agents(state: Dict[str, Any], agents: List[Dict]) -> Dict[str, Any]:
    """Return new state with agents and leaderboard."""
    from agent.governance_ui.data_access import build_trust_leaderboard
    return {
        **state,
        'agents': agents,
        'trust_leaderboard': build_trust_leaderboard(agents),
    }


def with_selected_agent(state: Dict[str, Any], agent: Optional[Dict]) -> Dict[str, Any]:
    """Return new state with selected agent."""
    return {
        **state,
        'selected_agent': agent,
        'show_agent_detail': agent is not None,
    }


def with_proposals(state: Dict[str, Any], proposals: List[Dict]) -> Dict[str, Any]:
    """Return new state with proposals."""
    return {**state, 'proposals': proposals}


def with_escalated_proposals(state: Dict[str, Any], escalated: List[Dict]) -> Dict[str, Any]:
    """Return new state with escalated proposals."""
    return {**state, 'escalated_proposals': escalated}


def with_governance_stats(state: Dict[str, Any], stats: Dict) -> Dict[str, Any]:
    """Return new state with governance stats."""
    return {**state, 'governance_stats': stats}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_trust_level(score: float) -> str:
    """Get trust level category from score (pure function)."""
    if score >= 0.8:
        return 'HIGH'
    elif score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def get_trust_level_color(level: str) -> str:
    """Get color for trust level (pure function)."""
    return TRUST_LEVEL_COLORS.get(level, 'grey')


def get_proposal_status_color(status: str) -> str:
    """Get color for proposal status (pure function)."""
    return PROPOSAL_STATUS_COLORS.get(status, 'grey')


def format_agent_card(agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format agent data for card display.

    Pure function: same input -> same output.

    Args:
        agent: Agent dict

    Returns:
        Formatted card data
    """
    trust_score = agent.get('trust_score', 0.0)
    trust_level = get_trust_level(trust_score)
    return {
        'agent_id': agent.get('agent_id', 'Unknown'),
        'name': agent.get('name', agent.get('agent_name', 'Unknown')),
        'agent_type': agent.get('agent_type', 'unknown'),
        'trust_score': trust_score,
        'trust_level': trust_level,
        'trust_color': get_trust_level_color(trust_level),
        'compliance_rate': agent.get('compliance_rate', 0.0),
        'accuracy_rate': agent.get('accuracy_rate', 0.0),
        'tenure_days': agent.get('tenure_days', 0),
    }


def format_proposal_card(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format proposal data for card display.

    Pure function: same input -> same output.

    Args:
        proposal: Proposal dict

    Returns:
        Formatted card data
    """
    status = proposal.get('proposal_status', 'pending')
    return {
        'proposal_id': proposal.get('proposal_id', 'Unknown'),
        'proposal_type': proposal.get('proposal_type', 'unknown'),
        'status': status,
        'status_color': get_proposal_status_color(status),
        'proposer_id': proposal.get('proposer_id', 'Unknown'),
        'affected_rule': proposal.get('affected_rule', ''),
        'evidence': proposal.get('evidence', ''),
    }
