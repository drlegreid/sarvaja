"""
Agent Trust Dashboard Tests (P9.5)
==================================
Tests for RULE-011 compliance metrics and agent trust scoring.

Per RULE-012: DSP Semantic Code Structure
Per TDD: Write tests first, then implement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Reusable constant for mock path (DRY principle - per P9.4 lesson)
TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_agents():
    """Sample agents for testing."""
    return [
        {
            'agent_id': 'claude-code-main',
            'name': 'Claude Code',
            'agent_type': 'claude-code',
            'trust_score': 0.92,
            'compliance_rate': 0.95,
            'accuracy_rate': 0.88,
            'tenure_days': 120,
        },
        {
            'agent_id': 'sync-agent-1',
            'name': 'Sync Agent',
            'agent_type': 'sync-agent',
            'trust_score': 0.78,
            'compliance_rate': 0.80,
            'accuracy_rate': 0.75,
            'tenure_days': 45,
        },
        {
            'agent_id': 'docker-agent-1',
            'name': 'Docker Agent',
            'agent_type': 'docker-agent',
            'trust_score': 0.45,
            'compliance_rate': 0.50,
            'accuracy_rate': 0.40,
            'tenure_days': 10,
        },
    ]


@pytest.fixture
def sample_proposals():
    """Sample proposals for testing."""
    return [
        {
            'proposal_id': 'PROP-001',
            'proposal_type': 'modify',
            'proposal_status': 'approved',
            'proposer_id': 'claude-code-main',
            'affected_rule': 'RULE-007',
        },
        {
            'proposal_id': 'PROP-002',
            'proposal_type': 'create',
            'proposal_status': 'pending',
            'proposer_id': 'sync-agent-1',
            'affected_rule': 'RULE-015',
        },
    ]


@pytest.fixture
def sample_votes():
    """Sample votes for testing."""
    return [
        {
            'voter_id': 'claude-code-main',
            'proposal_id': 'PROP-002',
            'vote_value': 'approve',
            'vote_weight': 0.92,
        },
        {
            'voter_id': 'sync-agent-1',
            'proposal_id': 'PROP-002',
            'vote_value': 'reject',
            'vote_weight': 0.78,
        },
    ]


@pytest.fixture
def mock_client():
    """Create a mock TypeDBClient."""
    client = Mock()
    client.connect.return_value = True
    client.close.return_value = None
    return client


# =============================================================================
# DATA ACCESS TESTS
# =============================================================================

class TestGetAgents:
    """Tests for get_agents function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_agents
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_agents()

            assert result == []
            mock_client.close.assert_called_once()

    def test_returns_agents_list(self, mock_client, sample_agents):
        """Test returns list of agent dicts."""
        mock_client.list_agents.return_value = sample_agents

        from agent.governance_ui.data_access import get_agents
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_agents()

            assert len(result) == 3
            assert result[0]['agent_id'] == 'claude-code-main'


class TestGetAgentTrustScore:
    """Tests for get_agent_trust_score function."""

    def test_returns_none_on_connection_failure(self):
        """Test returns None when connection fails."""
        from agent.governance_ui.data_access import get_agent_trust_score
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_agent_trust_score('claude-code-main')

            assert result is None

    def test_returns_trust_score(self, mock_client):
        """Test returns agent trust score."""
        mock_client.get_agent_trust.return_value = 0.92

        from agent.governance_ui.data_access import get_agent_trust_score
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_agent_trust_score('claude-code-main')

            assert result == 0.92


class TestCalculateTrustScore:
    """Tests for calculate_trust_score function (RULE-011 formula)."""

    def test_calculates_correct_trust_score(self):
        """Test trust score formula: Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)."""
        from agent.governance_ui.data_access import calculate_trust_score

        # Compliance: 0.95, Accuracy: 0.88, Consistency: 0.80, Tenure: 1.0 (max)
        # Expected: (0.95 * 0.4) + (0.88 * 0.3) + (0.80 * 0.2) + (1.0 * 0.1) = 0.38 + 0.264 + 0.16 + 0.1 = 0.904
        result = calculate_trust_score(
            compliance_rate=0.95,
            accuracy_rate=0.88,
            consistency_rate=0.80,
            tenure_days=365  # Max tenure = 1.0
        )

        assert abs(result - 0.904) < 0.001

    def test_tenure_normalization(self):
        """Test tenure is normalized to 0-1 scale (365 days = 1.0)."""
        from agent.governance_ui.data_access import calculate_trust_score

        # New agent (10 days) vs veteran (365+ days)
        new_agent = calculate_trust_score(0.8, 0.8, 0.8, 10)
        veteran = calculate_trust_score(0.8, 0.8, 0.8, 365)

        # Veteran should have higher score due to tenure
        assert veteran > new_agent

    def test_handles_zero_values(self):
        """Test handles zero values gracefully."""
        from agent.governance_ui.data_access import calculate_trust_score

        result = calculate_trust_score(0.0, 0.0, 0.0, 0)

        assert result == 0.0

    def test_clamps_to_max_1(self):
        """Test score is clamped to maximum 1.0."""
        from agent.governance_ui.data_access import calculate_trust_score

        # Even with inflated values, max should be 1.0
        result = calculate_trust_score(1.0, 1.0, 1.0, 1000)

        assert result <= 1.0


