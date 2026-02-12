"""
Unit tests for Agent Route Helpers.

Per DOC-SIZE-01-v1: Tests for routes/agents/helpers.py module.
Tests: build_agent_relations_lookup, get_agent_relations_from_lookup.
"""

import pytest
from unittest.mock import MagicMock

from governance.routes.agents.helpers import (
    build_agent_relations_lookup,
    get_agent_relations_from_lookup,
)


def _make_session(sid, agent_id=None):
    s = MagicMock()
    s.id = sid
    s.agent_id = agent_id
    return s


def _make_task(tid, agent_id=None, status="pending"):
    t = MagicMock()
    t.id = tid
    t.agent_id = agent_id
    t.status = status
    return t


# ---------------------------------------------------------------------------
# build_agent_relations_lookup
# ---------------------------------------------------------------------------
class TestBuildAgentRelationsLookup:
    """Tests for build_agent_relations_lookup()."""

    def test_returns_empty_when_no_client(self):
        sessions, tasks, counts = build_agent_relations_lookup(None)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_groups_sessions_by_agent(self):
        client = MagicMock()
        client.get_all_sessions.return_value = [
            _make_session("S-1", "agent-a"),
            _make_session("S-2", "agent-a"),
            _make_session("S-3", "agent-b"),
        ]
        client.get_all_tasks.return_value = []
        sessions, _, _ = build_agent_relations_lookup(client)
        assert sessions["agent-a"] == ["S-1", "S-2"]
        assert sessions["agent-b"] == ["S-3"]

    def test_groups_active_tasks(self):
        client = MagicMock()
        client.get_all_sessions.return_value = []
        client.get_all_tasks.return_value = [
            _make_task("T-1", "agent-a", "pending"),
            _make_task("T-2", "agent-a", "done"),
            _make_task("T-3", "agent-a", "in_progress"),
        ]
        _, tasks, _ = build_agent_relations_lookup(client)
        assert tasks["agent-a"] == ["T-1", "T-3"]  # only pending + in_progress

    def test_counts_all_tasks(self):
        client = MagicMock()
        client.get_all_sessions.return_value = []
        client.get_all_tasks.return_value = [
            _make_task("T-1", "agent-a", "done"),
            _make_task("T-2", "agent-a", "done"),
            _make_task("T-3", "agent-b", "pending"),
        ]
        _, _, counts = build_agent_relations_lookup(client)
        assert counts["agent-a"] == 2
        assert counts["agent-b"] == 1

    def test_skips_sessions_without_agent(self):
        client = MagicMock()
        client.get_all_sessions.return_value = [
            _make_session("S-1", None),
        ]
        client.get_all_tasks.return_value = []
        sessions, _, _ = build_agent_relations_lookup(client)
        assert sessions == {}

    def test_handles_exception(self):
        client = MagicMock()
        client.get_all_sessions.side_effect = ConnectionError("down")
        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_handles_none_sessions(self):
        client = MagicMock()
        client.get_all_sessions.return_value = None
        client.get_all_tasks.return_value = None
        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}


# ---------------------------------------------------------------------------
# get_agent_relations_from_lookup
# ---------------------------------------------------------------------------
class TestGetAgentRelationsFromLookup:
    """Tests for get_agent_relations_from_lookup()."""

    def test_returns_matching_data(self):
        sessions = {"agent-a": ["S-1", "S-2"]}
        tasks = {"agent-a": ["T-1"]}
        counts = {"agent-a": 5}
        s, t, c = get_agent_relations_from_lookup("agent-a", sessions, tasks, counts)
        assert s == ["S-1", "S-2"]
        assert t == ["T-1"]
        assert c == 5

    def test_returns_empty_for_unknown_agent(self):
        s, t, c = get_agent_relations_from_lookup("unknown", {}, {}, {})
        assert s == []
        assert t == []
        assert c == 0

    def test_limits_sessions_to_five(self):
        sessions = {"agent-a": [f"S-{i}" for i in range(10)]}
        s, _, _ = get_agent_relations_from_lookup("agent-a", sessions, {}, {})
        assert len(s) == 5

    def test_limits_tasks_to_five(self):
        tasks = {"agent-a": [f"T-{i}" for i in range(10)]}
        _, t, _ = get_agent_relations_from_lookup("agent-a", {}, tasks, {})
        assert len(t) == 5

    def test_handles_none_task_count(self):
        """task_count_by_agent defaults to None."""
        s, t, c = get_agent_relations_from_lookup("a", {}, {}, None)
        assert c == 0
