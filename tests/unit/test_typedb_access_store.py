"""Tests for governance/stores/typedb_access.py — TypeDB data access functions.

Covers: get_all_tasks_from_typedb, get_task_from_typedb,
get_all_sessions_from_typedb, get_session_from_typedb,
get_task_count, get_session_count, _task_to_dict, _session_to_dict.
"""

import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.stores.typedb_access import (
    get_all_tasks_from_typedb,
    get_task_from_typedb,
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    get_task_count,
    get_session_count,
    _task_to_dict,
    _session_to_dict,
)
from governance.stores.data_stores import TypeDBUnavailable


def _make_mock_task(**overrides):
    """Create a mock TypeDB Task entity."""
    task = MagicMock()
    task.id = overrides.get("id", "TASK-001")
    task.name = overrides.get("name", "Test Task")
    task.description = overrides.get("description", "A test task")
    task.body = overrides.get("body", None)
    task.phase = overrides.get("phase", "P10")
    task.status = overrides.get("status", "OPEN")
    task.agent_id = overrides.get("agent_id", None)
    task.created_at = overrides.get("created_at", datetime(2026, 2, 13, 10, 0))
    task.claimed_at = overrides.get("claimed_at", None)
    task.completed_at = overrides.get("completed_at", None)
    task.linked_rules = overrides.get("linked_rules", [])
    task.linked_sessions = overrides.get("linked_sessions", [])
    task.gap_id = overrides.get("gap_id", None)
    task.evidence = overrides.get("evidence", None)
    task.document_path = overrides.get("document_path", None)
    return task


def _make_mock_session(**overrides):
    """Create a mock TypeDB Session entity."""
    s = MagicMock()
    s.id = overrides.get("id", "SESSION-2026-02-13-TEST")
    s.started_at = overrides.get("started_at", datetime(2026, 2, 13, 9, 0))
    s.completed_at = overrides.get("completed_at", None)
    s.status = overrides.get("status", "ACTIVE")
    s.tasks_completed = overrides.get("tasks_completed", 0)
    s.agent_id = overrides.get("agent_id", "code-agent")
    s.description = overrides.get("description", "Test session")
    s.file_path = overrides.get("file_path", None)
    s.evidence_files = overrides.get("evidence_files", [])
    s.linked_rules_applied = overrides.get("linked_rules_applied", [])
    s.linked_decisions = overrides.get("linked_decisions", [])
    s.cc_session_uuid = overrides.get("cc_session_uuid", None)
    s.cc_project_slug = overrides.get("cc_project_slug", None)
    s.cc_git_branch = overrides.get("cc_git_branch", None)
    s.cc_tool_count = overrides.get("cc_tool_count", None)
    s.cc_thinking_chars = overrides.get("cc_thinking_chars", None)
    s.cc_compaction_count = overrides.get("cc_compaction_count", None)
    s.project_id = overrides.get("project_id", None)
    return s


class TestTaskToDict(unittest.TestCase):
    """Tests for _task_to_dict conversion."""

    def test_basic_conversion(self):
        task = _make_mock_task()
        d = _task_to_dict(task)
        self.assertEqual(d["task_id"], "TASK-001")
        self.assertEqual(d["name"], "Test Task")
        self.assertEqual(d["phase"], "P10")
        self.assertEqual(d["status"], "OPEN")
        self.assertIsNone(d["agent_id"])

    def test_body_overrides_description(self):
        """Per GAP-DATA-001: body > description > name."""
        task = _make_mock_task(body="Detailed body", description="Short desc")
        d = _task_to_dict(task)
        self.assertEqual(d["description"], "Detailed body")

    def test_description_fallback_to_name(self):
        task = _make_mock_task(body=None, description=None, name="Task Name")
        d = _task_to_dict(task)
        self.assertEqual(d["description"], "Task Name")

    def test_timestamps_iso(self):
        now = datetime(2026, 2, 13, 12, 30)
        task = _make_mock_task(created_at=now, claimed_at=now, completed_at=now)
        d = _task_to_dict(task)
        self.assertEqual(d["created_at"], "2026-02-13T12:30:00")
        self.assertEqual(d["claimed_at"], "2026-02-13T12:30:00")
        self.assertEqual(d["completed_at"], "2026-02-13T12:30:00")

    def test_none_timestamps(self):
        task = _make_mock_task(created_at=None, claimed_at=None, completed_at=None)
        d = _task_to_dict(task)
        self.assertIsNone(d["created_at"])
        self.assertIsNone(d["claimed_at"])

    def test_linked_fields(self):
        task = _make_mock_task(
            linked_rules=["R-1", "R-2"],
            linked_sessions=["S-1"],
            gap_id="GAP-001",
        )
        d = _task_to_dict(task)
        self.assertEqual(d["linked_rules"], ["R-1", "R-2"])
        self.assertEqual(d["linked_sessions"], ["S-1"])
        self.assertEqual(d["gap_id"], "GAP-001")


