"""Tests for governance/stores/agents.py — Agent config, metrics, trust score.

Covers: _calculate_trust_score, _build_agents_store, _AGENT_BASE_CONFIG,
_YAML_KEY_TO_AGENT_ID, _update_agent_metrics_on_claim, get_agent, get_all_agents,
get_available_agents_for_chat, _load_agent_metrics, _save_agent_metrics.
"""

import math
import json
import unittest
from unittest.mock import patch, mock_open, MagicMock

from governance.stores.agents import (
    _AGENT_BASE_CONFIG,
    _YAML_KEY_TO_AGENT_ID,
    _calculate_trust_score,
    _build_agents_store,
    _update_agent_metrics_on_claim,
    _load_agent_metrics,
    _save_agent_metrics,
    get_agent,
    get_all_agents,
    get_available_agents_for_chat,
    _agents_store,
)


class TestAgentBaseConfig(unittest.TestCase):
    """Tests for _AGENT_BASE_CONFIG constants."""

    def test_five_agents(self):
        self.assertEqual(len(_AGENT_BASE_CONFIG), 5)

    def test_agent_ids(self):
        expected = {"code-agent", "task-orchestrator", "rules-curator",
                    "research-agent", "local-assistant"}
        self.assertEqual(set(_AGENT_BASE_CONFIG.keys()), expected)

    def test_all_paused(self):
        """Per GAP-AGENT-PAUSE-001: all agents default PAUSED."""
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            self.assertEqual(config["default_status"], "PAUSED",
                             f"{agent_id} should be PAUSED")

    def test_base_trust_range(self):
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            self.assertGreater(config["base_trust"], 0.0)
            self.assertLessEqual(config["base_trust"], 1.0)

    def test_capabilities_list(self):
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            self.assertIsInstance(config["capabilities"], list)
            self.assertGreater(len(config["capabilities"]), 0)

    def test_code_agent_highest_capability(self):
        caps = _AGENT_BASE_CONFIG["code-agent"]["capabilities"]
        self.assertIn("code_generation", caps)
        self.assertIn("test_writing", caps)


class TestYamlKeyMapping(unittest.TestCase):
    """Tests for _YAML_KEY_TO_AGENT_ID mapping."""

    def test_current_keys(self):
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["code-agent"], "code-agent")
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["task-orchestrator"], "task-orchestrator")

    def test_legacy_keys(self):
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["orchestrator"], "task-orchestrator")
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["coder"], "code-agent")
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["researcher"], "research-agent")

    def test_simple_assistant_alias(self):
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["simple-assistant"], "local-assistant")
        self.assertEqual(_YAML_KEY_TO_AGENT_ID["simple_assistant"], "local-assistant")


class TestCalculateTrustScore(unittest.TestCase):
    """Tests for _calculate_trust_score."""

    def test_zero_tasks(self):
        score = _calculate_trust_score("test", 0, 0.85)
        self.assertEqual(score, 0.85)

    def test_small_task_count(self):
        score = _calculate_trust_score("test", 10, 0.85)
        expected = 0.85 * (1 + math.log10(11) * 0.05)
        self.assertAlmostEqual(score, expected, places=6)
        self.assertGreater(score, 0.85)

    def test_large_task_count(self):
        score = _calculate_trust_score("test", 1000, 0.85)
        # log10(1001) ≈ 3.0, so boost ≈ 0.15, score ≈ 0.85 * 1.15 ≈ 0.9775
        self.assertGreater(score, 0.95)
        self.assertLessEqual(score, 1.0)

    def test_capped_at_one(self):
        # Very high base trust + many tasks should cap at 1.0
        score = _calculate_trust_score("test", 100000, 0.99)
        self.assertLessEqual(score, 1.0)

    def test_different_base_trust(self):
        low = _calculate_trust_score("test", 100, 0.50)
        high = _calculate_trust_score("test", 100, 0.95)
        self.assertLess(low, high)

    def test_monotonic_increase(self):
        prev = _calculate_trust_score("test", 0, 0.85)
        for n in [1, 10, 100, 1000]:
            curr = _calculate_trust_score("test", n, 0.85)
            self.assertGreaterEqual(curr, prev)
            prev = curr


