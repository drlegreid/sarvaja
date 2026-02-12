"""
Unit tests for Seed Data Definitions.

Per DOC-SIZE-01-v1: Tests for seed/data.py module.
Tests: get_seed_tasks, get_seed_sessions, get_seed_projects, get_seed_agents.
"""

import pytest

from governance.seed.data import (
    get_seed_tasks,
    get_seed_sessions,
    get_seed_projects,
    get_seed_agents,
)


class TestGetSeedTasks:
    """Tests for get_seed_tasks()."""

    def test_returns_list(self):
        result = get_seed_tasks()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_task_has_required_fields(self):
        for task in get_seed_tasks():
            assert "task_id" in task
            assert "description" in task
            assert "status" in task
            assert "phase" in task

    def test_unique_task_ids(self):
        ids = [t["task_id"] for t in get_seed_tasks()]
        assert len(ids) == len(set(ids))

    def test_valid_statuses(self):
        valid = {"TODO", "IN_PROGRESS", "DONE", "BLOCKED"}
        for task in get_seed_tasks():
            assert task["status"] in valid

    def test_has_linked_rules(self):
        tasks_with_rules = [t for t in get_seed_tasks() if t.get("linked_rules")]
        assert len(tasks_with_rules) > 0


class TestGetSeedSessions:
    """Tests for get_seed_sessions()."""

    def test_returns_list(self):
        result = get_seed_sessions()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_session_has_required_fields(self):
        for session in get_seed_sessions():
            assert "session_id" in session
            assert "start_time" in session
            assert "status" in session
            assert "description" in session

    def test_unique_session_ids(self):
        ids = [s["session_id"] for s in get_seed_sessions()]
        assert len(ids) == len(set(ids))

    def test_session_id_format(self):
        for session in get_seed_sessions():
            assert session["session_id"].startswith("SESSION-")

    def test_has_evidence_files(self):
        sessions_with_evidence = [
            s for s in get_seed_sessions() if s.get("evidence_files")
        ]
        assert len(sessions_with_evidence) > 0


class TestGetSeedProjects:
    """Tests for get_seed_projects()."""

    def test_returns_list(self):
        result = get_seed_projects()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_project_has_required_fields(self):
        for proj in get_seed_projects():
            assert "project_id" in proj
            assert "name" in proj

    def test_sarvaja_project_exists(self):
        ids = [p["project_id"] for p in get_seed_projects()]
        assert "PROJ-SARVAJA" in ids


class TestGetSeedAgents:
    """Tests for get_seed_agents()."""

    def test_returns_list(self):
        result = get_seed_agents()
        assert isinstance(result, list)
        assert len(result) == 5

    def test_agent_has_required_fields(self):
        for agent in get_seed_agents():
            assert "agent_id" in agent
            assert "name" in agent
            assert "agent_type" in agent
            assert "base_trust" in agent

    def test_unique_agent_ids(self):
        ids = [a["agent_id"] for a in get_seed_agents()]
        assert len(ids) == len(set(ids))

    def test_trust_scores_in_range(self):
        for agent in get_seed_agents():
            assert 0.0 <= agent["base_trust"] <= 1.0

    def test_known_agents_present(self):
        ids = {a["agent_id"] for a in get_seed_agents()}
        assert "code-agent" in ids
        assert "research-agent" in ids
        assert "task-orchestrator" in ids
