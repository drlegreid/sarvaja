"""
Unit tests for Proposal MCP Tools.

Per GOV-BICAM-01-v1: Tests for proposal_create, proposal_vote,
proposal_dispute validation logic.
Tests focus on input validation and output structure (not MCP registration).
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from governance.mcp_tools.proposals import register_proposal_tools


def _json_format(data, **kw):
    """Test helper: force JSON output instead of TOON."""
    return json.dumps(data, default=str)


class _CaptureMCP:
    """Captures tools registered via @mcp.tool()."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _force_json_output():
    """Force JSON output for all proposal tests (TOON format not JSON-parseable)."""
    with patch("governance.mcp_tools.proposals.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture
def mcp_tools():
    """Register and return all proposal MCP tools."""
    mcp = _CaptureMCP()
    register_proposal_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# proposal_create
# ---------------------------------------------------------------------------
class TestProposalCreate:
    """Tests for proposal_create() tool."""

    def test_valid_create(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="create", hypothesis="Need new rule",
            evidence=["ev1.md"], directive="All tests must pass",
        ))
        assert result["status"] == "pending"
        assert result["proposal_id"].startswith("PROPOSAL-")
        assert result["action"] == "create"
        assert result["hypothesis"] == "Need new rule"
        assert result["directive"] == "All tests must pass"

    def test_valid_modify(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="modify", hypothesis="Update directive",
            evidence=["ev.md"], rule_id="R-1", directive="New text",
        ))
        assert result["action"] == "modify"
        assert result["rule_id"] == "R-1"

    def test_valid_deprecate(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="deprecate", hypothesis="Replaced by R-2",
            evidence=["ev.md"], rule_id="R-1",
        ))
        assert result["action"] == "deprecate"

    def test_invalid_action(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="invalid", hypothesis="test", evidence=[],
        ))
        assert "error" in result
        assert "Invalid action" in result["error"]

    def test_modify_requires_rule_id(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="modify", hypothesis="test", evidence=[], directive="text",
        ))
        assert "error" in result
        assert "rule_id required" in result["error"]

    def test_deprecate_requires_rule_id(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="deprecate", hypothesis="test", evidence=[],
        ))
        assert "error" in result
        assert "rule_id required" in result["error"]

    def test_create_requires_directive(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="create", hypothesis="test", evidence=[],
        ))
        assert "error" in result
        assert "directive required" in result["error"]

    def test_has_created_at(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="create", hypothesis="test",
            evidence=["e"], directive="d",
        ))
        assert "created_at" in result

    def test_evidence_preserved(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_create"](
            action="create", hypothesis="test",
            evidence=["a.md", "b.md"], directive="d",
        ))
        assert result["evidence"] == ["a.md", "b.md"]


# ---------------------------------------------------------------------------
# proposal_vote
# ---------------------------------------------------------------------------
class TestProposalVote:
    """Tests for proposal_vote() tool."""

    def test_invalid_vote(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_vote"](
            proposal_id="P-1", agent_id="agent-1", vote="maybe",
        ))
        assert "error" in result
        assert "Invalid vote" in result["error"]

    def test_valid_approve(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.trust as trust_mod
        mock_fn = MagicMock(return_value=json.dumps({"vote_weight": 0.85}))
        monkeypatch.setattr(trust_mod, "governance_get_trust_score", mock_fn, raising=False)
        result = json.loads(mcp_tools["proposal_vote"](
            proposal_id="P-1", agent_id="agent-1", vote="approve",
        ))
        assert result["vote"] == "approve"
        assert result["vote_weight"] == 0.85
        assert result["proposal_id"] == "P-1"

    def test_valid_reject_with_reason(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.trust as trust_mod
        mock_fn = MagicMock(return_value=json.dumps({"vote_weight": 0.70}))
        monkeypatch.setattr(trust_mod, "governance_get_trust_score", mock_fn, raising=False)
        result = json.loads(mcp_tools["proposal_vote"](
            proposal_id="P-1", agent_id="agent-1", vote="reject",
            reason="Conflicts with R-5",
        ))
        assert result["vote"] == "reject"
        assert result["reason"] == "Conflicts with R-5"

    def test_trust_error(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.trust as trust_mod
        mock_fn = MagicMock(return_value=json.dumps({"error": "Agent not found"}))
        monkeypatch.setattr(trust_mod, "governance_get_trust_score", mock_fn, raising=False)
        result = json.loads(mcp_tools["proposal_vote"](
            proposal_id="P-1", agent_id="unknown", vote="approve",
        ))
        assert "error" in result
        assert "Cannot get trust score" in result["error"]

    def test_abstain(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.trust as trust_mod
        mock_fn = MagicMock(return_value=json.dumps({"vote_weight": 0.50}))
        monkeypatch.setattr(trust_mod, "governance_get_trust_score", mock_fn, raising=False)
        result = json.loads(mcp_tools["proposal_vote"](
            proposal_id="P-2", agent_id="agent-2", vote="abstain",
        ))
        assert result["vote"] == "abstain"


# ---------------------------------------------------------------------------
# proposal_dispute
# ---------------------------------------------------------------------------
class TestProposalDispute:
    """Tests for proposal_dispute() tool."""

    def test_valid_evidence_dispute(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1",
            reason="Evidence insufficient",
        ))
        assert result["status"] == "active"
        assert result["resolution_method"] == "evidence"
        assert result["escalation_required"] is False
        assert result["dispute_id"].startswith("DISPUTE-")

    def test_escalation_dispute(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1",
            reason="Fundamental disagreement", resolution_method="escalate",
        ))
        assert result["escalation_required"] is True
        assert "ESCALATION" in result["message"]
        assert "bicameral" in result["message"]

    def test_consensus_method(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1",
            reason="Minor concern", resolution_method="consensus",
        ))
        assert result["resolution_method"] == "consensus"
        assert result["escalation_required"] is False

    def test_authority_method(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1",
            reason="Override needed", resolution_method="authority",
        ))
        assert result["resolution_method"] == "authority"

    def test_invalid_method(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1",
            reason="test", resolution_method="invalid",
        ))
        assert "error" in result
        assert "Invalid resolution method" in result["error"]

    def test_has_timestamp(self, mcp_tools):
        result = json.loads(mcp_tools["proposal_dispute"](
            proposal_id="P-1", agent_id="agent-1", reason="test",
        ))
        assert "timestamp" in result
