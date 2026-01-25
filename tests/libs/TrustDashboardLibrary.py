"""
Robot Framework library for Trust Dashboard tests.

Per P9.5: Agent trust scoring and compliance metrics
Migrated from tests/test_trust_dashboard.py
"""

from unittest.mock import Mock, patch
from robot.api.deco import keyword


class TrustDashboardLibrary:
    """Library for testing trust dashboard functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'

    def _sample_agents(self):
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
            },
            {
                'agent_id': 'docker-agent-1',
                'name': 'Docker Agent',
                'agent_type': 'docker-agent',
                'trust_score': 0.45,
            },
        ]

    def _sample_proposals(self):
        """Sample proposals for testing."""
        return [
            {'proposal_id': 'PROP-001', 'proposal_status': 'approved'},
            {'proposal_id': 'PROP-002', 'proposal_status': 'pending'},
        ]

    # =========================================================================
    # Data Access Tests
    # =========================================================================

    @keyword("Get Agents Returns Empty On Connection Failure")
    def get_agents_returns_empty_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        try:
            from agent.governance_ui.data_access import get_agents
            with patch(self.TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
                mock_client = Mock()
                mock_client.connect.return_value = False
                mock_get_client.return_value = mock_client
                result = get_agents()
                return {"empty_list": result == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Agents Returns Agents List")
    def get_agents_returns_agents_list(self):
        """Test returns list of agent dicts."""
        try:
            from agent.governance_ui.data_access import get_agents
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.list_agents.return_value = self._sample_agents()
            with patch(self.TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_agents()
                return {
                    "has_three": len(result) == 3,
                    "first_correct": result[0]['agent_id'] == 'claude-code-main'
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Agent Trust Score Returns None On Failure")
    def get_agent_trust_score_returns_none_on_failure(self):
        """Test returns None when connection fails."""
        try:
            from agent.governance_ui.data_access import get_agent_trust_score
            with patch(self.TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
                mock_client = Mock()
                mock_client.connect.return_value = False
                mock_get_client.return_value = mock_client
                result = get_agent_trust_score('claude-code-main')
                return {"is_none": result is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Agent Trust Score Returns Score")
    def get_agent_trust_score_returns_score(self):
        """Test returns agent trust score."""
        try:
            from agent.governance_ui.data_access import get_agent_trust_score
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.get_agent_trust.return_value = 0.92
            with patch(self.TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_agent_trust_score('claude-code-main')
                return {"correct_score": result == 0.92}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Trust Calculation Tests
    # =========================================================================

    @keyword("Calculate Trust Score Correct")
    def calculate_trust_score_correct(self):
        """Test trust score formula."""
        try:
            from agent.governance_ui.data_access import calculate_trust_score
            result = calculate_trust_score(
                compliance_rate=0.95,
                accuracy_rate=0.88,
                consistency_rate=0.80,
                tenure_days=365
            )
            expected = 0.904  # (0.95*0.4) + (0.88*0.3) + (0.80*0.2) + (1.0*0.1)
            return {"correct": abs(result - expected) < 0.001}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tenure Normalization Works")
    def tenure_normalization_works(self):
        """Test tenure is normalized to 0-1 scale."""
        try:
            from agent.governance_ui.data_access import calculate_trust_score
            new_agent = calculate_trust_score(0.8, 0.8, 0.8, 10)
            veteran = calculate_trust_score(0.8, 0.8, 0.8, 365)
            return {"veteran_higher": veteran > new_agent}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Zero Values Handled")
    def zero_values_handled(self):
        """Test handles zero values gracefully."""
        try:
            from agent.governance_ui.data_access import calculate_trust_score
            result = calculate_trust_score(0.0, 0.0, 0.0, 0)
            return {"is_zero": result == 0.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Score Clamped To Max")
    def score_clamped_to_max(self):
        """Test score is clamped to maximum 1.0."""
        try:
            from agent.governance_ui.data_access import calculate_trust_score
            result = calculate_trust_score(1.0, 1.0, 1.0, 1000)
            return {"max_one": result <= 1.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Leaderboard Tests
    # =========================================================================

    @keyword("Build Trust Leaderboard Sorts By Score")
    def build_trust_leaderboard_sorts_by_score(self):
        """Test agents are sorted by trust score descending."""
        try:
            from agent.governance_ui.data_access import build_trust_leaderboard
            leaderboard = build_trust_leaderboard(self._sample_agents())
            return {
                "first_highest": leaderboard[0]['agent_id'] == 'claude-code-main',
                "last_lowest": leaderboard[2]['agent_id'] == 'docker-agent-1'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Leaderboard Includes Rank")
    def leaderboard_includes_rank(self):
        """Test leaderboard includes rank."""
        try:
            from agent.governance_ui.data_access import build_trust_leaderboard
            leaderboard = build_trust_leaderboard(self._sample_agents())
            return {
                "rank_1": leaderboard[0].get('rank') == 1,
                "rank_2": leaderboard[1].get('rank') == 2,
                "rank_3": leaderboard[2].get('rank') == 3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Leaderboard Includes Trust Level")
    def leaderboard_includes_trust_level(self):
        """Test leaderboard includes trust level category."""
        try:
            from agent.governance_ui.data_access import build_trust_leaderboard
            leaderboard = build_trust_leaderboard(self._sample_agents())
            return {
                "high": leaderboard[0].get('trust_level') == 'HIGH',
                "medium": leaderboard[1].get('trust_level') == 'MEDIUM',
                "low": leaderboard[2].get('trust_level') == 'LOW'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # State Management Tests
    # =========================================================================

    @keyword("Initial State Has Trust Fields")
    def initial_state_has_trust_fields(self):
        """Test initial state includes trust dashboard fields."""
        try:
            from agent.governance_ui.state import get_initial_state
            state = get_initial_state()
            return {
                "has_agents": 'agents' in state,
                "has_selected_agent": 'selected_agent' in state,
                "has_trust_leaderboard": 'trust_leaderboard' in state,
                "has_proposals": 'proposals' in state,
                "has_escalated": 'escalated_proposals' in state
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Navigation Includes Trust")
    def navigation_includes_trust(self):
        """Test navigation items include trust dashboard."""
        try:
            from agent.governance_ui.state import NAVIGATION_ITEMS
            nav_values = [item['value'] for item in NAVIGATION_ITEMS]
            return {"has_trust": 'trust' in nav_values}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Agents Transform Works")
    def with_agents_transform_works(self):
        """Test with_agents state transform."""
        try:
            from agent.governance_ui.state import get_initial_state, with_agents
            state = get_initial_state()
            agents = [{'agent_id': 'test', 'trust_score': 0.8}]
            new_state = with_agents(state, agents)
            return {
                "agents_set": new_state['agents'] == agents,
                "leaderboard_built": len(new_state['trust_leaderboard']) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Trust Level Helpers Tests
    # =========================================================================

    @keyword("Trust Level Colors Defined")
    def trust_level_colors_defined(self):
        """Test trust level colors are defined for all levels."""
        try:
            from agent.governance_ui.state import TRUST_LEVEL_COLORS
            return {
                "has_high": 'HIGH' in TRUST_LEVEL_COLORS,
                "has_medium": 'MEDIUM' in TRUST_LEVEL_COLORS,
                "has_low": 'LOW' in TRUST_LEVEL_COLORS
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Trust Level Color Works")
    def get_trust_level_color_works(self):
        """Test get_trust_level_color returns correct colors."""
        try:
            from agent.governance_ui.state import get_trust_level_color
            return {
                "high_success": get_trust_level_color('HIGH') == 'success',
                "medium_warning": get_trust_level_color('MEDIUM') == 'warning',
                "low_error": get_trust_level_color('LOW') == 'error',
                "unknown_grey": get_trust_level_color('UNKNOWN') == 'grey'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Trust Level Categorizes Correctly")
    def get_trust_level_categorizes_correctly(self):
        """Test get_trust_level categorizes correctly."""
        try:
            from agent.governance_ui.state import get_trust_level
            return {
                "high_92": get_trust_level(0.92) == 'HIGH',
                "medium_78": get_trust_level(0.78) == 'MEDIUM',
                "low_45": get_trust_level(0.45) == 'LOW',
                "high_boundary": get_trust_level(0.80) == 'HIGH',
                "medium_boundary": get_trust_level(0.50) == 'MEDIUM'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Governance Metrics Tests
    # =========================================================================

    @keyword("Consensus Score In Range")
    def consensus_score_in_range(self):
        """Test consensus score calculation."""
        try:
            from agent.governance_ui.data_access import calculate_consensus_score
            sample_votes = [
                {'vote_value': 'approve', 'vote_weight': 0.92},
                {'vote_value': 'reject', 'vote_weight': 0.78},
            ]
            score = calculate_consensus_score(sample_votes)
            return {"in_range": 0.0 <= score <= 1.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Stats Has Fields")
    def governance_stats_has_fields(self):
        """Test governance stats aggregation."""
        try:
            from agent.governance_ui.data_access import get_governance_stats
            stats = get_governance_stats(self._sample_agents(), self._sample_proposals())
            return {
                "has_total_agents": 'total_agents' in stats,
                "has_avg_trust": 'avg_trust_score' in stats,
                "has_pending": 'pending_proposals' in stats,
                "has_approval": 'approval_rate' in stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Average Trust Score Correct")
    def average_trust_score_correct(self):
        """Test average trust score calculation."""
        try:
            from agent.governance_ui.data_access import get_governance_stats
            stats = get_governance_stats(self._sample_agents(), [])
            expected_avg = (0.92 + 0.78 + 0.45) / 3
            return {"correct": abs(stats['avg_trust_score'] - expected_avg) < 0.01}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
