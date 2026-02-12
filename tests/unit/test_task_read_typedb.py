"""
Unit tests for TypeDB Task Read Queries.

Batch 126: Tests for governance/typedb/queries/tasks/read.py
- _safe_query: graceful error handling
- _fetch_task_attr: single attribute DRY helper
- _fetch_task_relation: relationship list DRY helper
- get_all_tasks: batch fetch with filters
- _batch_fetch_task_attributes: 14 optional attributes
- _batch_fetch_task_relationships: rules, sessions, commits
- _build_task_from_id: single task hydration
- get_task / get_available_tasks: convenience wrappers
"""

from unittest.mock import MagicMock

from governance.typedb.queries.tasks.read import TaskReadQueries


def _make_client(query_results=None):
    """Create a mock client with TaskReadQueries mixed in."""

    class MockClient(TaskReadQueries):
        pass

    client = MockClient()
    client._execute_query = MagicMock(return_value=query_results or [])
    return client


# ── _safe_query ──────────────────────────────────────────


class TestSafeQuery:
    """Tests for _safe_query() helper."""

    def test_returns_results(self):
        client = _make_client([{"id": "T-1"}])
        result = client._safe_query("match ...")
        assert len(result) == 1

    def test_exception_returns_empty(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=Exception("schema missing"))
        result = client._safe_query("match ...")
        assert result == []


# ── _fetch_task_attr ─────────────────────────────────────


class TestFetchTaskAttr:
    """Tests for _fetch_task_attr() helper."""

    def test_returns_value(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[{"body": "Task body text"}])
        result = client._fetch_task_attr("T-1", "task-body", "body")
        assert result == "Task body text"

    def test_no_results_returns_none(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[])
        result = client._fetch_task_attr("T-1", "task-body", "body")
        assert result is None

    def test_query_contains_task_id_and_attr(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[])
        client._fetch_task_attr("MY-TASK", "item-type", "itype")
        query = client._safe_query.call_args[0][0]
        assert "MY-TASK" in query
        assert "item-type" in query


# ── _fetch_task_relation ─────────────────────────────────


class TestFetchTaskRelation:
    """Tests for _fetch_task_relation() helper."""

    def test_returns_id_list(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[
            {"rid": "RULE-001"}, {"rid": "RULE-002"},
        ])
        result = client._fetch_task_relation(
            "T-1",
            'match $t has task-id "{task_id}"; select $rid;',
            "rid"
        )
        assert result == ["RULE-001", "RULE-002"]

    def test_empty_returns_none(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[])
        result = client._fetch_task_relation("T-1", "...", "rid")
        assert result is None

    def test_formats_task_id_in_query(self):
        client = _make_client()
        client._safe_query = MagicMock(return_value=[])
        client._fetch_task_relation("T-42", 'task-id "{task_id}"', "rid")
        query = client._safe_query.call_args[0][0]
        assert "T-42" in query


# ── get_all_tasks ────────────────────────────────────────