class TestSessionToDict(unittest.TestCase):
    """Tests for _session_to_dict conversion."""

    def test_basic_conversion(self):
        s = _make_mock_session()
        d = _session_to_dict(s)
        self.assertEqual(d["session_id"], "SESSION-2026-02-13-TEST")
        self.assertEqual(d["status"], "ACTIVE")
        self.assertEqual(d["agent_id"], "code-agent")
        self.assertEqual(d["tasks_completed"], 0)

    def test_start_time_iso(self):
        s = _make_mock_session(started_at=datetime(2026, 1, 15, 8, 0))
        d = _session_to_dict(s)
        self.assertEqual(d["start_time"], "2026-01-15T08:00:00")

    def test_start_time_none_fallback(self):
        s = _make_mock_session(started_at=None)
        d = _session_to_dict(s)
        # Should use datetime.now() fallback
        self.assertIsNotNone(d["start_time"])

    def test_end_time_none(self):
        s = _make_mock_session(completed_at=None)
        d = _session_to_dict(s)
        self.assertIsNone(d["end_time"])

    def test_cc_attributes(self):
        s = _make_mock_session(
            cc_session_uuid="uuid-123",
            cc_project_slug="sarvaja",
            cc_git_branch="master",
            cc_tool_count=50,
            cc_thinking_chars=10000,
            cc_compaction_count=2,
            project_id="proj-1",
        )
        d = _session_to_dict(s)
        self.assertEqual(d["cc_session_uuid"], "uuid-123")
        self.assertEqual(d["cc_project_slug"], "sarvaja")
        self.assertEqual(d["cc_git_branch"], "master")
        self.assertEqual(d["cc_tool_count"], 50)
        self.assertEqual(d["project_id"], "proj-1")

    def test_tasks_completed_zero(self):
        s = _make_mock_session(tasks_completed=None)
        d = _session_to_dict(s)
        self.assertEqual(d["tasks_completed"], 0)


