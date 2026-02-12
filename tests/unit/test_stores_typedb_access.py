"""
Unit tests for Governance Stores TypeDB Data Access Functions.

Per DOC-SIZE-01-v1: Tests for stores/typedb_access.py module.
Tests: get_all_tasks_from_typedb, get_task_from_typedb,
       get_all_sessions_from_typedb, get_session_from_typedb,
       get_task_count, get_session_count, _task_to_dict, _session_to_dict.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

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


_P_CLIENT = "governance.stores.typedb_access.get_typedb_client"
_P_TASKS = "governance.stores.typedb_access._tasks_store"
_P_SESSIONS = "governance.stores.typedb_access._sessions_store"


def _make_task(task_id="T-1", name="Test", status="OPEN", phase="P1",
               agent_id=None, body=None, evidence=None):
    t = MagicMock()
    t.id = task_id
    t.name = name
    t.status = status
    t.phase = phase
    t.agent_id = agent_id
    t.body = body
    t.description = name
    t.evidence = evidence
    t.created_at = None
    t.claimed_at = None
    t.completed_at = None
    t.linked_rules = None
    t.linked_sessions = None
    t.gap_id = None
    t.document_path = None
    return t


def _make_session(session_id="S-1", status="ACTIVE", agent_id=None,
                  description=None):
    s = MagicMock()
    s.id = session_id
    s.status = status
    s.agent_id = agent_id
    s.description = description
    s.started_at = datetime(2026, 2, 11, 10, 0, 0)
    s.completed_at = None
    s.tasks_completed = 0
    s.file_path = None
    s.evidence_files = None
    s.linked_rules_applied = None
    s.linked_decisions = None
    return s


class TestTaskToDict:
    def test_basic(self):
        d = _task_to_dict(_make_task())
        assert d["task_id"] == "T-1"
        assert d["name"] == "Test"
        assert d["status"] == "OPEN"
        assert d["phase"] == "P1"

    def test_with_timestamps(self):
        t = _make_task()
        t.created_at = datetime(2026, 1, 1)
        t.completed_at = datetime(2026, 1, 2)
        d = _task_to_dict(t)
        assert d["created_at"] == "2026-01-01T00:00:00"
        assert d["completed_at"] == "2026-01-02T00:00:00"

    def test_description_fallback(self):
        t = _make_task(body="Body text")
        d = _task_to_dict(t)
        assert d["description"] == "Body text"


class TestSessionToDict:
    def test_basic(self):
        d = _session_to_dict(_make_session())
        assert d["session_id"] == "S-1"
        assert d["status"] == "ACTIVE"
        assert d["start_time"] == "2026-02-11T10:00:00"

    def test_with_completed(self):
        s = _make_session()
        s.completed_at = datetime(2026, 2, 11, 12, 0, 0)
        d = _session_to_dict(s)
        assert d["end_time"] == "2026-02-11T12:00:00"


class TestGetAllTasks:
    def test_from_typedb(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_make_task()]
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TASKS, {}):
            tasks = get_all_tasks_from_typedb()
        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "T-1"

    def test_typedb_unavailable_raises(self):
        with patch(_P_CLIENT, return_value=None):
            with pytest.raises(TypeDBUnavailable):
                get_all_tasks_from_typedb(allow_fallback=False)

    def test_fallback_to_memory(self):
        store = {"T-1": {"task_id": "T-1", "status": "OPEN", "phase": "P1"}}
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_TASKS, store):
            tasks = get_all_tasks_from_typedb(allow_fallback=True)
        assert len(tasks) == 1

    def test_fallback_filters(self):
        store = {
            "T-1": {"task_id": "T-1", "status": "OPEN", "phase": "P1"},
            "T-2": {"task_id": "T-2", "status": "DONE", "phase": "P1"},
        }
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_TASKS, store):
            tasks = get_all_tasks_from_typedb(allow_fallback=True, status="OPEN")
        assert len(tasks) == 1

    def test_merges_evidence(self):
        client = MagicMock()
        task = _make_task(evidence=None)
        client.get_all_tasks.return_value = [task]
        store = {"T-1": {"evidence": "Evidence from memory"}}

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TASKS, store):
            tasks = get_all_tasks_from_typedb()
        assert tasks[0]["evidence"] == "Evidence from memory"


class TestGetTask:
    def test_from_typedb(self):
        client = MagicMock()
        client.get_task.return_value = _make_task()
        with patch(_P_CLIENT, return_value=client):
            task = get_task_from_typedb("T-1")
        assert task["task_id"] == "T-1"

    def test_not_found(self):
        client = MagicMock()
        client.get_task.return_value = None
        with patch(_P_CLIENT, return_value=client):
            task = get_task_from_typedb("NONEXISTENT")
        assert task is None

    def test_fallback(self):
        store = {"T-1": {"task_id": "T-1"}}
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_TASKS, store):
            task = get_task_from_typedb("T-1", allow_fallback=True)
        assert task["task_id"] == "T-1"

    def test_raises_without_fallback(self):
        with patch(_P_CLIENT, return_value=None):
            with pytest.raises(TypeDBUnavailable):
                get_task_from_typedb("T-1", allow_fallback=False)


class TestGetAllSessions:
    def test_from_typedb(self):
        client = MagicMock()
        client.get_all_sessions.return_value = [_make_session()]
        with patch(_P_CLIENT, return_value=client):
            sessions = get_all_sessions_from_typedb()
        assert len(sessions) == 1

    def test_fallback(self):
        store = {"S-1": {"session_id": "S-1"}}
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_SESSIONS, store):
            sessions = get_all_sessions_from_typedb(allow_fallback=True)
        assert len(sessions) == 1


class TestGetSession:
    def test_from_typedb(self):
        client = MagicMock()
        client.get_session.return_value = _make_session()
        with patch(_P_CLIENT, return_value=client):
            session = get_session_from_typedb("S-1")
        assert session["session_id"] == "S-1"

    def test_not_found(self):
        client = MagicMock()
        client.get_session.return_value = None
        with patch(_P_CLIENT, return_value=client):
            session = get_session_from_typedb("S-1")
        assert session is None


class TestCounts:
    def test_task_count(self):
        client = MagicMock()
        client.get_all_tasks.return_value = [_make_task(), _make_task()]
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_TASKS, {}):
            assert get_task_count() == 2

    def test_session_count(self):
        client = MagicMock()
        client.get_all_sessions.return_value = [_make_session()]
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_SESSIONS, {}):
            assert get_session_count() == 1

    def test_count_zero_on_unavailable(self):
        with patch(_P_CLIENT, return_value=None), \
             patch(_P_TASKS, {}):
            assert get_task_count(allow_fallback=True) == 0
