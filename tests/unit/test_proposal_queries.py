"""
Unit tests for ProposalQueries mixin.

Per BUG-1: Validates list_proposals, get_escalated_proposals,
get_proposal_votes methods exist and work correctly.
"""

import pytest
from governance.typedb.queries.proposals import ProposalQueries
from governance.stores.data_stores import _proposals_store, _proposal_votes_store


@pytest.fixture(autouse=True)
def clean_stores():
    """Clear stores before each test."""
    _proposals_store.clear()
    _proposal_votes_store.clear()
    yield
    _proposals_store.clear()
    _proposal_votes_store.clear()


@pytest.fixture
def queries():
    """Create a ProposalQueries instance."""
    return ProposalQueries()


class TestListProposals:
    def test_empty(self, queries):
        assert queries.list_proposals() == []

    def test_returns_all(self, queries):
        queries.store_proposal("P-001", {"status": "pending", "action": "create"})
        queries.store_proposal("P-002", {"status": "approved", "action": "modify"})
        result = queries.list_proposals()
        assert len(result) == 2

    def test_filter_by_status(self, queries):
        queries.store_proposal("P-001", {"status": "pending", "action": "create"})
        queries.store_proposal("P-002", {"status": "approved", "action": "modify"})
        queries.store_proposal("P-003", {"status": "pending", "action": "deprecate"})
        result = queries.list_proposals(status="pending")
        assert len(result) == 2
        assert all(p["status"] == "pending" for p in result)

    def test_filter_no_match(self, queries):
        queries.store_proposal("P-001", {"status": "pending", "action": "create"})
        assert queries.list_proposals(status="rejected") == []


class TestGetEscalatedProposals:
    def test_empty(self, queries):
        assert queries.get_escalated_proposals() == []

    def test_returns_escalated_only(self, queries):
        queries.store_proposal("P-001", {"status": "pending", "escalation_required": True})
        queries.store_proposal("P-002", {"status": "approved", "escalation_required": False})
        queries.store_proposal("P-003", {"status": "disputed", "escalation_required": True})
        result = queries.get_escalated_proposals()
        assert len(result) == 2
        assert all(p["escalation_required"] for p in result)


class TestGetProposalVotes:
    def test_empty(self, queries):
        assert queries.get_proposal_votes("P-001") == []

    def test_returns_votes(self, queries):
        queries.store_proposal_vote("P-001", {"agent_id": "agent-1", "vote": "approve"})
        queries.store_proposal_vote("P-001", {"agent_id": "agent-2", "vote": "reject"})
        result = queries.get_proposal_votes("P-001")
        assert len(result) == 2

    def test_votes_isolated_per_proposal(self, queries):
        queries.store_proposal_vote("P-001", {"agent_id": "agent-1", "vote": "approve"})
        queries.store_proposal_vote("P-002", {"agent_id": "agent-2", "vote": "reject"})
        assert len(queries.get_proposal_votes("P-001")) == 1
        assert len(queries.get_proposal_votes("P-002")) == 1


class TestStoreProposal:
    def test_stores_with_id(self, queries):
        queries.store_proposal("P-001", {"action": "create", "hypothesis": "test"})
        result = queries.list_proposals()
        assert len(result) == 1
        assert result[0]["proposal_id"] == "P-001"
        assert result[0]["action"] == "create"

    def test_overwrite(self, queries):
        queries.store_proposal("P-001", {"status": "pending"})
        queries.store_proposal("P-001", {"status": "approved"})
        result = queries.list_proposals()
        assert len(result) == 1
        assert result[0]["status"] == "approved"


class TestClientIntegration:
    """Verify ProposalQueries is accessible via TypeDBClient."""

    def test_client_has_list_proposals(self):
        from governance.client import TypeDBClient
        assert hasattr(TypeDBClient, "list_proposals")

    def test_client_has_get_escalated_proposals(self):
        from governance.client import TypeDBClient
        assert hasattr(TypeDBClient, "get_escalated_proposals")

    def test_client_has_get_proposal_votes(self):
        from governance.client import TypeDBClient
        assert hasattr(TypeDBClient, "get_proposal_votes")

    def test_client_has_store_proposal(self):
        from governance.client import TypeDBClient
        assert hasattr(TypeDBClient, "store_proposal")