class TestGetAllTasksFromTypedb(unittest.TestCase):
    """Tests for get_all_tasks_from_typedb."""

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_typedb_success(self, mock_get_client):
        client = MagicMock()
        task1 = _make_mock_task(id="T-1")
        task2 = _make_mock_task(id="T-2")
        client.get_all_tasks.return_value = [task1, task2]
        mock_get_client.return_value = client
        result = get_all_tasks_from_typedb()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["task_id"], "T-1")

    @patch("governance.stores.typedb_access._tasks_store", {"T-MEM": {"task_id": "T-MEM", "status": "OPEN"}})
    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_fallback_to_memory(self, mock_get_client):
        mock_get_client.return_value = None
        result = get_all_tasks_from_typedb(allow_fallback=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_id"], "T-MEM")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_raises_without_fallback(self, mock_get_client):
        mock_get_client.return_value = None
        with self.assertRaises(TypeDBUnavailable):
            get_all_tasks_from_typedb(allow_fallback=False)

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_exception_with_fallback(self, mock_get_client):
        client = MagicMock()
        client.get_all_tasks.side_effect = Exception("connection lost")
        mock_get_client.return_value = client
        with patch("governance.stores.typedb_access._tasks_store", {"T-FB": {"task_id": "T-FB", "phase": "P10"}}):
            result = get_all_tasks_from_typedb(allow_fallback=True)
        self.assertEqual(len(result), 1)

    @patch("governance.stores.typedb_access._tasks_store", {
        "T-1": {"task_id": "T-1", "status": "OPEN", "phase": "P10", "agent_id": None},
        "T-2": {"task_id": "T-2", "status": "DONE", "phase": "P11", "agent_id": "code-agent"},
    })
    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_fallback_filters(self, mock_get_client):
        mock_get_client.return_value = None
        result = get_all_tasks_from_typedb(status="DONE", allow_fallback=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_id"], "T-2")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_evidence_merge_from_memory(self, mock_get_client):
        """Per EPIC-DR-008: Evidence merged from in-memory store."""
        client = MagicMock()
        task = _make_mock_task(id="T-1", evidence=None)
        client.get_all_tasks.return_value = [task]
        mock_get_client.return_value = client
        with patch("governance.stores.typedb_access._tasks_store", {"T-1": {"evidence": "proof.md"}}):
            result = get_all_tasks_from_typedb()
        self.assertEqual(result[0]["evidence"], "proof.md")


class TestGetTaskFromTypedb(unittest.TestCase):
    """Tests for get_task_from_typedb."""

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_found(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = _make_mock_task(id="T-1")
        mock_get_client.return_value = client
        result = get_task_from_typedb("T-1")
        self.assertEqual(result["task_id"], "T-1")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_not_found(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = None
        mock_get_client.return_value = client
        result = get_task_from_typedb("T-MISSING")
        self.assertIsNone(result)

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_raises_without_fallback(self, mock_get_client):
        mock_get_client.return_value = None
        with self.assertRaises(TypeDBUnavailable):
            get_task_from_typedb("T-1", allow_fallback=False)

    @patch("governance.stores.typedb_access._tasks_store", {"T-1": {"task_id": "T-1"}})
    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_fallback(self, mock_get_client):
        mock_get_client.return_value = None
        result = get_task_from_typedb("T-1", allow_fallback=True)
        self.assertEqual(result["task_id"], "T-1")


class TestGetAllSessionsFromTypedb(unittest.TestCase):
    """Tests for get_all_sessions_from_typedb."""

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_typedb_success(self, mock_get_client):
        client = MagicMock()
        s1 = _make_mock_session(id="S-1")
        client.get_all_sessions.return_value = [s1]
        mock_get_client.return_value = client
        result = get_all_sessions_from_typedb()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], "S-1")
        self.assertEqual(result[0]["persistence_status"], "persisted")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_merges_orphan_sessions(self, mock_get_client):
        """Per Phase-1 Data Integrity: merges memory-only orphans."""
        client = MagicMock()
        s1 = _make_mock_session(id="S-1")
        client.get_all_sessions.return_value = [s1]
        mock_get_client.return_value = client
        mem_sessions = {
            "S-2": {"session_id": "S-2", "status": "ACTIVE"},
        }
        with patch("governance.stores.typedb_access._sessions_store", mem_sessions):
            result = get_all_sessions_from_typedb(allow_fallback=True)
        self.assertEqual(len(result), 2)
        orphan = [r for r in result if r["session_id"] == "S-2"][0]
        self.assertEqual(orphan["persistence_status"], "memory_only")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_no_orphan_merge_without_fallback(self, mock_get_client):
        client = MagicMock()
        client.get_all_sessions.return_value = [_make_mock_session(id="S-1")]
        mock_get_client.return_value = client
        with patch("governance.stores.typedb_access._sessions_store", {"S-2": {"session_id": "S-2"}}):
            result = get_all_sessions_from_typedb(allow_fallback=False)
        self.assertEqual(len(result), 1)

    @patch("governance.stores.typedb_access._sessions_store", {"S-M": {"session_id": "S-M"}})
    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_full_fallback(self, mock_get_client):
        mock_get_client.return_value = None
        result = get_all_sessions_from_typedb(allow_fallback=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["persistence_status"], "memory_only")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_raises_without_fallback(self, mock_get_client):
        mock_get_client.return_value = None
        with self.assertRaises(TypeDBUnavailable):
            get_all_sessions_from_typedb(allow_fallback=False)


class TestGetSessionFromTypedb(unittest.TestCase):
    """Tests for get_session_from_typedb."""

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_found(self, mock_get_client):
        client = MagicMock()
        client.get_session.return_value = _make_mock_session(id="S-1")
        mock_get_client.return_value = client
        result = get_session_from_typedb("S-1")
        self.assertEqual(result["session_id"], "S-1")

    @patch("governance.stores.typedb_access.get_typedb_client")
    def test_not_found(self, mock_get_client):
        client = MagicMock()
        client.get_session.return_value = None
        mock_get_client.return_value = client
        result = get_session_from_typedb("S-NOPE")
        self.assertIsNone(result)


class TestCounts(unittest.TestCase):
    """Tests for get_task_count and get_session_count."""

    @patch("governance.stores.typedb_access.get_all_tasks_from_typedb")
    def test_task_count(self, mock_get):
        mock_get.return_value = [{"task_id": "T-1"}, {"task_id": "T-2"}]
        self.assertEqual(get_task_count(), 2)

    @patch("governance.stores.typedb_access.get_all_tasks_from_typedb")
    def test_task_count_unavailable(self, mock_get):
        mock_get.side_effect = TypeDBUnavailable("down")
        self.assertEqual(get_task_count(), 0)

    @patch("governance.stores.typedb_access.get_all_sessions_from_typedb")
    def test_session_count(self, mock_get):
        mock_get.return_value = [{"session_id": "S-1"}]
        self.assertEqual(get_session_count(), 1)

    @patch("governance.stores.typedb_access.get_all_sessions_from_typedb")
    def test_session_count_unavailable(self, mock_get):
        mock_get.side_effect = TypeDBUnavailable("down")
        self.assertEqual(get_session_count(), 0)


if __name__ == "__main__":
    unittest.main()
