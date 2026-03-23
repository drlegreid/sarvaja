"""
TDD tests for EPIC-TASK-QUALITY-V3 Phase 11: MCP Data Integrity Hardening.

Per TEST-FIX-01-v1: Failing tests written FIRST, then implementation.

Bugs:
- SRVJ-BUG-018: agent_id not persisted through update_task()
- SRVJ-BUG-019: created_at reads null / AttributeError on string datetime
- SRVJ-BUG-020: link_task_to_rule creates duplicates (no idempotency guard)
"""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Mock typedb.driver for in-function imports
_mock_typedb_driver = MagicMock()
_mock_typedb_driver.TransactionType.WRITE = "write"
_mock_typedb_driver.TransactionType.READ = "read"


@pytest.fixture(autouse=True)
def _mock_typedb():
    with patch.dict(sys.modules, {
        "typedb": MagicMock(),
        "typedb.driver": _mock_typedb_driver,
    }):
        yield


from governance.typedb.queries.tasks.crud import TaskCRUDOperations, _ALLOWED_TASK_ATTR_NAMES
from governance.typedb.queries.tasks.linking import TaskLinkingOperations
from governance.typedb.entities import Task
from governance.stores.helpers import task_to_response


# ============================================================================
# Test fixtures
# ============================================================================

class _CRUDClient(TaskCRUDOperations):
    """Concrete class for testing CRUD mixin."""
    def __init__(self):
        self._driver = MagicMock()
        self._execute_query = MagicMock(return_value=[])
        self.database = "test-db"
        self._mock_tasks = {}

    def get_task(self, task_id):
        return self._mock_tasks.get(task_id)


class _LinkClient(TaskLinkingOperations):
    """Concrete class for testing linking mixin."""
    def __init__(self):
        self._driver = MagicMock()
        self.database = "test-db"
        self._query_results = []

    def _execute_query(self, query):
        return self._query_results

    def _setup_tx(self):
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = iter([])
        tx.query.return_value = query_result
        self._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        self._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return tx


@pytest.fixture()
def crud():
    c = _CRUDClient()
    tx = MagicMock()
    tx.query.return_value = MagicMock(resolve=MagicMock())
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=tx)
    ctx.__exit__ = MagicMock(return_value=False)
    c._driver.transaction.return_value = ctx
    c._tx = tx
    return c


# ============================================================================
# SRVJ-BUG-018: agent_id persistence through update_task()
# ============================================================================