class TestBuildAgentsStore(unittest.TestCase):
    """Tests for _build_agents_store."""

    @patch("governance.stores.agents._load_workflow_configs", return_value={})
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_builds_five_agents(self, mock_metrics, mock_wf):
        store = _build_agents_store()
        self.assertEqual(len(store), 5)

    @patch("governance.stores.agents._load_workflow_configs", return_value={})
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_default_fields(self, mock_metrics, mock_wf):
        store = _build_agents_store()
        agent = store["code-agent"]
        self.assertEqual(agent["agent_id"], "code-agent")
        self.assertEqual(agent["name"], "Claude Code Agent")
        self.assertEqual(agent["agent_type"], "claude-code")
        self.assertEqual(agent["status"], "PAUSED")
        self.assertEqual(agent["tasks_executed"], 0)

    @patch("governance.stores.agents._load_workflow_configs", return_value={})
    @patch("governance.stores.agents._load_agent_metrics", return_value={
        "code-agent": {"tasks_executed": 50, "last_active": "2026-02-13T10:00:00"}
    })
    def test_loads_metrics(self, mock_metrics, mock_wf):
        store = _build_agents_store()
        agent = store["code-agent"]
        self.assertEqual(agent["tasks_executed"], 50)
        self.assertEqual(agent["last_active"], "2026-02-13T10:00:00")
        self.assertGreater(agent["trust_score"], _AGENT_BASE_CONFIG["code-agent"]["base_trust"])

    @patch("governance.stores.agents._load_workflow_configs", return_value={
        "code-agent": {"description": "AI coding assistant", "model": "claude", "instructions": "help", "tools": ["chat"]},
    })
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_loads_workflow_config(self, mock_metrics, mock_wf):
        store = _build_agents_store()
        agent = store["code-agent"]
        self.assertEqual(agent["description"], "AI coding assistant")
        self.assertEqual(agent["model"], "claude")
        self.assertEqual(agent["tools"], ["chat"])


class TestUpdateAgentMetricsOnClaim(unittest.TestCase):
    """Tests for _update_agent_metrics_on_claim."""

    def setUp(self):
        # Save original agent store state
        self._orig = {}
        for k, v in _agents_store.items():
            self._orig[k] = dict(v)

    def tearDown(self):
        # Restore original state
        for k, v in self._orig.items():
            _agents_store[k] = v

    @patch("governance.stores.agents._save_agent_metrics")
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_increments_tasks(self, mock_load, mock_save):
        original_tasks = _agents_store["code-agent"]["tasks_executed"]
        _update_agent_metrics_on_claim("code-agent")
        self.assertEqual(_agents_store["code-agent"]["tasks_executed"], original_tasks + 1)

    @patch("governance.stores.agents._save_agent_metrics")
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_updates_last_active(self, mock_load, mock_save):
        _update_agent_metrics_on_claim("code-agent")
        self.assertIsNotNone(_agents_store["code-agent"]["last_active"])

    @patch("governance.stores.agents._save_agent_metrics")
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_recalculates_trust(self, mock_load, mock_save):
        orig_trust = _agents_store["code-agent"]["trust_score"]
        _update_agent_metrics_on_claim("code-agent")
        # Trust should increase (or stay same if already high)
        self.assertGreaterEqual(_agents_store["code-agent"]["trust_score"], orig_trust)

    @patch("governance.stores.agents._save_agent_metrics")
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_persists_metrics(self, mock_load, mock_save):
        _update_agent_metrics_on_claim("code-agent")
        mock_save.assert_called_once()

    @patch("governance.stores.agents._save_agent_metrics")
    @patch("governance.stores.agents._load_agent_metrics", return_value={})
    def test_unknown_agent_noop(self, mock_load, mock_save):
        _update_agent_metrics_on_claim("nonexistent-agent")
        mock_save.assert_not_called()


class TestGetAgent(unittest.TestCase):
    """Tests for get_agent and get_all_agents."""

    def test_get_existing(self):
        agent = get_agent("code-agent")
        self.assertIsNotNone(agent)
        self.assertEqual(agent["agent_id"], "code-agent")

    def test_get_missing(self):
        agent = get_agent("no-such-agent")
        self.assertIsNone(agent)

    def test_get_all_agents(self):
        agents = get_all_agents()
        self.assertEqual(len(agents), 5)
        ids = {a["agent_id"] for a in agents}
        self.assertIn("code-agent", ids)
        self.assertIn("task-orchestrator", ids)

    def test_get_available_for_chat(self):
        agents = get_available_agents_for_chat()
        self.assertEqual(len(agents), 5)
        self.assertIsInstance(agents, list)


class TestLoadSaveMetrics(unittest.TestCase):
    """Tests for _load_agent_metrics and _save_agent_metrics."""

    @patch("os.path.exists", return_value=True)
    def test_load_existing(self, mock_exists):
        data = {"code-agent": {"tasks_executed": 10, "last_active": "2026-01-01"}}
        m = mock_open(read_data=json.dumps(data))
        with patch("builtins.open", m):
            result = _load_agent_metrics()
        self.assertEqual(result["code-agent"]["tasks_executed"], 10)

    @patch("os.path.exists", return_value=False)
    def test_load_missing(self, mock_exists):
        result = _load_agent_metrics()
        self.assertEqual(result, {})

    @patch("os.path.exists", return_value=True)
    def test_load_corrupt(self, mock_exists):
        m = mock_open(read_data="NOT JSON")
        with patch("builtins.open", m):
            result = _load_agent_metrics()
        self.assertEqual(result, {})

    @patch("os.makedirs")
    def test_save(self, mock_makedirs):
        m = mock_open()
        with patch("builtins.open", m):
            _save_agent_metrics({"test": {"tasks": 1}})
        m.assert_called_once()
        mock_makedirs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
