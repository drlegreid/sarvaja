"""
Unit tests for Task Verification & Session Sync MCP Tools.

Batch 151: Tests for governance/mcp_tools/tasks_crud_verify.py
- task_verify: validation, TypeDB update, failure paths
- session_sync_todos: JSON parsing, create/update/skip logic
"""

import json
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

import pytest

from governance.mcp_tools.tasks_crud_verify import register_task_verify_tools


_MOD = "governance.mcp_tools.tasks_crud_verify"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_task_verify_tools(mcp)
    return mcp.tools


def _mock_client(get_task_rv=None, update_rv=True, insert_rv=True):
    client = MagicMock()
    client.get_task.return_value = get_task_rv
    client.update_task.return_value = update_rv
    client.insert_task.return_value = insert_rv
    return client


@contextmanager
def _with_client(client):
    @contextmanager
    def ctx():
        yield client
    with patch(f"{_MOD}.typedb_client", ctx):
        yield


@pytest.fixture(autouse=True)
def _force_json():
    with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt), \
         patch(f"{_MOD}.log_monitor_event"):
        yield


# ── Registration ────────────────────────────────────────

class TestRegistration:
    def test_registers_two_tools(self):
        tools = _register()
        assert "task_verify" in tools
        assert "session_sync_todos" in tools


# ── task_verify ─────────────────────────────────────────

class TestTaskVerify:
    def test_missing_verification_method(self):
        tools = _register()
        result = json.loads(tools["task_verify"](
            task_id="T-1", verification_method="", evidence="some evidence"))
        assert "error" in result
        assert "verification_method" in result["error"]

    def test_missing_evidence(self):
        tools = _register()
        result = json.loads(tools["task_verify"](
            task_id="T-1", verification_method="pytest", evidence=""))
        assert "error" in result
        assert "evidence" in result["error"]

    def test_failed_test(self):
        tools = _register()
        result = json.loads(tools["task_verify"](
            task_id="T-1", verification_method="pytest",
            evidence="3 failed", test_passed=False))
        assert result["status"] == "VERIFICATION_FAILED"
        assert "Cannot mark completed" in result["error"]

    def test_success_typedb_update(self):
        tools = _register()
        client = _mock_client(update_rv=True)
        with _with_client(client):
            result = json.loads(tools["task_verify"](
                task_id="T-1", verification_method="pytest",
                evidence="all passed"))
        assert result["status"] == "completed"
        assert result["verified"] is True
        client.update_task.assert_called_once_with(task_id="T-1", status="completed")

    def test_not_in_typedb(self):
        tools = _register()
        client = _mock_client(update_rv=False)
        with _with_client(client):
            result = json.loads(tools["task_verify"](
                task_id="T-1", verification_method="curl",
                evidence="200 OK"))
        assert result["verified"] is True
        assert "not in TypeDB" in result["note"]

    def test_long_evidence_truncated(self):
        tools = _register()
        client = _mock_client(update_rv=True)
        with _with_client(client):
            result = json.loads(tools["task_verify"](
                task_id="T-1", verification_method="pytest",
                evidence="x" * 600))
        assert len(result["evidence"]) == 500

    def test_exception(self):
        tools = _register()

        @contextmanager
        def failing_ctx():
            raise Exception("db down")
            yield  # noqa: unreachable

        with patch(f"{_MOD}.typedb_client", failing_ctx):
            result = json.loads(tools["task_verify"](
                task_id="T-1", verification_method="pytest",
                evidence="ok"))
        assert "error" in result


# ── session_sync_todos ──────────────────────────────────

class TestSessionSyncTodos:
    def test_invalid_json(self):
        tools = _register()
        result = json.loads(tools["session_sync_todos"](
            session_id="S-1", todos_json="not json"))
        assert "error" in result
        assert "Invalid JSON" in result["error"]

    def test_not_array(self):
        tools = _register()
        result = json.loads(tools["session_sync_todos"](
            session_id="S-1", todos_json='{"a": 1}'))
        assert "error" in result
        assert "JSON array" in result["error"]

    def test_creates_new_tasks(self):
        tools = _register()
        client = _mock_client(get_task_rv=None)
        todos = [{"content": "Fix bug", "status": "pending"}]
        with _with_client(client):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json=json.dumps(todos)))
        assert result["summary"]["created"] == 1
        assert result["summary"]["updated"] == 0
        client.insert_task.assert_called_once()

    def test_updates_existing_tasks(self):
        tools = _register()
        existing = MagicMock()
        existing.status = "pending"
        client = _mock_client(get_task_rv=existing)
        todos = [{"content": "Fix bug", "status": "completed"}]
        with _with_client(client):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json=json.dumps(todos)))
        assert result["summary"]["updated"] == 1
        client.update_task.assert_called_once()

    def test_skips_same_status(self):
        tools = _register()
        existing = MagicMock()
        existing.status = "pending"
        client = _mock_client(get_task_rv=existing)
        todos = [{"content": "Same", "status": "pending"}]
        with _with_client(client):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json=json.dumps(todos)))
        assert result["summary"]["skipped"] == 1

    def test_skips_empty_content(self):
        tools = _register()
        client = _mock_client()
        todos = [{"content": "", "status": "pending"}]
        with _with_client(client):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json=json.dumps(todos)))
        assert result["summary"]["skipped"] == 1

    def test_mixed_operations(self):
        tools = _register()
        existing = MagicMock()
        existing.status = "pending"

        # First call (index 1) returns existing, second (index 2) returns None
        call_count = {"n": 0}
        def get_task_side(task_id):
            call_count["n"] += 1
            return existing if call_count["n"] == 1 else None

        client = _mock_client()
        client.get_task.side_effect = get_task_side
        todos = [
            {"content": "Existing changed", "status": "completed"},
            {"content": "New task", "status": "pending"},
            {"content": "", "status": "pending"},
        ]
        with _with_client(client):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json=json.dumps(todos)))
        assert result["summary"]["updated"] == 1
        assert result["summary"]["created"] == 1
        assert result["summary"]["skipped"] == 1

    def test_exception(self):
        tools = _register()

        @contextmanager
        def failing_ctx():
            raise Exception("db down")
            yield  # noqa: unreachable

        with patch(f"{_MOD}.typedb_client", failing_ctx):
            result = json.loads(tools["session_sync_todos"](
                session_id="S-1", todos_json='[{"content":"x","status":"pending"}]'))
        assert "error" in result
