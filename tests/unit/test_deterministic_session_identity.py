"""
Tests for P9: Deterministic Session Identity (BUG-SESSION-POISON-01 root cause).

Validates that auto-linking is REMOVED — session_id must be explicit.
TDD RED phase: these tests MUST FAIL before implementation.

BDD Scenarios:
  1. Task created without session_id has no linked session
  2. Task created with explicit session_id links correctly
  3. Invalid session_id rejected at all boundaries
  4. Poisoned _sessions_store cannot affect task creation

Created: 2026-03-28
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Scenario 1: No session_id → no linked session ────────────────────

class TestNoAutoLinking:
    """create_task/update_task without session_id must NOT auto-link."""

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_no_session_id_gives_empty_linked_sessions(self, mock_client):
        """Task created without session_id has linked_sessions=[]."""
        mock_client.return_value = None  # Force fallback path
        from governance.services.tasks import create_task, _tasks_store
        _tasks_store.clear()

        result = create_task(
            task_id="P9-DETERM-001",
            description="Test deterministic session identity",
        )
        assert result.get("linked_sessions") == [] or result.linked_sessions == []

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_no_session_even_with_active_sessions(self, mock_client):
        """Active sessions in _sessions_store must NOT auto-link to new tasks."""
        mock_client.return_value = None
        from governance.services.tasks import create_task, _tasks_store
        from governance.stores import _sessions_store
        _tasks_store.clear()

        # Poison the sessions store with a valid, active session
        _sessions_store["SESSION-ACTIVE-001"] = {
            "status": "ACTIVE",
            "start_time": datetime.now().isoformat(),
        }

        try:
            result = create_task(
                task_id="P9-DETERM-002",
                description="Should not auto-link",
            )
            linked = result.get("linked_sessions", [])
            if hasattr(result, 'linked_sessions'):
                linked = result.linked_sessions or []
            # THIS IS THE KEY ASSERTION: must be empty
            assert linked == [], (
                f"Auto-linking is still active! Got linked_sessions={linked}"
            )
        finally:
            _sessions_store.pop("SESSION-ACTIVE-001", None)
            _tasks_store.pop("P9-DETERM-002", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_status_no_auto_link(self, mock_client):
        """update_task with status change must NOT auto-link when no session_id given."""
        mock_client.return_value = None
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        _tasks_store["P9-DETERM-003"] = {
            "task_id": "P9-DETERM-003",
            "description": "Test no auto-link on update",
            "status": "OPEN",
            "linked_sessions": [],
            "linked_rules": [],
            "linked_documents": [],
            "phase": "P9",
            "persistence_status": "memory_only",
        }
        _sessions_store["SESSION-ACTIVE-002"] = {
            "status": "ACTIVE",
            "start_time": datetime.now().isoformat(),
        }

        try:
            result = update_task(
                task_id="P9-DETERM-003",
                status="IN_PROGRESS",
            )
            linked = result.get("linked_sessions", [])
            assert linked == [], (
                f"Auto-linking on update is still active! Got linked_sessions={linked}"
            )
        finally:
            _sessions_store.pop("SESSION-ACTIVE-002", None)
            _tasks_store.pop("P9-DETERM-003", None)


# ── Scenario 2: Explicit session_id links correctly ──────────────────

class TestExplicitSessionLinking:
    """Explicit session_id parameter is the ONLY way to link."""

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_with_explicit_session_links(self, mock_client):
        """Task created with explicit session_id has it in linked_sessions."""
        mock_client.return_value = None
        from governance.services.tasks import create_task, _tasks_store
        _tasks_store.clear()

        result = create_task(
            task_id="P9-DETERM-010",
            description="Test explicit session link",
            linked_sessions=["SESSION-VALID-001"],
        )
        linked = result.get("linked_sessions", [])
        if hasattr(result, 'linked_sessions'):
            linked = result.linked_sessions or []
        assert "SESSION-VALID-001" in linked

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_with_explicit_session_links(self, mock_client):
        """update_task with explicit linked_sessions stores them."""
        mock_client.return_value = None
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        _tasks_store["P9-DETERM-011"] = {
            "task_id": "P9-DETERM-011",
            "description": "Test explicit link on update",
            "status": "OPEN",
            "linked_sessions": [],
            "linked_rules": [],
            "linked_documents": [],
            "phase": "P9",
            "persistence_status": "memory_only",
        }

        try:
            result = update_task(
                task_id="P9-DETERM-011",
                linked_sessions=["SESSION-EXPLICIT-001"],
            )
            linked = result.get("linked_sessions", [])
            assert "SESSION-EXPLICIT-001" in linked
        finally:
            _tasks_store.pop("P9-DETERM-011", None)


# ── Scenario 3: Invalid session_id rejected ───────────────────────────

class TestInvalidSessionRejection:
    """Invalid session_id rejected at all boundaries (defense-in-depth)."""

    def test_is_valid_session_id_rejects_path_traversal(self):
        """_is_valid_session_id rejects path traversal strings."""
        from governance.services.tasks import _is_valid_session_id
        assert _is_valid_session_id("../../etc/passwd") is False
        assert _is_valid_session_id("../secret") is False
        assert _is_valid_session_id("session/../../etc") is False

    def test_is_valid_session_id_rejects_injection(self):
        """_is_valid_session_id rejects injection attempts."""
        from governance.services.tasks import _is_valid_session_id
        assert _is_valid_session_id('session"injection') is False
        assert _is_valid_session_id("session;drop") is False
        assert _is_valid_session_id("") is False

    def test_is_valid_session_id_accepts_valid(self):
        """_is_valid_session_id accepts legitimate session IDs."""
        from governance.services.tasks import _is_valid_session_id
        assert _is_valid_session_id("SESSION-2026-03-28-WORK") is True
        assert _is_valid_session_id("SESSION-(PAREN)") is True
        assert _is_valid_session_id("simple_id") is True

    def test_mcp_task_link_session_rejects_traversal(self):
        """MCP task_link_session rejects path traversal session_id."""
        mcp = MagicMock()
        registered_tools = {}

        def capture_tool():
            def decorator(fn):
                registered_tools[fn.__name__] = fn
                return fn
            return decorator

        mcp.tool = capture_tool
        from governance.mcp_tools.tasks_linking import register_task_linking_tools
        register_task_linking_tools(mcp)

        result = registered_tools["task_link_session"]("TASK-001", "../../etc/passwd")
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_typedb_link_rejects_traversal(self):
        """TypeDB link_task_to_session rejects path traversal before transaction."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        client = MagicMock()
        result = TaskLinkingOperations.link_task_to_session(
            client, "TASK-001", "../../etc/passwd"
        )
        assert result is False
        client._driver.transaction.assert_not_called()


