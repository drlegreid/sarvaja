"""
Unit tests for Agent Route Helpers.

Per DOC-SIZE-01-v1: Tests for governance/routes/agents/helpers.py.
Tests: build_agent_relations_lookup, get_agent_relations_from_lookup.
"""

from unittest.mock import MagicMock

from governance.routes.agents.helpers import (
    build_agent_relations_lookup,
    get_agent_relations_from_lookup,
)


def _mock_session(agent_id, sid):
    s = MagicMock()
    s.agent_id = agent_id
    s.id = sid
    return s


def _mock_task(agent_id, tid, status="completed"):
    t = MagicMock()
    t.agent_id = agent_id
    t.id = tid
    t.status = status
    return t


# ── build_agent_relations_lookup ───────────────────────


class TestBuildAgentRelationsLookup:
    def test_none_client(self):
        sessions, tasks, counts = build_agent_relations_lookup(None)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_empty_data(self):
        client = MagicMock()
        client.get_all_sessions.return_value = []
        client.get_all_tasks.return_value = []

        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_groups_sessions_by_agent(self):
        client = MagicMock()
        client.get_all_sessions.return_value = [
            _mock_session("bot-1", "S-1"),
            _mock_session("bot-1", "S-2"),
            _mock_session("bot-2", "S-3"),
        ]
        client.get_all_tasks.return_value = []

        sessions, _, _ = build_agent_relations_lookup(client)
        assert sessions["bot-1"] == ["S-1", "S-2"]
        assert sessions["bot-2"] == ["S-3"]

    def test_groups_active_tasks(self):
        client = MagicMock()
        client.get_all_sessions.return_value = []
        client.get_all_tasks.return_value = [
            _mock_task("bot-1", "T-1", "in_progress"),
            _mock_task("bot-1", "T-2", "completed"),
            _mock_task("bot-1", "T-3", "pending"),
        ]

        _, tasks, counts = build_agent_relations_lookup(client)
        assert tasks["bot-1"] == ["T-1", "T-3"]
        assert counts["bot-1"] == 3  # Total, not just active

    def test_session_without_agent_id(self):
        client = MagicMock()
        s = MagicMock()
        s.agent_id = None
        s.id = "S-1"
        client.get_all_sessions.return_value = [s]
        client.get_all_tasks.return_value = []

        sessions, _, _ = build_agent_relations_lookup(client)
        assert sessions == {}

    def test_exception_returns_empty(self):
        client = MagicMock()
        client.get_all_sessions.side_effect = Exception("db error")

        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}


# ── get_agent_relations_from_lookup ────────────────────


class TestGetAgentRelationsFromLookup:
    def test_found_agent(self):
        sessions_by = {"bot-1": ["S-1", "S-2"]}
        tasks_by = {"bot-1": ["T-1"]}
        counts = {"bot-1": 5}

        recent, active, total = get_agent_relations_from_lookup(
            "bot-1", sessions_by, tasks_by, counts)
        assert recent == ["S-1", "S-2"]
        assert active == ["T-1"]
        assert total == 5

    def test_unknown_agent(self):
        recent, active, total = get_agent_relations_from_lookup(
            "unknown", {}, {}, {})
        assert recent == []
        assert active == []
        assert total == 0

    def test_limits_to_5(self):
        sessions_by = {"bot-1": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6"]}
        tasks_by = {"bot-1": ["T-1", "T-2", "T-3", "T-4", "T-5", "T-6"]}

        recent, active, _ = get_agent_relations_from_lookup(
            "bot-1", sessions_by, tasks_by)
        assert len(recent) == 5
        assert len(active) == 5

    def test_none_counts(self):
        _, _, total = get_agent_relations_from_lookup(
            "bot-1", {}, {}, None)
        assert total == 0