class TestBug018AgentIdPersistence:
    """SRVJ-BUG-018: update_task() must accept and persist agent_id to TypeDB."""

    def test_update_task_accepts_agent_id_param(self, crud):
        """update_task() must accept agent_id as a keyword argument."""
        task = Task(id="T-1", name="Test", status="IN_PROGRESS", phase="P11")
        task.agent_id = None
        crud._mock_tasks["T-1"] = task
        # This should NOT raise TypeError
        result = crud.update_task("T-1", agent_id="code-agent")
        assert result is True

    def test_update_task_writes_agent_id_to_typedb(self, crud):
        """update_task() must write agent-id attribute to TypeDB."""
        task = Task(id="T-1", name="Test", status="IN_PROGRESS", phase="P11")
        task.agent_id = None
        crud._mock_tasks["T-1"] = task
        crud.update_task("T-1", agent_id="code-agent")
        # Check that agent-id appears in one of the TypeQL queries
        queries = [c[0][0] for c in crud._tx.query.call_args_list]
        agent_queries = [q for q in queries if "agent-id" in q]
        assert len(agent_queries) >= 1, "agent-id must be written to TypeDB"
        assert any('"code-agent"' in q for q in agent_queries)

    def test_update_task_replaces_existing_agent_id(self, crud):
        """update_task() must delete old agent-id before inserting new one."""
        task = Task(id="T-1", name="Test", status="IN_PROGRESS", phase="P11")
        task.agent_id = "old-agent"
        crud._mock_tasks["T-1"] = task
        crud.update_task("T-1", agent_id="new-agent")
        queries = [c[0][0] for c in crud._tx.query.call_args_list]
        # Should have a delete and an insert for agent-id
        deletes = [q for q in queries if "delete" in q.lower() and "agent-id" in q]
        inserts = [q for q in queries if "insert" in q.lower() and "agent-id" in q]
        assert len(deletes) >= 1, "Must delete old agent-id"
        assert len(inserts) >= 1, "Must insert new agent-id"

    def test_agent_id_in_allowed_attr_names(self):
        """agent-id must be in the _ALLOWED_TASK_ATTR_NAMES allowlist."""
        assert "agent-id" in _ALLOWED_TASK_ATTR_NAMES

    def test_service_update_passes_agent_id_to_client(self):
        """Service layer update_task() must pass agent_id to client.update_task()."""
        mock_client = MagicMock()
        mock_task = Task(id="T-1", name="Test", status="IN_PROGRESS", phase="P11")
        mock_task.agent_id = None
        mock_task.created_at = datetime(2026, 1, 1)
        mock_client.get_task.return_value = mock_task
        mock_client.update_task.return_value = True
        mock_client.update_task_status.return_value = mock_task

        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations.log_event"), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations._monitor"):
            from governance.services.tasks_mutations import update_task
            update_task("T-1", agent_id="code-agent", status="IN_PROGRESS", source="test")

        # client.update_task must have been called WITH agent_id
        if mock_client.update_task.called:
            _, kwargs = mock_client.update_task.call_args
            assert kwargs.get("agent_id") == "code-agent", \
                "agent_id must be passed to client.update_task()"

    def test_h_task_002_auto_agent_id_reaches_typedb(self):
        """H-TASK-002 auto-assigned agent_id must be passed to TypeDB writes.

        Root cause: H-TASK-002 ran AFTER TypeDB writes, so auto-assigned
        agent_id only went to _tasks_store (in-memory), never to TypeDB.
        Fix: moved H-TASK-002 before TypeDB writes.
        """
        mock_client = MagicMock()
        mock_task = Task(id="T-1", name="Test", status="OPEN", phase="P11")
        mock_task.agent_id = None
        mock_task.created_at = datetime(2026, 1, 1)
        mock_client.get_task.return_value = mock_task
        mock_client.update_task_status.return_value = mock_task

        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations.log_event"), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations._monitor"):
            from governance.services.tasks_mutations import update_task
            # Simulate MCP path: status=IN_PROGRESS, no explicit agent_id
            update_task("T-1", status="IN_PROGRESS", source="mcp")

        # update_task_status must receive "code-agent" (auto-assigned)
        mock_client.update_task_status.assert_called_once()
        call_args = mock_client.update_task_status.call_args
        # Args: (task_id, status, agent_id, evidence=...)
        actual_agent = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("agent_id")
        assert actual_agent == "code-agent", \
            f"H-TASK-002 auto-assigned agent_id must reach TypeDB, got: {actual_agent}"


# ============================================================================
# SRVJ-BUG-019: created_at null read-back / string handling
# ============================================================================

