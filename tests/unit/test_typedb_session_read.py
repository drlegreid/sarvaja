"""
Unit tests for TypeDB Session Read Queries.

Per DOC-SIZE-01-v1: Tests for typedb/queries/sessions/read.py module.
Tests: get_all_sessions, get_session, _build_session_from_id,
       _batch_fetch_session_attributes, _batch_fetch_session_relationships,
       get_tasks_for_session.
"""

from unittest.mock import MagicMock

import pytest

from governance.typedb.queries.sessions.read import SessionReadQueries


class _ConcreteSessionReader(SessionReadQueries):
    def __init__(self):
        self._execute_query = MagicMock(return_value=[])
        self._driver = MagicMock()
        self.database = "test-db"
        self._connected = True
        self._query_count = 0
        self._total_query_ms = 0.0

    def _record_query_timing(self, t0, query):
        pass


@pytest.fixture()
def reader():
    return _ConcreteSessionReader()


class TestGetAllSessions:
    def test_returns_sessions(self, reader):
        reader._execute_query.return_value = [
            {"id": "SESSION-2026-02-11-TEST"},
            {"id": "SESSION-2026-02-10-WORK"},
        ]
        sessions = reader.get_all_sessions()
        assert len(sessions) == 2
        assert sessions[0].id == "SESSION-2026-02-11-TEST"

    def test_empty(self, reader):
        reader._execute_query.return_value = []
        assert reader.get_all_sessions() == []

    def test_skips_none_ids(self, reader):
        reader._execute_query.return_value = [
            {"id": "SESSION-2026-02-11-TEST"},
            {"id": None},
        ]
        sessions = reader.get_all_sessions()
        assert len(sessions) == 1


class TestBatchFetchAttributes:
    def test_sets_name_and_description(self, reader):
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        call_count = [0]
        def _mock(q):
            call_count[0] += 1
            if "session-name" in q:
                return [{"id": "S-1", "v": "Test Session"}]
            if "session-description" in q:
                return [{"id": "S-1", "v": "Description here"}]
            if "completed-at" in q:
                return [{"id": "S-1", "v": "2026-02-11T12:00:00"}]
            return []
        reader._execute_query.side_effect = _mock

        reader._batch_fetch_session_attributes(session_map)
        assert session_map["S-1"].name == "Test Session"
        assert session_map["S-1"].description == "Description here"
        assert session_map["S-1"].status == "COMPLETED"

    def test_unknown_when_no_completed_at_and_no_started_at(self, reader):
        """BUG-SESSIONS-ONGOING-001: Sessions without completed-at and no started_at get UNKNOWN."""
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        reader._execute_query.return_value = []
        reader._batch_fetch_session_attributes(session_map)
        assert session_map["S-1"].status == "UNKNOWN"

    def test_active_when_no_completed_at_but_has_started_at(self, reader):
        """Sessions without completed-at but WITH started_at remain ACTIVE."""
        from governance.typedb.entities import Session
        session = Session(id="S-1")
        session.started_at = "2026-02-11T08:00:00"
        session_map = {"S-1": session}

        reader._execute_query.return_value = []
        reader._batch_fetch_session_attributes(session_map)
        assert session_map["S-1"].status == "ACTIVE"

    def test_error_resilience(self, reader):
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        reader._execute_query.side_effect = Exception("TypeDB down")
        # Should not raise; keeps entity default ("ACTIVE")
        # The merge layer corrects status from _sessions_store
        reader._batch_fetch_session_attributes(session_map)
        assert session_map["S-1"].status == "ACTIVE"


class TestBatchFetchRelationships:
    def test_sets_rules_and_decisions(self, reader):
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        call_count = [0]
        def _mock(q):
            call_count[0] += 1
            if "session-applied-rule" in q:
                return [{"sid": "S-1", "rid": "RULE-001"}]
            if "session-decision" in q:
                return [{"sid": "S-1", "did": "DECISION-001"}]
            return []
        reader._execute_query.side_effect = _mock

        reader._batch_fetch_session_relationships(session_map)
        assert session_map["S-1"].linked_rules_applied == ["RULE-001"]
        assert session_map["S-1"].linked_decisions == ["DECISION-001"]

    def test_sets_evidence_files(self, reader):
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        def _mock(q):
            if "has-evidence" in q:
                return [{"sid": "S-1", "src": "evidence/file.md"}]
            return []
        reader._execute_query.side_effect = _mock

        reader._batch_fetch_session_relationships(session_map)
        assert session_map["S-1"].evidence_files == ["evidence/file.md"]

    def test_sets_task_count(self, reader):
        from governance.typedb.entities import Session
        session_map = {"S-1": Session(id="S-1")}

        def _mock(q):
            if "completed-in" in q:
                return [{"sid": "S-1", "t": "T1"}, {"sid": "S-1", "t": "T2"}]
            return []
        reader._execute_query.side_effect = _mock

        reader._batch_fetch_session_relationships(session_map)
        assert session_map["S-1"].tasks_completed == 2


class TestGetSession:
    def test_found(self, reader):
        # Override consolidated attr/relation fetchers
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-name": "Test",
        })
        reader._fetch_session_relations_batch = MagicMock()
        session = reader.get_session("SESSION-2026-02-11-TEST")
        assert session is not None
        assert session.id == "SESSION-2026-02-11-TEST"

    def test_not_found(self, reader):
        reader._fetch_all_session_attrs = MagicMock(return_value=None)
        session = reader.get_session("NONEXISTENT")
        assert session is None


class TestGetTasksForSession:
    def test_returns_tasks(self, reader):
        reader._execute_query.return_value = [
            {"tid": "T-1", "name": "Task 1", "status": "DONE"},
            {"tid": "T-2", "name": "Task 2", "status": "IN_PROGRESS"},
        ]
        tasks = reader.get_tasks_for_session("S-1")
        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "T-1"
        assert tasks[1]["status"] == "IN_PROGRESS"

    def test_empty(self, reader):
        reader._execute_query.return_value = []
        assert reader.get_tasks_for_session("S-1") == []
