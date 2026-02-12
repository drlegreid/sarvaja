"""
Unit tests for Trust Dashboard State Transforms.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/trust.py.
Tests: with_agents, with_selected_agent, with_proposals,
       with_escalated_proposals, with_governance_stats,
       get_trust_level, get_trust_level_color, get_proposal_status_color,
       format_agent_card, format_proposal_card.
"""

from unittest.mock import patch

from agent.governance_ui.state.trust import (
    with_agents, with_selected_agent, with_proposals,
    with_escalated_proposals, with_governance_stats,
    get_trust_level, get_trust_level_color, get_proposal_status_color,
    format_agent_card, format_proposal_card,
)


# ── State Transforms ─────────────────────────────────────


class TestWithAgents:
    @patch("agent.governance_ui.data_access.build_trust_leaderboard", return_value=[{"rank": 1}])
    def test_sets_agents_and_leaderboard(self, mock_lb):
        agents = [{"agent_id": "A-1"}]
        result = with_agents({}, agents)
        assert result["agents"] == agents
        assert result["trust_leaderboard"] == [{"rank": 1}]
        mock_lb.assert_called_once_with(agents)


class TestWithSelectedAgent:
    def test_selects_agent(self):
        agent = {"agent_id": "A-1"}
        result = with_selected_agent({}, agent)
        assert result["selected_agent"] == agent
        assert result["show_agent_detail"] is True

    def test_deselects_agent(self):
        result = with_selected_agent({}, None)
        assert result["selected_agent"] is None
        assert result["show_agent_detail"] is False


class TestWithProposals:
    def test_sets_proposals(self):
        proposals = [{"proposal_id": "P-1"}]
        assert with_proposals({}, proposals)["proposals"] == proposals


class TestWithEscalatedProposals:
    def test_sets_escalated(self):
        esc = [{"proposal_id": "P-2"}]
        assert with_escalated_proposals({}, esc)["escalated_proposals"] == esc


class TestWithGovernanceStats:
    def test_sets_stats(self):
        stats = {"total_agents": 5}
        assert with_governance_stats({}, stats)["governance_stats"] == stats


# ── UI Helpers ────────────────────────────────────────────


class TestGetTrustLevel:
    def test_high(self):
        assert get_trust_level(0.9) == "HIGH"
        assert get_trust_level(0.8) == "HIGH"

    def test_medium(self):
        assert get_trust_level(0.7) == "MEDIUM"
        assert get_trust_level(0.5) == "MEDIUM"

    def test_low(self):
        assert get_trust_level(0.4) == "LOW"
        assert get_trust_level(0.0) == "LOW"


class TestGetTrustLevelColor:
    def test_known_levels(self):
        assert get_trust_level_color("HIGH") == "success"
        assert get_trust_level_color("MEDIUM") == "warning"
        assert get_trust_level_color("LOW") == "error"

    def test_unknown_fallback(self):
        assert get_trust_level_color("UNKNOWN") == "grey"


class TestGetProposalStatusColor:
    def test_known_statuses(self):
        assert get_proposal_status_color("pending") == "info"
        assert get_proposal_status_color("approved") == "success"
        assert get_proposal_status_color("rejected") == "error"
        assert get_proposal_status_color("disputed") == "warning"
        assert get_proposal_status_color("escalated") == "purple"

    def test_unknown_fallback(self):
        assert get_proposal_status_color("xyz") == "grey"


# ── Format Functions ──────────────────────────────────────


class TestFormatAgentCard:
    def test_full_agent(self):
        agent = {
            "agent_id": "A-001",
            "name": "Code Agent",
            "agent_type": "code",
            "trust_score": 0.85,
            "compliance_rate": 0.95,
            "accuracy_rate": 0.90,
            "tenure_days": 30,
        }
        result = format_agent_card(agent)
        assert result["agent_id"] == "A-001"
        assert result["name"] == "Code Agent"
        assert result["trust_level"] == "HIGH"
        assert result["trust_color"] == "success"
        assert result["compliance_rate"] == 0.95

    def test_low_trust(self):
        result = format_agent_card({"trust_score": 0.2})
        assert result["trust_level"] == "LOW"
        assert result["trust_color"] == "error"

    def test_defaults(self):
        result = format_agent_card({})
        assert result["agent_id"] == "Unknown"
        assert result["name"] == "Unknown"
        assert result["trust_score"] == 0.0
        assert result["trust_level"] == "LOW"

    def test_uses_agent_name_fallback(self):
        result = format_agent_card({"agent_name": "Fallback"})
        assert result["name"] == "Fallback"


class TestFormatProposalCard:
    def test_full_proposal(self):
        proposal = {
            "proposal_id": "P-001",
            "proposal_type": "create",
            "proposal_status": "approved",
            "proposer_id": "A-001",
            "affected_rule": "R-1",
            "evidence": "some evidence",
        }
        result = format_proposal_card(proposal)
        assert result["proposal_id"] == "P-001"
        assert result["status"] == "approved"
        assert result["status_color"] == "success"
        assert result["proposer_id"] == "A-001"

    def test_defaults(self):
        result = format_proposal_card({})
        assert result["proposal_id"] == "Unknown"
        assert result["status"] == "pending"
        assert result["status_color"] == "info"
        assert result["affected_rule"] == ""
