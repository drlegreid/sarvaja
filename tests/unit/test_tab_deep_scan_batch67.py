"""
Batch 67 — Deep Scan: Session CRUD + Task status escaping.

Fixes verified:
- BUG-TYPEQL-ESCAPE-SESSION-004: session_id + cc_session_uuid escaped in insert_session/end_session
- BUG-TYPEQL-ESCAPE-TASK-003: task_id escaped in all update_task_status queries
"""
import inspect
import re

import pytest


# ===========================================================================
# BUG-TYPEQL-ESCAPE-SESSION-004: Session insert + end escaping
# ===========================================================================

class TestSessionInsertEscaping:
    """Verify session_id escaped in session insert/end queries."""

    def test_insert_session_escapes_session_id(self):
        """insert_session must escape session_id."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        assert "session_id_escaped" in src or "session_id.replace(" in src

    def test_insert_session_escapes_cc_uuid(self):
        """insert_session must escape cc_session_uuid."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        assert "uuid_esc" in src or "cc_session_uuid.replace(" in src

    def test_end_session_escapes_session_id(self):
        """end_session must escape session_id."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.end_session)
        assert '.replace(' in src

    def test_no_raw_session_id_in_insert(self):
        """insert_session must not have raw session_id in insert_parts."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        raw = re.findall(r'session-id "\{session_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped session_id in insert"

    def test_no_raw_session_id_in_end(self):
        """end_session must not have raw session_id in query."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.end_session)
        raw = re.findall(r'session-id "\{session_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped session_id in end"

    def test_insert_session_total_escapes(self):
        """insert_session must have comprehensive escaping."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations.insert_session)
        escape_count = src.count('.replace(')
        assert escape_count >= 6, f"Expected 6+ escape calls, found {escape_count}"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-TASK-003: Task status update escaping
# ===========================================================================

class TestTaskStatusEscaping:
    """Verify task_id escaped in all task status update queries."""

    def test_status_update_escapes_task_id(self):
        """update_task_status must escape task_id."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert 'task_id.replace(' in src or "tid = task_id" in src

    def test_status_update_escapes_status(self):
        """update_task_status must escape status value."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "status_escaped" in src

    def test_no_raw_task_id_in_status(self):
        """update_task_status must not have raw task_id in any query."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        raw = re.findall(r'task-id "\{task_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped task_id in status queries"

    def test_escaped_tid_used_in_all_queries(self):
        """All f-string queries must use escaped tid variable."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        escaped = re.findall(r'task-id "\{tid\}"', src)
        assert len(escaped) >= 10, f"Expected 10+ escaped tid uses, found {len(escaped)}"

    def test_agent_id_escaped_in_status(self):
        """update_task_status must escape agent_id."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "agent_id_escaped" in src

    def test_evidence_escaped_in_status(self):
        """update_task_status must escape evidence."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "evidence_escaped" in src

    def test_resolution_escaped_in_status(self):
        """update_task_status must escape resolution."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "resolution_escaped" in src

    def test_total_escape_calls(self):
        """update_task_status must have comprehensive escaping."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        escape_count = src.count('.replace(')
        assert escape_count >= 7, f"Expected 7+ escape calls, found {escape_count}"


# ===========================================================================
# Cross-file: Full TypeDB layer escaping completeness
# ===========================================================================

class TestFullTypeDBEscapingAudit:
    """Final audit: ALL TypeDB query files must have comprehensive escaping."""

    def test_sessions_crud_escaping(self):
        """SessionCRUDOperations must escape in both insert and end."""
        from governance.typedb.queries.sessions.crud import SessionCRUDOperations
        src = inspect.getsource(SessionCRUDOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 7, f"Expected 7+ in crud, found {escape_count}"

    def test_sessions_mutations_escaping(self):
        """SessionMutationOperations must have comprehensive escaping."""
        from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations
        src = inspect.getsource(SessionMutationOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 5, f"Expected 5+ in mutations, found {escape_count}"

    def test_sessions_linking_escaping(self):
        """SessionLinkingOperations must have comprehensive escaping."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 8, f"Expected 8+ in linking, found {escape_count}"

    def test_sessions_read_escaping(self):
        """SessionReadQueries must have comprehensive escaping."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 3, f"Expected 3+ in read, found {escape_count}"

    def test_tasks_status_escaping(self):
        """update_task_status must have comprehensive escaping."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        escape_count = src.count('.replace(')
        assert escape_count >= 7, f"Expected 7+ in status, found {escape_count}"

    def test_agents_escaping(self):
        """AgentQueries must have comprehensive escaping."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 6, f"Expected 6+ in agents, found {escape_count}"
