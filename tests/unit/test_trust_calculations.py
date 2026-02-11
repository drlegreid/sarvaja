"""
Unit tests for Agent Trust Calculations — pure functions.

Per DOC-SIZE-01-v1: Tests for extracted trust_calculations.py module.
Tests: calculate_trust_score, build_trust_leaderboard, calculate_consensus_score,
       get_governance_stats, _get_trust_level.
"""

import pytest

from agent.governance_ui.data_access.trust_calculations import (
    TRUST_WEIGHTS,
    MAX_TENURE_DAYS,
    calculate_trust_score,
    build_trust_leaderboard,
    calculate_consensus_score,
    get_governance_stats,
    _get_trust_level,
)


class TestTrustWeights:
    """Verify trust weight constants."""

    def test_weights_sum_to_one(self):
        total = sum(TRUST_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_max_tenure_days(self):
        assert MAX_TENURE_DAYS == 365


class TestCalculateTrustScore:
    """Tests for calculate_trust_score() pure function."""

    def test_perfect_scores(self):
        score = calculate_trust_score(1.0, 1.0, 1.0, MAX_TENURE_DAYS)
        assert abs(score - 1.0) < 1e-9

    def test_zero_scores(self):
        score = calculate_trust_score(0.0, 0.0, 0.0, 0)
        assert score == 0.0

    def test_compliance_weighted_highest(self):
        # Compliance only (40% weight)
        score_compliance = calculate_trust_score(1.0, 0.0, 0.0, 0)
        assert abs(score_compliance - 0.4) < 1e-9

    def test_accuracy_weight(self):
        score = calculate_trust_score(0.0, 1.0, 0.0, 0)
        assert abs(score - 0.3) < 1e-9

    def test_consistency_weight(self):
        score = calculate_trust_score(0.0, 0.0, 1.0, 0)
        assert abs(score - 0.2) < 1e-9

    def test_tenure_weight(self):
        score = calculate_trust_score(0.0, 0.0, 0.0, MAX_TENURE_DAYS)
        assert abs(score - 0.1) < 1e-9

    def test_tenure_capped_at_max(self):
        # 2x max days should still equal 0.1 (capped)
        score = calculate_trust_score(0.0, 0.0, 0.0, MAX_TENURE_DAYS * 2)
        assert abs(score - 0.1) < 1e-9

    def test_partial_scores(self):
        score = calculate_trust_score(0.8, 0.7, 0.6, 182)
        expected = (0.8 * 0.4) + (0.7 * 0.3) + (0.6 * 0.2) + (182 / 365 * 0.1)
        assert abs(score - expected) < 1e-9

    def test_clamped_to_range(self):
        score = calculate_trust_score(1.0, 1.0, 1.0, 9999)
        assert score <= 1.0
        assert score >= 0.0


class TestGetTrustLevel:
    """Tests for _get_trust_level() helper."""

    def test_high_trust(self):
        assert _get_trust_level(0.8) == "HIGH"
        assert _get_trust_level(0.95) == "HIGH"
        assert _get_trust_level(1.0) == "HIGH"

    def test_medium_trust(self):
        assert _get_trust_level(0.5) == "MEDIUM"
        assert _get_trust_level(0.79) == "MEDIUM"

    def test_low_trust(self):
        assert _get_trust_level(0.0) == "LOW"
        assert _get_trust_level(0.49) == "LOW"


class TestBuildTrustLeaderboard:
    """Tests for build_trust_leaderboard() pure function."""

    def test_empty_agents(self):
        result = build_trust_leaderboard([])
        assert result == []

    def test_sorted_by_trust_descending(self):
        agents = [
            {"agent_id": "low", "trust_score": 0.3},
            {"agent_id": "high", "trust_score": 0.9},
            {"agent_id": "mid", "trust_score": 0.6},
        ]
        result = build_trust_leaderboard(agents)
        assert result[0]["agent_id"] == "high"
        assert result[1]["agent_id"] == "mid"
        assert result[2]["agent_id"] == "low"

    def test_ranks_assigned(self):
        agents = [
            {"agent_id": "a", "trust_score": 0.9},
            {"agent_id": "b", "trust_score": 0.5},
        ]
        result = build_trust_leaderboard(agents)
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2

    def test_trust_levels_assigned(self):
        agents = [
            {"agent_id": "high", "trust_score": 0.85},
            {"agent_id": "med", "trust_score": 0.6},
            {"agent_id": "low", "trust_score": 0.2},
        ]
        result = build_trust_leaderboard(agents)
        assert result[0]["trust_level"] == "HIGH"
        assert result[1]["trust_level"] == "MEDIUM"
        assert result[2]["trust_level"] == "LOW"

    def test_preserves_original_fields(self):
        agents = [{"agent_id": "a", "trust_score": 0.9, "extra": "data"}]
        result = build_trust_leaderboard(agents)
        assert result[0]["extra"] == "data"

    def test_missing_trust_score_defaults_zero(self):
        agents = [{"agent_id": "no-score"}]
        result = build_trust_leaderboard(agents)
        assert result[0]["trust_level"] == "LOW"
        assert result[0]["rank"] == 1


class TestCalculateConsensusScore:
    """Tests for calculate_consensus_score() pure function."""

    def test_empty_votes(self):
        assert calculate_consensus_score([]) == 0.0

    def test_unanimous_approve(self):
        votes = [
            {"vote_value": "approve", "vote_weight": 1.0},
            {"vote_value": "approve", "vote_weight": 1.0},
        ]
        assert calculate_consensus_score(votes) == 1.0

    def test_unanimous_reject(self):
        votes = [
            {"vote_value": "reject", "vote_weight": 1.0},
            {"vote_value": "reject", "vote_weight": 1.0},
        ]
        assert calculate_consensus_score(votes) == 1.0

    def test_split_vote(self):
        votes = [
            {"vote_value": "approve", "vote_weight": 1.0},
            {"vote_value": "reject", "vote_weight": 1.0},
        ]
        assert calculate_consensus_score(votes) == 0.5

    def test_weighted_majority(self):
        votes = [
            {"vote_value": "approve", "vote_weight": 3.0},
            {"vote_value": "reject", "vote_weight": 1.0},
        ]
        # majority = 3.0 / 4.0 = 0.75
        assert abs(calculate_consensus_score(votes) - 0.75) < 1e-9

    def test_abstain_reduces_consensus(self):
        votes = [
            {"vote_value": "approve", "vote_weight": 1.0},
            {"vote_value": "abstain", "vote_weight": 1.0},
        ]
        # majority = 1.0 / 2.0 = 0.5
        assert abs(calculate_consensus_score(votes) - 0.5) < 1e-9

    def test_default_weight(self):
        votes = [{"vote_value": "approve"}, {"vote_value": "reject"}]
        # Both default weight 1.0, split = 0.5
        assert calculate_consensus_score(votes) == 0.5


class TestGetGovernanceStats:
    """Tests for get_governance_stats() pure function."""

    def test_empty_inputs(self):
        stats = get_governance_stats([], [])
        assert stats["total_agents"] == 0
        assert stats["avg_trust_score"] == 0.0
        assert stats["total_proposals"] == 0
        assert stats["approval_rate"] == 0.0

    def test_agent_stats(self):
        agents = [
            {"trust_score": 0.9},
            {"trust_score": 0.3},
            {"trust_score": 0.6},
        ]
        stats = get_governance_stats(agents, [])
        assert stats["total_agents"] == 3
        assert abs(stats["avg_trust_score"] - 0.6) < 1e-9
        assert stats["high_trust_agents"] == 1
        assert stats["low_trust_agents"] == 1

    def test_proposal_stats(self):
        proposals = [
            {"proposal_status": "approved"},
            {"proposal_status": "approved"},
            {"proposal_status": "rejected"},
            {"proposal_status": "pending"},
        ]
        stats = get_governance_stats([], proposals)
        assert stats["total_proposals"] == 4
        assert stats["pending_proposals"] == 1
        assert stats["approved_proposals"] == 2
        assert stats["rejected_proposals"] == 1
        # approval_rate = 2/3 ≈ 0.667
        assert abs(stats["approval_rate"] - 2 / 3) < 1e-9

    def test_no_resolved_proposals(self):
        proposals = [{"proposal_status": "pending"}]
        stats = get_governance_stats([], proposals)
        assert stats["approval_rate"] == 0.0
