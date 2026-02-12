"""
Unit tests for Governance Stores - Agent Configuration.

Per DOC-SIZE-01-v1: Tests for stores/agents.py module.
Tests: _calculate_trust_score, _AGENT_BASE_CONFIG, get_agent, get_all_agents.
"""

import pytest

from governance.stores.agents import (
    _calculate_trust_score,
    _AGENT_BASE_CONFIG,
    _YAML_KEY_TO_AGENT_ID,
    get_agent,
    get_all_agents,
    get_available_agents_for_chat,
)


class TestCalculateTrustScore:
    """Tests for _calculate_trust_score()."""

    def test_zero_tasks(self):
        score = _calculate_trust_score("test", 0, 0.85)
        assert score == 0.85

    def test_increases_with_tasks(self):
        score0 = _calculate_trust_score("test", 0, 0.85)
        score10 = _calculate_trust_score("test", 10, 0.85)
        assert score10 > score0

    def test_logarithmic_growth(self):
        score10 = _calculate_trust_score("test", 10, 0.85)
        score100 = _calculate_trust_score("test", 100, 0.85)
        score1000 = _calculate_trust_score("test", 1000, 0.85)
        # Growth is sub-linear: 100x more tasks gives far less than 100x boost
        assert score1000 > score100 > score10
        boost_1000 = score1000 - 0.85
        assert boost_1000 < 0.85 * 0.20  # Less than 20% boost even at 1000

    def test_capped_at_1(self):
        score = _calculate_trust_score("test", 1000000, 0.99)
        assert score <= 1.0

    def test_different_base_trust(self):
        score_high = _calculate_trust_score("test", 10, 0.95)
        score_low = _calculate_trust_score("test", 10, 0.50)
        assert score_high > score_low


class TestAgentBaseConfig:
    """Tests for _AGENT_BASE_CONFIG."""

    def test_all_five_agents(self):
        expected = ["code-agent", "task-orchestrator", "rules-curator",
                     "research-agent", "local-assistant"]
        for agent_id in expected:
            assert agent_id in _AGENT_BASE_CONFIG

    def test_all_paused_by_default(self):
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert config["default_status"] == "PAUSED"

    def test_have_capabilities(self):
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert "capabilities" in config
            assert len(config["capabilities"]) > 0

    def test_have_base_trust(self):
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert 0.0 < config["base_trust"] <= 1.0


class TestYamlKeyMapping:
    """Tests for _YAML_KEY_TO_AGENT_ID mapping."""

    def test_ten_mappings(self):
        """5 current identity keys + 5 legacy backward-compat keys."""
        assert len(_YAML_KEY_TO_AGENT_ID) == 10

    def test_current_identity_mappings(self):
        assert _YAML_KEY_TO_AGENT_ID["task-orchestrator"] == "task-orchestrator"
        assert _YAML_KEY_TO_AGENT_ID["code-agent"] == "code-agent"
        assert _YAML_KEY_TO_AGENT_ID["rules-curator"] == "rules-curator"
        assert _YAML_KEY_TO_AGENT_ID["research-agent"] == "research-agent"
        assert _YAML_KEY_TO_AGENT_ID["simple-assistant"] == "simple-assistant"

    def test_legacy_orchestrator_mapping(self):
        assert _YAML_KEY_TO_AGENT_ID["orchestrator"] == "task-orchestrator"

    def test_coder_mapping(self):
        assert _YAML_KEY_TO_AGENT_ID["coder"] == "code-agent"


class TestGetAgent:
    """Tests for get_agent()."""

    def test_known_agent(self):
        agent = get_agent("code-agent")
        assert agent is not None
        assert agent["agent_id"] == "code-agent"
        assert "trust_score" in agent

    def test_unknown_agent(self):
        assert get_agent("nonexistent") is None

    def test_agent_has_required_fields(self):
        agent = get_agent("code-agent")
        for field in ["agent_id", "name", "agent_type", "status",
                       "trust_score", "capabilities"]:
            assert field in agent


class TestGetAllAgents:
    """Tests for get_all_agents()."""

    def test_returns_five(self):
        agents = get_all_agents()
        assert len(agents) == 5

    def test_returns_list(self):
        agents = get_all_agents()
        assert isinstance(agents, list)
        assert all(isinstance(a, dict) for a in agents)


class TestGetAvailableAgentsForChat:
    """Tests for get_available_agents_for_chat()."""

    def test_returns_list(self):
        agents = get_available_agents_for_chat()
        assert isinstance(agents, list)
        assert len(agents) == 5