class TestGetAgentActions:
    """Tests for get_agent_actions function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_agent_actions
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_agent_actions('claude-code-main')

            assert result == []

    def test_returns_actions_list(self, mock_client):
        """Test returns list of agent actions."""
        mock_client.get_agent_actions.return_value = [
            {'action_type': 'propose', 'outcome': 'success'},
            {'action_type': 'vote', 'outcome': 'success'},
        ]

        from agent.governance_ui.data_access import get_agent_actions
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_agent_actions('claude-code-main')

            assert len(result) == 2
            assert result[0]['action_type'] == 'propose'


class TestGetProposals:
    """Tests for get_proposals function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_proposals
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_proposals()

            assert result == []

    def test_returns_proposals_list(self, mock_client, sample_proposals):
        """Test returns list of proposals."""
        mock_client.list_proposals.return_value = sample_proposals

        from agent.governance_ui.data_access import get_proposals
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_proposals()

            assert len(result) == 2
            assert result[0]['proposal_id'] == 'PROP-001'


class TestGetProposalVotes:
    """Tests for get_proposal_votes function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_proposal_votes
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_proposal_votes('PROP-001')

            assert result == []

    def test_returns_votes_list(self, mock_client, sample_votes):
        """Test returns list of votes for proposal."""
        mock_client.get_proposal_votes.return_value = sample_votes

        from agent.governance_ui.data_access import get_proposal_votes
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_proposal_votes('PROP-002')

            assert len(result) == 2


class TestGetEscalatedProposals:
    """Tests for get_escalated_proposals function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_escalated_proposals
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_escalated_proposals()

            assert result == []

    def test_returns_escalated_list(self, mock_client):
        """Test returns list of escalated proposals."""
        mock_client.get_escalated_proposals.return_value = [
            {'proposal_id': 'PROP-003', 'escalation_trigger': 'DEADLOCK'}
        ]

        from agent.governance_ui.data_access import get_escalated_proposals
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_escalated_proposals()

            assert len(result) == 1
            assert result[0]['escalation_trigger'] == 'DEADLOCK'


class TestBuildTrustLeaderboard:
    """Tests for build_trust_leaderboard function."""

    def test_sorts_agents_by_trust_score(self, sample_agents):
        """Test agents are sorted by trust score descending."""
        from agent.governance_ui.data_access import build_trust_leaderboard

        leaderboard = build_trust_leaderboard(sample_agents)

        assert len(leaderboard) == 3
        assert leaderboard[0]['agent_id'] == 'claude-code-main'  # Highest trust
        assert leaderboard[2]['agent_id'] == 'docker-agent-1'    # Lowest trust

    def test_includes_rank(self, sample_agents):
        """Test leaderboard includes rank."""
        from agent.governance_ui.data_access import build_trust_leaderboard

        leaderboard = build_trust_leaderboard(sample_agents)

        assert leaderboard[0]['rank'] == 1
        assert leaderboard[1]['rank'] == 2
        assert leaderboard[2]['rank'] == 3

    def test_includes_trust_level(self, sample_agents):
        """Test leaderboard includes trust level category."""
        from agent.governance_ui.data_access import build_trust_leaderboard

        leaderboard = build_trust_leaderboard(sample_agents)

        # Trust >= 0.8 = HIGH, 0.5-0.8 = MEDIUM, < 0.5 = LOW
        assert leaderboard[0]['trust_level'] == 'HIGH'     # 0.92
        assert leaderboard[1]['trust_level'] == 'MEDIUM'   # 0.78
        assert leaderboard[2]['trust_level'] == 'LOW'      # 0.45


# =============================================================================
# STATE MANAGEMENT TESTS
# =============================================================================