# ── Scenario 4: Poisoned store cannot affect task creation ────────────

class TestPoisonImmunity:
    """Poisoned _sessions_store CANNOT affect task creation."""

    @patch("governance.services.tasks.get_typedb_client")
    def test_poisoned_store_no_effect_on_create(self, mock_client):
        """_sessions_store with path traversal entry does NOT auto-link."""
        mock_client.return_value = None
        from governance.services.tasks import create_task, _tasks_store
        from governance.stores import _sessions_store

        _tasks_store.clear()
        _sessions_store["../../etc/passwd"] = {
            "status": "ACTIVE",
            "start_time": "2026-03-28T10:00:00",
        }

        try:
            result = create_task(
                task_id="P9-DETERM-020",
                description="Poison immunity test",
            )
            linked = result.get("linked_sessions", [])
            if hasattr(result, 'linked_sessions'):
                linked = result.linked_sessions or []
            assert linked == [], (
                f"Poisoned store affected task creation! linked_sessions={linked}"
            )
        finally:
            _sessions_store.pop("../../etc/passwd", None)
            _tasks_store.pop("P9-DETERM-020", None)

    @patch("governance.services.tasks.get_typedb_client")
    def test_poisoned_store_mixed_valid_invalid_no_autolink(self, mock_client):
        """Even if _sessions_store has valid sessions, auto-link must not happen."""
        mock_client.return_value = None
        from governance.services.tasks import create_task, _tasks_store
        from governance.stores import _sessions_store

        _tasks_store.clear()
        _sessions_store["../../etc/passwd"] = {
            "status": "ACTIVE",
            "start_time": "2026-03-28T10:00:00",
        }
        _sessions_store["SESSION-VALID-999"] = {
            "status": "ACTIVE",
            "start_time": "2026-03-28T09:00:00",
        }

        try:
            result = create_task(
                task_id="P9-DETERM-021",
                description="Mixed poison immunity test",
            )
            linked = result.get("linked_sessions", [])
            if hasattr(result, 'linked_sessions'):
                linked = result.linked_sessions or []
            # CRITICAL: even the valid session must NOT be auto-linked
            assert linked == [], (
                f"Auto-linking still active despite removal! linked_sessions={linked}"
            )
        finally:
            _sessions_store.pop("../../etc/passwd", None)
            _sessions_store.pop("SESSION-VALID-999", None)
            _tasks_store.pop("P9-DETERM-021", None)


# ── _get_active_session_id removed ────────────────────────────────────

class TestAutoLinkFunctionRemoved:
    """_get_active_session_id() must be removed entirely."""

    def test_get_active_session_id_not_importable(self):
        """_get_active_session_id should not exist in tasks module."""
        from governance.services import tasks
        assert not hasattr(tasks, '_get_active_session_id'), (
            "_get_active_session_id still exists — must be removed"
        )

    def test_get_active_session_id_not_in_mutations(self):
        """tasks_mutations must not import _get_active_session_id."""
        import inspect
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        assert '_get_active_session_id' not in source, (
            "_get_active_session_id still referenced in tasks_mutations.py"
        )