class TestGetAllTasks:
    """Tests for get_all_tasks() method."""

    def test_empty_results(self):
        client = _make_client([])
        assert client.get_all_tasks() == []

    def test_returns_task_objects(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "T-1", "name": "Task 1", "status": "OPEN", "phase": "P1"}],
            # _batch_fetch_task_attributes: 14 queries
            *[[] for _ in range(14)],
            # _batch_fetch_task_relationships: 3 queries
            [], [], [],
        ])

        tasks = client.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == "T-1"
        assert tasks[0].name == "Task 1"

    def test_status_filter(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "T-1", "name": "Task", "status": "CLOSED", "phase": "P1"}],
            *[[] for _ in range(17)],
        ])
        tasks = client.get_all_tasks(status="CLOSED")
        query = client._execute_query.call_args_list[0][0][0]
        assert 'has task-status "CLOSED"' in query

    def test_phase_filter(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [], *[[] for _ in range(17)],
        ])
        client.get_all_tasks(phase="P2")
        query = client._execute_query.call_args_list[0][0][0]
        assert 'has phase "P2"' in query

    def test_agent_id_filter(self):
        """agent_id filters post-fetch (not in TypeQL query)."""
        client = _make_client()

        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [
                    {"id": "T-1", "name": "A", "status": "OPEN", "phase": "P1"},
                    {"id": "T-2", "name": "B", "status": "OPEN", "phase": "P1"},
                ]
            # agent-id attr query
            if "agent-id" in q:
                return [{"id": "T-1", "v": "code-agent"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        tasks = client.get_all_tasks(agent_id="code-agent")
        assert len(tasks) == 1
        assert tasks[0].id == "T-1"

    def test_populates_optional_attributes(self):
        client = _make_client()

        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"id": "T-1", "name": "Task", "status": "OPEN", "phase": "P1"}]
            if "task-body" in q:
                return [{"id": "T-1", "v": "Body text"}]
            if "task-resolution" in q:
                return [{"id": "T-1", "v": "IMPLEMENTED"}]
            if "gap-reference" in q:
                return [{"id": "T-1", "v": "GAP-001"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        tasks = client.get_all_tasks()
        t = tasks[0]
        assert t.body == "Body text"
        assert t.resolution == "IMPLEMENTED"
        assert t.gap_id == "GAP-001"

    def test_populates_relationships(self):
        client = _make_client()

        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"id": "T-1", "name": "Task", "status": "OPEN", "phase": "P1"}]
            if "implements-rule" in q:
                return [{"tid": "T-1", "rid": "RULE-001"}]
            if "completed-in" in q:
                return [{"tid": "T-1", "sid": "S-1"}]
            if "task-commit" in q:
                return [{"tid": "T-1", "sha": "abc1234"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        tasks = client.get_all_tasks()
        t = tasks[0]
        assert "RULE-001" in t.linked_rules
        assert "S-1" in t.linked_sessions
        assert "abc1234" in t.linked_commits


# ── _build_task_from_id ──────────────────────────────────


class TestBuildTaskFromId:
    """Tests for _build_task_from_id() method."""

    def test_not_found(self):
        client = _make_client([])
        result = client._build_task_from_id("MISSING")
        assert result is None

    def test_minimal_task(self):
        client = _make_client()
        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"name": "Task", "status": "OPEN", "phase": "P1"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        task = client._build_task_from_id("T-1")
        assert task.id == "T-1"
        assert task.name == "Task"
        assert task.status == "OPEN"

    def test_fetches_optional_attrs(self):
        client = _make_client()

        def side_effect(q):
            if "task-name" in q and "task-status" in q:
                return [{"name": "Task", "status": "OPEN", "phase": "P1"}]
            if "task-body" in q:
                return [{"body": "Detailed body"}]
            if "agent-id" in q and "task-id" in q and "select" in q.lower():
                return [{"agent": "code-agent"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        task = client._build_task_from_id("T-1")
        assert task.body == "Detailed body"
        assert task.agent_id == "code-agent"

    def test_fetches_relationships(self):
        client = _make_client()

        def side_effect(q):
            if "task-name" in q and "task-status" in q:
                return [{"name": "Task", "status": "OPEN", "phase": "P1"}]
            if "implements-rule" in q:
                return [{"rid": "R-1"}]
            if "completed-in" in q:
                return [{"sid": "S-1"}]
            if "task-commit" in q:
                return [{"sha": "abc"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        task = client._build_task_from_id("T-1")
        assert task.linked_rules == ["R-1"]
        assert task.linked_sessions == ["S-1"]
        assert task.linked_commits == ["abc"]


# ── get_task ─────────────────────────────────────────────


class TestGetTask:
    """Tests for get_task() convenience method."""

    def test_delegates_to_build(self):
        client = _make_client()
        client._build_task_from_id = MagicMock(return_value="mock_task")
        result = client.get_task("T-1")
        assert result == "mock_task"
        client._build_task_from_id.assert_called_once_with("T-1")


# ── get_available_tasks ──────────────────────────────────


class TestGetAvailableTasks:
    """Tests for get_available_tasks() method."""

    def test_returns_unassigned_tasks(self):
        client = _make_client()

        t1 = MagicMock()
        t1.agent_id = None
        t2 = MagicMock()
        t2.agent_id = "code-agent"  # assigned — should be filtered
        t3 = MagicMock()
        t3.agent_id = None

        client.get_all_tasks = MagicMock(side_effect=[
            [t1, t2],  # TODO tasks
            [t3],       # pending tasks
        ])

        result = client.get_available_tasks()
        assert len(result) == 2
        assert t1 in result
        assert t3 in result
        assert t2 not in result

    def test_no_available_tasks(self):
        client = _make_client()
        client.get_all_tasks = MagicMock(return_value=[])
        result = client.get_available_tasks()
        assert result == []

    def test_queries_todo_and_pending(self):
        client = _make_client()
        client.get_all_tasks = MagicMock(return_value=[])
        client.get_available_tasks()
        calls = client.get_all_tasks.call_args_list
        assert calls[0] == ((), {"status": "TODO"})
        assert calls[1] == ((), {"status": "pending"})
