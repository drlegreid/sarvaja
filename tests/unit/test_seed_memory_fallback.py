"""
Unit tests for Memory Fallback Seeder.

Per DOC-SIZE-01-v1: Tests for seed/memory.py module.
Tests: seed_to_memory_fallback.
"""

import pytest

from governance.seed.memory import seed_to_memory_fallback


class TestSeedToMemoryFallback:
    """Tests for seed_to_memory_fallback()."""

    def test_seeds_empty_tasks(self):
        tasks = {}
        sessions = {}
        seed_to_memory_fallback(tasks, sessions)
        assert len(tasks) > 0

    def test_seeds_empty_sessions(self):
        tasks = {}
        sessions = {}
        seed_to_memory_fallback(tasks, sessions)
        assert len(sessions) > 0

    def test_skips_non_empty_tasks(self):
        tasks = {"existing": {"task_id": "existing"}}
        sessions = {}
        seed_to_memory_fallback(tasks, sessions)
        assert len(tasks) == 1  # not modified

    def test_skips_non_empty_sessions(self):
        tasks = {}
        sessions = {"existing": {"session_id": "existing"}}
        seed_to_memory_fallback(tasks, sessions)
        assert len(sessions) == 1  # not modified

    def test_seeds_agents_when_provided(self):
        tasks = {}
        sessions = {}
        agents = {}
        seed_to_memory_fallback(tasks, sessions, agents_store=agents)
        assert len(agents) == 5  # all 5 agents

    def test_agents_default_to_paused(self):
        tasks = {}
        sessions = {}
        agents = {}
        seed_to_memory_fallback(tasks, sessions, agents_store=agents)
        for agent in agents.values():
            assert agent["status"] == "PAUSED"

    def test_agents_none_store_skipped(self):
        tasks = {}
        sessions = {}
        seed_to_memory_fallback(tasks, sessions, agents_store=None)
        # No error raised

    def test_skips_non_empty_agents(self):
        tasks = {}
        sessions = {}
        agents = {"existing": {"agent_id": "existing"}}
        seed_to_memory_fallback(tasks, sessions, agents_store=agents)
        assert len(agents) == 1

    def test_agent_fields(self):
        tasks = {}
        sessions = {}
        agents = {}
        seed_to_memory_fallback(tasks, sessions, agents_store=agents)
        for agent in agents.values():
            assert "agent_id" in agent
            assert "name" in agent
            assert "agent_type" in agent
            assert "status" in agent
            assert "trust_score" in agent
            assert "tasks_executed" in agent
            assert agent["tasks_executed"] == 0
            assert agent["last_active"] is None

    def test_task_ids_match_seed_data(self):
        from governance.seed.data import get_seed_tasks
        tasks = {}
        sessions = {}
        seed_to_memory_fallback(tasks, sessions)
        seed_ids = {t["task_id"] for t in get_seed_tasks()}
        assert set(tasks.keys()) == seed_ids
