"""
Unit tests for Proposal MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/proposals.py module.
Tests: proposal_create, proposal_vote, proposal_dispute,
       proposals_list, proposals_escalated.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

_P = "governance.mcp_tools.proposals"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register(**overrides):
    mcp = _CaptureMCP()
    with patch(f"{_P}.MONITORING_AVAILABLE", overrides.get("monitoring", False)):
        from governance.mcp_tools.proposals import register_proposal_tools
        register_proposal_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x)):
        yield


# ── proposal_create ──────────────────────────────────────────────


class TestProposalCreate:
    def test_create_success(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="create", hypothesis="New rule needed",
            evidence=["ev1"], directive="Do X",
        ))
        assert result["status"] == "pending"
        assert result["proposal_id"].startswith("PROPOSAL-")
        assert result["action"] == "create"

    def test_modify_success(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="modify", hypothesis="Change rule",
            evidence=["ev1"], rule_id="RULE-001", directive="Do Y",
        ))
        assert result["rule_id"] == "RULE-001"
        assert result["directive"] == "Do Y"

    def test_deprecate_success(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="deprecate", hypothesis="Remove rule",
            evidence=["ev1"], rule_id="RULE-002",
        ))
        assert result["action"] == "deprecate"

    def test_invalid_action(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="invalid", hypothesis="X", evidence=[],
        ))
        assert "error" in result
        assert "Invalid action" in result["error"]

    def test_modify_requires_rule_id(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="modify", hypothesis="X", evidence=[], directive="D",
        ))
        assert "error" in result
        assert "rule_id required" in result["error"]

    def test_deprecate_requires_rule_id(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="deprecate", hypothesis="X", evidence=[],
        ))
        assert "error" in result
        assert "rule_id required" in result["error"]

    def test_create_requires_directive(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="create", hypothesis="X", evidence=[],
        ))
        assert "error" in result
        assert "directive required" in result["error"]

    def test_modify_requires_directive(self):
        tools = _register()
        result = json.loads(tools["proposal_create"](
            action="modify", hypothesis="X", evidence=[],
            rule_id="R-1",
        ))
        assert "error" in result
        assert "directive required" in result["error"]

    def test_monitoring_called(self):
        with patch(f"{_P}.log_monitor_event", create=True) as mock_log:
            tools = _register(monitoring=True)
            with patch(f"{_P}.MONITORING_AVAILABLE", True):
                tools["proposal_create"](
                    action="create", hypothesis="X",
                    evidence=[], directive="D",
                )
            mock_log.assert_called_once()


# ── proposal_vote ────────────────────────────────────────────────


class TestProposalVote:
    def test_success(self):
        tools = _register()
        trust_json = json.dumps({"vote_weight": 0.85, "trust_score": 0.9})
        # governance_get_trust_score is a nested function; use create=True
        with patch("governance.mcp_tools.trust.governance_get_trust_score",
                    create=True, return_value=trust_json):
            result = json.loads(tools["proposal_vote"](
                proposal_id="P-1", agent_id="code-agent", vote="approve",
            ))
        assert result["vote"] == "approve"
        assert result["vote_weight"] == 0.85

    def test_reject_vote(self):
        tools = _register()
        trust_json = json.dumps({"vote_weight": 0.5})
        with patch("governance.mcp_tools.trust.governance_get_trust_score",
                    create=True, return_value=trust_json):
            result = json.loads(tools["proposal_vote"](
                proposal_id="P-1", agent_id="agent-2", vote="reject",
                reason="Disagree",
            ))
        assert result["vote"] == "reject"
        assert result["reason"] == "Disagree"

    def test_invalid_vote(self):
        tools = _register()
        result = json.loads(tools["proposal_vote"](
            proposal_id="P-1", agent_id="a", vote="maybe",
        ))
        assert "error" in result
        assert "Invalid vote" in result["error"]

    def test_trust_score_error(self):
        tools = _register()
        trust_json = json.dumps({"error": "Agent not found"})
        with patch("governance.mcp_tools.trust.governance_get_trust_score",
                    create=True, return_value=trust_json):
            result = json.loads(tools["proposal_vote"](
                proposal_id="P-1", agent_id="unknown", vote="approve",
            ))
        assert "error" in result
        assert "Cannot get trust score" in result["error"]


# ── proposal_dispute ─────────────────────────────────────────────


class TestProposalDispute:
    def test_evidence_method(self):
        tools = _register()
        result = json.loads(tools["proposal_dispute"](
            proposal_id="P-1", agent_id="a1", reason="Wrong",
        ))
        assert result["resolution_method"] == "evidence"
        assert result["escalation_required"] is False
        assert result["dispute_id"].startswith("DISPUTE-")

    def test_escalate_method(self):
        tools = _register()
        result = json.loads(tools["proposal_dispute"](
            proposal_id="P-1", agent_id="a1", reason="Critical",
            resolution_method="escalate",
        ))
        assert result["escalation_required"] is True
        assert "ESCALATION" in result["message"]

    def test_consensus_method(self):
        tools = _register()
        result = json.loads(tools["proposal_dispute"](
            proposal_id="P-1", agent_id="a1", reason="Minor",
            resolution_method="consensus",
        ))
        assert result["resolution_method"] == "consensus"
        assert result["escalation_required"] is False

    def test_invalid_method(self):
        tools = _register()
        result = json.loads(tools["proposal_dispute"](
            proposal_id="P-1", agent_id="a1", reason="X",
            resolution_method="invalid",
        ))
        assert "error" in result
        assert "Invalid resolution method" in result["error"]

    def test_monitoring_escalation_critical(self):
        with patch(f"{_P}.log_monitor_event", create=True) as mock_log:
            tools = _register(monitoring=True)
            with patch(f"{_P}.MONITORING_AVAILABLE", True):
                tools["proposal_dispute"](
                    proposal_id="P-1", agent_id="a1", reason="R",
                    resolution_method="escalate",
                )
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args
            assert call_kwargs[1]["severity"] == "CRITICAL" or call_kwargs.kwargs.get("severity") == "CRITICAL"


# ── proposals_list ───────────────────────────────────────────────


class TestProposalsList:
    def test_empty_no_client(self):
        tools = _register()
        with patch("governance.stores.get_typedb_client", return_value=None):
            result = json.loads(tools["proposals_list"]())
        assert result["count"] == 0
        assert result["proposals"] == []

    def test_with_results(self):
        tools = _register()
        mock_client = MagicMock()
        mock_client._execute_query.return_value = [
            {"pid": "P-1", "ptype": "create", "pstatus": "pending"},
            {"pid": "P-2", "ptype": "modify", "pstatus": "approved"},
        ]
        with patch("governance.stores.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["proposals_list"]())
        assert result["count"] == 2

    def test_with_status_filter(self):
        tools = _register()
        mock_client = MagicMock()
        mock_client._execute_query.return_value = [
            {"pid": "P-1", "ptype": "create", "pstatus": "pending"},
        ]
        with patch("governance.stores.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["proposals_list"](status="pending"))
        assert result["count"] == 1

    def test_query_error(self):
        tools = _register()
        mock_client = MagicMock()
        mock_client._execute_query.side_effect = Exception("DB error")
        with patch("governance.stores.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["proposals_list"]())
        assert result["count"] == 0
        assert "Query error" in result["note"]


# ── proposals_escalated ──────────────────────────────────────────


class TestProposalsEscalated:
    def test_empty_no_client(self):
        tools = _register()
        with patch("governance.stores.get_typedb_client", return_value=None):
            result = json.loads(tools["proposals_escalated"]())
        assert result["count"] == 0
        assert result["requires_human_review"] is False

    def test_with_escalated(self):
        tools = _register()
        mock_client = MagicMock()
        mock_client._execute_query.return_value = [
            {"pid": "P-1", "pstatus": "disputed", "trigger": "high-risk"},
        ]
        with patch("governance.stores.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["proposals_escalated"]())
        assert result["count"] == 1
        assert result["requires_human_review"] is True
        assert "HUMAN OVERSIGHT" in result["note"]

    def test_query_error(self):
        tools = _register()
        mock_client = MagicMock()
        mock_client._execute_query.side_effect = Exception("inference error")
        with patch("governance.stores.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["proposals_escalated"]())
        assert result["count"] == 0
        assert "Query error" in result["note"]