class TestBug019CreatedAtReadBack:
    """SRVJ-BUG-019: task_to_response must handle string and datetime created_at."""

    def test_task_to_response_handles_string_created_at(self):
        """task_to_response() must not crash when created_at is a string."""
        task = Task(id="T-1", name="Test", status="OPEN", phase="P11")
        task.created_at = "2026-03-23T10:00:00"
        response = task_to_response(task)
        assert response.created_at is not None
        assert "2026-03-23" in response.created_at

    def test_task_to_response_handles_datetime_created_at(self):
        """task_to_response() must handle datetime created_at (existing behavior)."""
        task = Task(id="T-1", name="Test", status="OPEN", phase="P11")
        task.created_at = datetime(2026, 3, 23, 10, 0, 0)
        response = task_to_response(task)
        assert response.created_at is not None
        assert "2026-03-23" in response.created_at

    def test_task_to_response_handles_none_created_at(self):
        """task_to_response() must return None when created_at is None."""
        task = Task(id="T-1", name="Test", status="OPEN", phase="P11")
        task.created_at = None
        response = task_to_response(task)
        assert response.created_at is None

    def test_task_to_response_handles_string_claimed_at(self):
        """Defensive handling for string claimed_at too."""
        task = Task(id="T-1", name="Test", status="IN_PROGRESS", phase="P11")
        task.claimed_at = "2026-03-23T10:00:00"
        response = task_to_response(task)
        assert response.claimed_at is not None
        assert "2026-03-23" in response.claimed_at

    def test_task_to_response_handles_string_completed_at(self):
        """Defensive handling for string completed_at too."""
        task = Task(id="T-1", name="Test", status="DONE", phase="P11")
        task.completed_at = "2026-03-23T12:00:00"
        response = task_to_response(task)
        assert response.completed_at is not None
        assert "2026-03-23" in response.completed_at

    def test_batch_fetch_created_at_sets_value(self):
        """_batch_fetch_task_attributes must set created_at on task objects."""
        from governance.typedb.queries.tasks.read import TaskReadQueries

        class _ReadClient(TaskReadQueries):
            def __init__(self):
                pass

            def _execute_query(self, query):
                if "task-created-at" in query:
                    return [{"id": "T-1", "v": "2026-03-23T10:00:00"}]
                return []

            def _safe_query(self, query):
                return self._execute_query(query)

        reader = _ReadClient()
        task = Task(id="T-1", name="Test", status="OPEN", phase="P11")
        task_map = {"T-1": task}
        reader._batch_fetch_task_attributes(task_map)
        assert task.created_at is not None, "created_at must be set by batch fetch"


# ============================================================================
# SRVJ-BUG-020: link_task_to_rule idempotency
# ============================================================================

class TestBug020LinkTaskToRuleIdempotency:
    """SRVJ-BUG-020: link_task_to_rule must be idempotent (no duplicates)."""

    def test_link_task_to_rule_checks_existing_before_insert(self):
        """link_task_to_rule must check for existing relation before INSERT."""
        linker = _LinkClient()
        tx = linker._setup_tx()
        linker.link_task_to_rule("T-1", "TEST-E2E-01-v1")
        queries = [c[0][0] for c in tx.query.call_args_list]
        # Must have at least one MATCH that checks implements-rule existence
        existence_checks = [
            q for q in queries
            if "implements-rule" in q and "match" in q.lower()
            and "insert" not in q.lower()
        ]
        assert len(existence_checks) >= 1, \
            "Must check for existing implements-rule relation before INSERT"

    def test_link_task_to_rule_skips_insert_if_exists(self):
        """If relation already exists, link_task_to_rule must skip INSERT."""
        linker = _LinkClient()
        tx = linker._setup_tx()
        # First call: existence check returns a result (relation exists)
        existing_result = MagicMock()
        existing_result.resolve.return_value = iter([MagicMock()])
        # Second call would be INSERT (should not happen)
        insert_result = MagicMock()
        insert_result.resolve.return_value = None
        tx.query.side_effect = [existing_result, insert_result]

        result = linker.link_task_to_rule("T-1", "R-1")
        assert result is True
        # Should only have 1 query (the existence check), not 2
        queries = [c[0][0] for c in tx.query.call_args_list]
        insert_queries = [q for q in queries if "insert" in q.lower()]
        assert len(insert_queries) == 0, \
            "Must NOT insert when relation already exists"

    def test_link_task_to_rule_inserts_when_not_exists(self):
        """If no existing relation, link_task_to_rule must INSERT."""
        linker = _LinkClient()
        tx = linker._setup_tx()
        # First call: existence check returns empty (no existing relation)
        check_result = MagicMock()
        check_result.resolve.return_value = iter([])
        # Second call: INSERT
        insert_result = MagicMock()
        insert_result.resolve.return_value = None
        tx.query.side_effect = [check_result, insert_result]

        result = linker.link_task_to_rule("T-1", "R-1")
        assert result is True
        queries = [c[0][0] for c in tx.query.call_args_list]
        insert_queries = [q for q in queries if "insert" in q.lower()]
        assert len(insert_queries) == 1, "Must INSERT when no existing relation"
