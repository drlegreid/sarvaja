"""
TypeDB Proposal Queries.

Per GOV-BICAM-01-v1: Proposal, voting, dispute operations.
Per BUG-1: Missing list_proposals/get_escalated_proposals on TypeDBClient.

In-memory primary with TypeDB best-effort (no proposal schema yet).
Created: 2026-02-21
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_proposals_store():
    """Lazy import to avoid circular dependency (client ↔ stores)."""
    from governance.stores.data_stores import _proposals_store
    return _proposals_store


def _get_votes_store():
    """Lazy import to avoid circular dependency (client ↔ stores)."""
    from governance.stores.data_stores import _proposal_votes_store
    return _proposal_votes_store


class ProposalQueries:
    """
    Proposal query operations for TypeDBClient.

    Uses mixin pattern. In-memory store is primary since TypeDB
    has no proposal entity schema yet. Methods match the interface
    expected by agent/governance_ui/data_access/trust.py.
    """

    def list_proposals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all proposals, optionally filtered by status."""
        proposals = list(_get_proposals_store().values())
        if status:
            proposals = [p for p in proposals if p.get("status") == status]
        return proposals

    def get_escalated_proposals(self) -> List[Dict[str, Any]]:
        """Get proposals requiring human escalation."""
        return [
            p for p in _get_proposals_store().values()
            if p.get("escalation_required")
        ]

    def get_proposal_votes(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get votes for a specific proposal."""
        return _get_votes_store().get(proposal_id, [])

    def store_proposal(self, proposal_id: str, data: Dict[str, Any]) -> bool:
        """Store a proposal in the in-memory store."""
        _get_proposals_store()[proposal_id] = {**data, "proposal_id": proposal_id}
        return True

    def store_proposal_vote(self, proposal_id: str, vote: Dict[str, Any]) -> bool:
        """Store a vote for a proposal."""
        store = _get_votes_store()
        if proposal_id not in store:
            store[proposal_id] = []
        store[proposal_id].append(vote)
        return True
