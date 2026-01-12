"""
Proposal Tools
==============
Type-safe proposal creation operations.

Per RULE-011: Multi-Agent Governance Protocol
Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

from datetime import datetime

from ..models import ProposalConfig, ProposalResult


def create_proposal_typed(config: ProposalConfig) -> ProposalResult:
    """
    Create a rule proposal with type-safe configuration.

    Args:
        config: Validated proposal configuration

    Returns:
        Structured proposal result
    """
    proposal_id = f"PROPOSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return ProposalResult(
        success=True,
        proposal_id=proposal_id,
        status="pending",
        action=config.action,
        rule_id=config.rule_id,
        created_at=datetime.now().isoformat(),
        message=f"Proposal {proposal_id} created. Awaiting votes from agents."
    )
