"""
Tests for BUG-SESSION-POISON-01 fixes.

Validates that session_id validation prevents path traversal poisoning
at all 4 defense layers:
1. API route (POST /api/sessions)
2. Auto-linking (_get_active_session_id filters invalid IDs)
3. TypeDB linking (link_task_to_session rejects invalid IDs)
4. MCP tool (task_link_session rejects invalid IDs)

Created: 2026-03-26
"""

import re
import pytest
from unittest.mock import patch, MagicMock


# ── Layer 1: API route validation ────────────────────────────────────

class TestSessionCreateValidation:
    """POST /api/sessions rejects path traversal session_ids."""

    def _get_validate_fn(self):
        from governance.routes.sessions.crud import _validate_session_id
        return _validate_session_id

    def _get_regex(self):
        from governance.routes.sessions.crud import _SESSION_ID_RE
        return _SESSION_ID_RE

    INVALID_IDS = [
        "../../etc/passwd",
        "../secret",
        "session/../../etc",
        "session id with spaces",
        "",
        'session"injection',
        "session;drop",
        "a" * 201,
    ]

    VALID_IDS = [
        "SESSION-2026-03-26-WORK",
        "SESSION-2026-03-26-CHECK-(RULE)",
        "SESSION-2026.03.26-TEST",
        "simple_id",
        "A",
    ]

    @pytest.mark.parametrize("session_id", INVALID_IDS)
    def test_rejects_invalid_session_ids(self, session_id):
        """Invalid session_ids raise HTTPException 422."""
        from fastapi import HTTPException
        validate = self._get_validate_fn()
        with pytest.raises(HTTPException) as exc_info:
            validate(session_id)
        assert exc_info.value.status_code == 422

    @pytest.mark.parametrize("session_id", VALID_IDS)
    def test_accepts_valid_session_ids(self, session_id):
        """Valid session_ids pass without exception."""
        validate = self._get_validate_fn()
        validate(session_id)  # Should not raise

    def test_regex_rejects_path_traversal(self):
        """Regex pattern itself rejects ../../etc/passwd."""
        regex = self._get_regex()
        assert not regex.match("../../etc/passwd")
        assert not regex.match("../secret")
        assert not regex.match("session/../../etc")

    def test_regex_accepts_parentheses(self):
        """Regex accepts session IDs with parentheses."""
        regex = self._get_regex()
        assert regex.match("SESSION-CHECK-(RULE)")
        assert regex.match("SESSION-(test)")


# ── Layer 2: Auto-linking REMOVED (P9 root cause fix) ────────────────

class TestAutoLinkingRemoved:
    """P9: _get_active_session_id() removed — auto-linking is gone.

    Previously tested band-aid filtering. Root cause now fixed:
    session_id must be passed explicitly (BUG-SESSION-POISON-01).
    """

    def test_get_active_session_id_removed(self):
        """_get_active_session_id no longer exists in tasks module."""
        from governance.services import tasks
        assert not hasattr(tasks, '_get_active_session_id'), (
            "P9: _get_active_session_id must be removed — auto-linking is the root cause"
        )

    def test_is_valid_session_id_still_exists(self):
        """_is_valid_session_id kept as defense-in-depth at boundaries."""
        from governance.services.tasks import _is_valid_session_id
        assert _is_valid_session_id("SESSION-VALID") is True
        assert _is_valid_session_id("SESSION-(PAREN)") is True
        assert _is_valid_session_id("../../etc/passwd") is False
        assert _is_valid_session_id("") is False
        assert _is_valid_session_id("a" * 201) is False

    def test_create_task_no_autolink(self):
        """create_task without linked_sessions gives empty list, not auto-linked."""
        from governance.services.tasks import create_task, _tasks_store
        _tasks_store.clear()
        with patch("governance.services.tasks.get_typedb_client", return_value=None):
            result = create_task(
                task_id="P9-POISON-LAYER2-001",
                description="Layer 2 no-autolink test",
            )
        assert result.get("linked_sessions") == []


# ── Layer 3: TypeDB linking validation ───────────────────────────────

class TestLinkTaskToSessionValidation:
    """link_task_to_session() rejects invalid session IDs before auto-creating."""

    def test_rejects_path_traversal(self):
        """Path traversal session_id returns False without touching TypeDB."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        client = MagicMock()
        result = TaskLinkingOperations.link_task_to_session(
            client, "TASK-001", "../../etc/passwd"
        )
        assert result is False
        # Should NOT have opened a TypeDB transaction
        client._driver.transaction.assert_not_called()

    def test_rejects_empty_session_id(self):
        """Empty session_id returns False."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        client = MagicMock()
        result = TaskLinkingOperations.link_task_to_session(client, "TASK-001", "")
        assert result is False

    def test_accepts_valid_session_id(self):
        """Valid session_id proceeds to TypeDB transaction (not rejected by validation)."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        client = MagicMock()
        client.database = "test-db"
        client._connected = True
        # Mock the transaction context manager
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = iter([])
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        TaskLinkingOperations.link_task_to_session(
            client, "TASK-001", "SESSION-VALID-001"
        )
        # Should have attempted a TypeDB transaction (validation passed)
        client._driver.transaction.assert_called()


# ── Layer 4: MCP tool validation ─────────────────────────────────────

class TestMCPTaskLinkSessionValidation:
    """MCP task_link_session tool rejects invalid session IDs."""

    def test_rejects_path_traversal(self):
        """Path traversal session_id returns error via MCP."""
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

    def test_accepts_valid_session_id(self):
        """Valid session_id proceeds (may fail at TypeDB but not validation)."""
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

        with patch("governance.mcp_tools.tasks_linking.get_typedb_client") as mock_client:
            mock_client.return_value.connect.return_value = True
            mock_client.return_value.link_task_to_session.return_value = True
            result = registered_tools["task_link_session"]("TASK-001", "SESSION-VALID")
        # Should succeed (not hit the validation error path)
        assert "invalid" not in result.lower()