class TestTrustDashboardState:
    """Tests for trust dashboard state management."""

    def test_initial_state_has_trust_fields(self):
        """Test initial state includes trust dashboard fields."""
        from agent.governance_ui.state import get_initial_state
        state = get_initial_state()

        assert 'agents' in state
        assert 'selected_agent' in state
        assert 'trust_leaderboard' in state
        assert 'proposals' in state
        assert 'escalated_proposals' in state

    def test_navigation_includes_trust(self):
        """Test navigation items include trust dashboard."""
        from agent.governance_ui.state import NAVIGATION_ITEMS

        nav_values = [item['value'] for item in NAVIGATION_ITEMS]
        assert 'trust' in nav_values

    def test_with_agents_transform(self):
        """Test with_agents state transform."""
        from agent.governance_ui.state import get_initial_state, with_agents

        state = get_initial_state()
        agents = [{'agent_id': 'test', 'trust_score': 0.8}]

        new_state = with_agents(state, agents)

        assert new_state['agents'] == agents
        assert len(new_state['trust_leaderboard']) == 1

    def test_with_selected_agent_transform(self):
        """Test with_selected_agent state transform."""
        from agent.governance_ui.state import get_initial_state, with_selected_agent

        state = get_initial_state()
        agent = {'agent_id': 'test', 'trust_score': 0.8}

        new_state = with_selected_agent(state, agent)

        assert new_state['selected_agent'] == agent

    def test_with_proposals_transform(self):
        """Test with_proposals state transform."""
        from agent.governance_ui.state import get_initial_state, with_proposals

        state = get_initial_state()
        proposals = [{'proposal_id': 'PROP-001'}]

        new_state = with_proposals(state, proposals)

        assert new_state['proposals'] == proposals


class TestTrustLevelHelpers:
    """Tests for trust level helper functions."""

    def test_trust_level_colors_defined(self):
        """Test trust level colors are defined for all levels."""
        from agent.governance_ui.state import TRUST_LEVEL_COLORS

        assert 'HIGH' in TRUST_LEVEL_COLORS
        assert 'MEDIUM' in TRUST_LEVEL_COLORS
        assert 'LOW' in TRUST_LEVEL_COLORS

    def test_get_trust_level_color(self):
        """Test get_trust_level_color returns correct colors."""
        from agent.governance_ui.state import get_trust_level_color

        assert get_trust_level_color('HIGH') == 'success'
        assert get_trust_level_color('MEDIUM') == 'warning'
        assert get_trust_level_color('LOW') == 'error'
        assert get_trust_level_color('UNKNOWN') == 'grey'  # Default

    def test_get_trust_level(self):
        """Test get_trust_level categorizes correctly."""
        from agent.governance_ui.state import get_trust_level

        assert get_trust_level(0.92) == 'HIGH'
        assert get_trust_level(0.78) == 'MEDIUM'
        assert get_trust_level(0.45) == 'LOW'
        assert get_trust_level(0.80) == 'HIGH'   # Boundary
        assert get_trust_level(0.50) == 'MEDIUM' # Boundary

    def test_format_agent_card(self, sample_agents):
        """Test format_agent_card formats correctly."""
        from agent.governance_ui.state import format_agent_card

        formatted = format_agent_card(sample_agents[0])

        assert formatted['agent_id'] == 'claude-code-main'
        assert formatted['name'] == 'Claude Code'
        assert formatted['trust_score'] == 0.92
        assert formatted['trust_level'] == 'HIGH'
        assert formatted['trust_color'] == 'success'

    def test_format_proposal_card(self, sample_proposals):
        """Test format_proposal_card formats correctly."""
        from agent.governance_ui.state import format_proposal_card

        formatted = format_proposal_card(sample_proposals[0])

        assert formatted['proposal_id'] == 'PROP-001'
        assert formatted['status'] == 'approved'
        assert 'status_color' in formatted


# =============================================================================
# GOVERNANCE METRICS TESTS
# =============================================================================

class TestGovernanceMetrics:
    """Tests for governance metrics calculations."""

    def test_calculate_consensus_score(self, sample_votes):
        """Test consensus score calculation."""
        from agent.governance_ui.data_access import calculate_consensus_score

        # 1 approve (weight 0.92) vs 1 reject (weight 0.78)
        # Weighted approve: 0.92, Weighted reject: 0.78
        # Total: 1.70, Majority: 0.92
        # Consensus = 0.92 / 1.70 = 0.54 (approx)
        score = calculate_consensus_score(sample_votes)

        assert 0.0 <= score <= 1.0

    def test_get_governance_stats(self, sample_agents, sample_proposals):
        """Test governance stats aggregation."""
        from agent.governance_ui.data_access import get_governance_stats

        stats = get_governance_stats(sample_agents, sample_proposals)

        assert 'total_agents' in stats
        assert 'avg_trust_score' in stats
        assert 'pending_proposals' in stats
        assert 'approval_rate' in stats

    def test_avg_trust_score_calculation(self, sample_agents):
        """Test average trust score calculation."""
        from agent.governance_ui.data_access import get_governance_stats

        stats = get_governance_stats(sample_agents, [])

        # Average: (0.92 + 0.78 + 0.45) / 3 = 0.717 (approx)
        expected_avg = (0.92 + 0.78 + 0.45) / 3
        assert abs(stats['avg_trust_score'] - expected_avg) < 0.01

