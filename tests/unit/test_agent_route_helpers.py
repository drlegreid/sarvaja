"""
Unit tests for Agent Route Helpers.

Per DOC-SIZE-01-v1: Tests for extracted agents/helpers.py module.
Tests: build_agent_relations_lookup, get_agent_relations_from_lookup.
"""

import pytest
from unittest.mock import MagicMock

from governance.routes.agents.helpers import (
    build_agent_relations_lookup,
    get_agent_relations_from_lookup,
)


class TestBuildAgentRelationsLookup:
    """Tests for build_agent_relations_lookup()."""

    def test_no_client(self):
        sessions, tasks, counts = build_agent_relations_lookup(None)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_builds_session_lookup(self):
        s1 = MagicMock(); s1.agent_id = "code-agent"; s1.id = "S-1"
        s2 = MagicMock(); s2.agent_id = "code-agent"; s2.id = "S-2"
        s3 = MagicMock(); s3.agent_id = "research-agent"; s3.id = "S-3"

        client = MagicMock()
        client.get_all_sessions.return_value = [s1, s2, s3]
        client.get_all_tasks.return_value = []

        sessions, _, _ = build_agent_relations_lookup(client)
        assert len(sessions["code-agent"]) == 2
        assert sessions["research-agent"] == ["S-3"]

    def test_builds_task_lookup(self):
        t1 = MagicMock(); t1.agent_id = "code-agent"; t1.id = "T-1"; t1.status = "in_progress"
        t2 = MagicMock(); t2.agent_id = "code-agent"; t2.id = "T-2"; t2.status = "completed"
        t3 = MagicMock(); t3.agent_id = "research-agent"; t3.id = "T-3"; t3.status = "pending"

        client = MagicMock()
        client.get_all_sessions.return_value = []
        client.get_all_tasks.return_value = [t1, t2, t3]

        _, active_tasks, task_counts = build_agent_relations_lookup(client)
        # Active only in_progress and pending
        assert active_tasks["code-agent"] == ["T-1"]
        assert active_tasks["research-agent"] == ["T-3"]
        # Total counts include all statuses
        assert task_counts["code-agent"] == 2
        assert task_counts["research-agent"] == 1

    def test_skips_no_agent_id(self):
        s1 = MagicMock(); s1.agent_id = None; s1.id = "S-1"
        t1 = MagicMock(); t1.agent_id = None; t1.id = "T-1"; t1.status = "pending"

        client = MagicMock()
        client.get_all_sessions.return_value = [s1]
        client.get_all_tasks.return_value = [t1]

        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}

    def test_handles_exception(self):
        client = MagicMock()
        client.get_all_sessions.side_effect = Exception("TypeDB down")

        sessions, tasks, counts = build_agent_relations_lookup(client)
        assert sessions == {}
        assert tasks == {}
        assert counts == {}


class TestGetAgentRelationsFromLookup:
    """Tests for get_agent_relations_from_lookup()."""

    def test_basic(self):
        sessions_by = {"agent-1": ["S-1", "S-2", "S-3"]}
        tasks_by = {"agent-1": ["T-1"]}
        counts = {"agent-1": 5}

        sess, tasks, total = get_agent_relations_from_lookup(
            "agent-1", sessions_by, tasks_by, counts,
        )
        assert sess == ["S-1", "S-2", "S-3"]
        assert tasks == ["T-1"]
        assert total == 5

    def test_caps_at_5(self):
        sessions_by = {"agent-1": [f"S-{i}" for i in range(10)]}
        tasks_by = {"agent-1": [f"T-{i}" for i in range(8)]}

        sess, tasks, _ = get_agent_relations_from_lookup(
            "agent-1", sessions_by, tasks_by,
        )
        assert len(sess) == 5
        assert len(tasks) == 5

    def test_missing_agent(self):
        sess, tasks, total = get_agent_relations_from_lookup(
            "unknown", {}, {}, {},
        )
        assert sess == []
        assert tasks == []
        assert total == 0

    def test_no_task_count_dict(self):
        sess, tasks, total = get_agent_relations_from_lookup(
            "agent-1", {"agent-1": ["S-1"]}, {},
        )
        assert total == 0
