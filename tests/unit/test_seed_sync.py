"""
Unit tests for TypeDB to Memory Sync.

Per P10.1/P10.2/P10.3: Tests for sync_typedb_to_memory().
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from governance.seed.sync import sync_typedb_to_memory


class _FakeTask:
    """Mock TypeDB task entity."""
    def __init__(self, **kw):
        self.id = kw.get("id", "TASK-001")
        self.name = kw.get("name", "Test Task")
        self.description = kw.get("description", "Desc")
        self.phase = kw.get("phase", "P10")
        self.status = kw.get("status", "TODO")
        self.agent_id = kw.get("agent_id", "code-agent")
        self.body = kw.get("body", "")
        self.linked_rules = kw.get("linked_rules", [])
        self.linked_sessions = kw.get("linked_sessions", [])
        self.gap_id = kw.get("gap_id", None)
        self.created_at = kw.get("created_at", datetime(2026, 2, 11))
        self.claimed_at = kw.get("claimed_at", None)
        self.completed_at = kw.get("completed_at", None)
        self.evidence = kw.get("evidence", None)


class _FakeSession:
    """Mock TypeDB session entity."""
    def __init__(self, **kw):
        self.id = kw.get("id", "SESSION-2026-02-11-TEST")
        self.started_at = kw.get("started_at", datetime(2026, 2, 11, 9, 0))
        self.completed_at = kw.get("completed_at", datetime(2026, 2, 11, 13, 0))
        self.status = kw.get("status", "COMPLETED")
        self.tasks_completed = kw.get("tasks_completed", 3)
        self.description = kw.get("description", "Test session")
        self.agent_id = kw.get("agent_id", "code-agent")
        self.file_path = kw.get("file_path", None)
        self.evidence_files = kw.get("evidence_files", [])
        self.linked_rules_applied = kw.get("linked_rules_applied", [])
        self.linked_decisions = kw.get("linked_decisions", [])


class _FakeAgent:
    """Mock TypeDB agent entity."""
    def __init__(self, **kw):
        self.id = kw.get("id", "code-agent")
        self.name = kw.get("name", "Code Agent")
        self.agent_type = kw.get("agent_type", "code")
        self.tasks_executed = kw.get("tasks_executed", 10)
        self.trust_score = kw.get("trust_score", 0.9)


# ---------------------------------------------------------------------------
# Task sync
# ---------------------------------------------------------------------------
class TestTaskSync:
    """Tests for task sync path."""

    def test_syncs_tasks(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask()]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        assert "TASK-001" in tasks_store
        assert tasks_store["TASK-001"]["task_id"] == "TASK-001"

    def test_task_fields(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask(
            phase="P10", status="IN_PROGRESS", agent_id="test-agent",
            linked_rules=["R-1"], gap_id="GAP-001",
        )]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        t = tasks_store["TASK-001"]
        assert t["phase"] == "P10"
        assert t["status"] == "IN_PROGRESS"
        assert t["agent_id"] == "test-agent"
        assert t["linked_rules"] == ["R-1"]
        assert t["gap_id"] == "GAP-001"

    def test_task_timestamps(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask(
            created_at=datetime(2026, 1, 1),
            completed_at=datetime(2026, 1, 2),
        )]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        t = tasks_store["TASK-001"]
        assert t["created_at"] == "2026-01-01T00:00:00"
        assert t["completed_at"] == "2026-01-02T00:00:00"

    def test_task_null_timestamps(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask(
            created_at=None, claimed_at=None, completed_at=None,
        )]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        t = tasks_store["TASK-001"]
        assert t["created_at"] is None
        assert t["claimed_at"] is None
        assert t["completed_at"] is None

    def test_task_sync_error_isolated(self):
        client = MagicMock()
        client.get_all_tasks.side_effect = Exception("DB error")
        client.get_all_sessions.return_value = [_FakeSession()]
        tasks_store = {}
        sessions_store = {}
        sync_typedb_to_memory(client, tasks_store, sessions_store)
        assert len(tasks_store) == 0
        assert len(sessions_store) == 1  # sessions still synced

    def test_multiple_tasks(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [
            _FakeTask(id="T-1"), _FakeTask(id="T-2"), _FakeTask(id="T-3"),
        ]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        assert len(tasks_store) == 3

    def test_name_fallback_to_description(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask(name=None, description="Fallback")]
        tasks_store = {}
        sync_typedb_to_memory(client, tasks_store, {})
        assert tasks_store["TASK-001"]["description"] == "Fallback"


# ---------------------------------------------------------------------------
# Session sync
# ---------------------------------------------------------------------------
class TestSessionSync:
    """Tests for session sync path."""

    def test_syncs_sessions(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = [_FakeSession()]
        sessions_store = {}
        sync_typedb_to_memory(client, {}, sessions_store)
        assert "SESSION-2026-02-11-TEST" in sessions_store

    def test_session_fields(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = [_FakeSession(
            status="ACTIVE", tasks_completed=5, agent_id="rules-curator",
        )]
        sessions_store = {}
        sync_typedb_to_memory(client, {}, sessions_store)
        s = sessions_store["SESSION-2026-02-11-TEST"]
        assert s["status"] == "ACTIVE"
        assert s["tasks_completed"] == 5
        assert s["agent_id"] == "rules-curator"

    def test_session_timestamps(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = [_FakeSession()]
        sessions_store = {}
        sync_typedb_to_memory(client, {}, sessions_store)
        s = sessions_store["SESSION-2026-02-11-TEST"]
        assert s["start_time"] is not None
        assert s["end_time"] is not None

    def test_session_null_timestamps(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = [_FakeSession(
            started_at=None, completed_at=None,
        )]
        sessions_store = {}
        sync_typedb_to_memory(client, {}, sessions_store)
        s = sessions_store["SESSION-2026-02-11-TEST"]
        assert s["start_time"] is None
        assert s["end_time"] is None

    def test_session_sync_error_isolated(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask()]
        client.get_all_sessions.side_effect = Exception("DB error")
        tasks_store = {}
        sessions_store = {}
        sync_typedb_to_memory(client, tasks_store, sessions_store)
        assert len(tasks_store) == 1
        assert len(sessions_store) == 0


# ---------------------------------------------------------------------------
# Agent sync
# ---------------------------------------------------------------------------
class TestAgentSync:
    """Tests for agent sync path (P10.3)."""

    def test_syncs_agents(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent()]
        agents_store = {}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        assert "code-agent" in agents_store

    def test_agent_fields(self):
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent(
            name="Test Agent", agent_type="test", tasks_executed=20, trust_score=0.95,
        )]
        agents_store = {}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        a = agents_store["code-agent"]
        assert a["name"] == "Test Agent"
        assert a["agent_type"] == "test"
        assert a["tasks_executed"] == 20
        assert a["trust_score"] == 0.95

    def test_preserves_existing_status(self):
        """Per GAP-AGENT-PAUSE-001: existing in-memory status preserved."""
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent()]
        agents_store = {"code-agent": {"status": "ACTIVE"}}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        assert agents_store["code-agent"]["status"] == "ACTIVE"

    def test_default_status_paused(self):
        """New agents default to PAUSED."""
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent(id="new-agent")]
        agents_store = {}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        assert agents_store["new-agent"]["status"] == "PAUSED"

    def test_default_trust_score(self):
        """Null trust_score defaults to 0.8."""
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent(trust_score=None)]
        agents_store = {}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        assert agents_store["code-agent"]["trust_score"] == 0.8

    def test_skip_agents_when_none(self):
        """When agents_store is None, skip agent sync."""
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        sync_typedb_to_memory(client, {}, {}, None)
        client.get_all_agents.assert_not_called()

    def test_agent_sync_error_isolated(self):
        """Agent sync error doesn't affect tasks/sessions."""
        client = MagicMock()
        client.get_all_tasks.return_value = [_FakeTask()]
        client.get_all_sessions.return_value = [_FakeSession()]
        client.get_all_agents.side_effect = Exception("Agent DB error")
        tasks_store, sessions_store, agents_store = {}, {}, {}
        sync_typedb_to_memory(client, tasks_store, sessions_store, agents_store)
        assert len(tasks_store) == 1
        assert len(sessions_store) == 1
        assert len(agents_store) == 0

    def test_last_active_is_none(self):
        """last_active is always None (loaded separately)."""
        client = MagicMock()
        client.get_all_tasks.return_value = []
        client.get_all_sessions.return_value = []
        client.get_all_agents.return_value = [_FakeAgent()]
        agents_store = {}
        sync_typedb_to_memory(client, {}, {}, agents_store)
        assert agents_store["code-agent"]["last_active"] is None
