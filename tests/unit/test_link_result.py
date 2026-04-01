"""
Unit tests for LinkResult structured error returns.

Per SRVJ-BUG-ERROR-OBS-01 / EPIC-TASK-WORKFLOW-HEAL-01 P3:
All linking functions must return LinkResult instead of bare bool.
Callers can distinguish "already existed" vs "created" vs specific failures.

TDD Phase: RED — these tests MUST fail before implementation.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from dataclasses import FrozenInstanceError


# ── 1. LinkResult Dataclass Tests ────────────────────────────────────────


class TestLinkResultDataclass:
    """LinkResult must exist, be a dataclass, and format for MCP."""

    def test_import(self):
        """LinkResult is importable from governance.services.link_result."""
        from governance.services.link_result import LinkResult
        assert LinkResult is not None

    def test_success_fields(self):
        """Successful link has success=True, already_existed=False, reason."""
        from governance.services.link_result import LinkResult
        r = LinkResult(success=True, already_existed=False, reason="created")
        assert r.success is True
        assert r.already_existed is False
        assert r.reason == "created"
        assert r.error_code is None

    def test_idempotent_fields(self):
        """Idempotent (duplicate) link has success=True, already_existed=True."""
        from governance.services.link_result import LinkResult
        r = LinkResult(success=True, already_existed=True, reason="relation already exists")
        assert r.success is True
        assert r.already_existed is True

    def test_failure_fields(self):
        """Failed link has success=False with reason and error_code."""
        from governance.services.link_result import LinkResult
        r = LinkResult(
            success=False,
            already_existed=False,
            reason="task T-999 not found",
            error_code="ENTITY_NOT_FOUND",
        )
        assert r.success is False
        assert r.error_code == "ENTITY_NOT_FOUND"
        assert "T-999" in r.reason

    def test_connection_failure(self):
        """Connection failure has error_code NO_CLIENT."""
        from governance.services.link_result import LinkResult
        r = LinkResult(
            success=False,
            already_existed=False,
            reason="TypeDB client unavailable",
            error_code="NO_CLIENT",
        )
        assert r.error_code == "NO_CLIENT"

    def test_to_mcp_response_success(self):
        """to_mcp_response() returns dict with success + already_existed."""
        from governance.services.link_result import LinkResult
        r = LinkResult(success=True, already_existed=False, reason="created")
        d = r.to_mcp_response()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["already_existed"] is False
        assert d["reason"] == "created"
        assert "error_code" not in d  # omitted when None

    def test_to_mcp_response_failure(self):
        """to_mcp_response() includes error_code when present."""
        from governance.services.link_result import LinkResult
        r = LinkResult(
            success=False,
            already_existed=False,
            reason="task T-999 not found",
            error_code="ENTITY_NOT_FOUND",
        )
        d = r.to_mcp_response()
        assert d["success"] is False
        assert d["error_code"] == "ENTITY_NOT_FOUND"
        assert "T-999" in d["reason"]

    def test_to_mcp_response_idempotent(self):
        """to_mcp_response() for idempotent result shows already_existed=True."""
        from governance.services.link_result import LinkResult
        r = LinkResult(success=True, already_existed=True, reason="relation already exists")
        d = r.to_mcp_response()
        assert d["success"] is True
        assert d["already_existed"] is True

    def test_bool_coercion(self):
        """LinkResult is truthy when success=True, falsy when False.

        This preserves backward compatibility with callers that do `if result:`.
        """
        from governance.services.link_result import LinkResult
        assert bool(LinkResult(success=True, already_existed=False, reason="ok"))
        assert not bool(LinkResult(success=False, already_existed=False, reason="fail"))


# ── 2. Service Layer — link_task_to_session ──────────────────────────────


class TestLinkTaskToSessionReturnsLinkResult:
    """link_task_to_session must return LinkResult, not bool."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_no_client_returns_link_result(self, mock_get_client):
        mock_get_client.return_value = None
        from governance.services.tasks_mutations_linking import link_task_to_session
        result = link_task_to_session("T-001", "SESSION-1")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert result.error_code == "NO_CLIENT"

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_task_not_found_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = None
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_session
        result = link_task_to_session("T-MISSING", "SESSION-1")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert result.error_code == "ENTITY_NOT_FOUND"
        assert "T-MISSING" in result.reason

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_success_new_link_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_session.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_session
        from governance.stores import _tasks_store
        _tasks_store["T-001"] = {"linked_sessions": []}
        result = link_task_to_session("T-001", "SESSION-1")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is True
        assert result.already_existed is False

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_exception_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_session.side_effect = ConnectionError("connection refused")
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_session
        result = link_task_to_session("T-001", "SESSION-1")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert result.error_code == "EXCEPTION"
        assert "connection" in result.reason.lower()


# ── 3. Service Layer — link_task_to_rule ─────────────────────────────────


class TestLinkTaskToRuleReturnsLinkResult:
    """link_task_to_rule must return LinkResult, not bool."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_no_client_returns_link_result(self, mock_get_client):
        mock_get_client.return_value = None
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("T-001", "RULE-001")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert result.error_code == "NO_CLIENT"

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_task_not_found(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = None
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("T-GONE", "RULE-001")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert "T-GONE" in result.reason

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_success_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_rule.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("T-001", "RULE-001")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is True


# ── 4. Service Layer — link_task_to_document ─────────────────────────────


class TestLinkTaskToDocumentReturnsLinkResult:
    """link_task_to_document must return LinkResult, not bool."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_success_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_document.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_document
        from governance.stores import _tasks_store
        _tasks_store["T-001"] = {"linked_documents": []}
        result = link_task_to_document("T-001", "docs/README.md")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is True

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_exception_includes_context(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_document.side_effect = RuntimeError("TypeDB unreachable")
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_document
        result = link_task_to_document("T-001", "docs/README.md")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert "RuntimeError" in result.reason or "unreachable" in result.reason.lower()


# ── 5. Service Layer — unlink_task_from_document ─────────────────────────


class TestUnlinkTaskFromDocumentReturnsLinkResult:
    """unlink_task_from_document must return LinkResult, not bool."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_success_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.unlink_task_from_document.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import unlink_task_from_document
        result = unlink_task_from_document("T-001", "docs/README.md")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is True

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_no_client_returns_link_result(self, mock_get_client):
        mock_get_client.return_value = None
        from governance.services.tasks_mutations_linking import unlink_task_from_document
        result = unlink_task_from_document("T-001", "docs/README.md")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert result.error_code == "NO_CLIENT"


# ── 6. Service Layer — link_task_to_workspace ────────────────────────────


class TestLinkTaskToWorkspaceReturnsLinkResult:
    """link_task_to_workspace must return LinkResult, not bool."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_success_returns_link_result(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_workspace.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_workspace
        result = link_task_to_workspace("T-001", "WS-TEST-SANDBOX")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is True

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_task_not_found(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = None
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_workspace
        result = link_task_to_workspace("T-GONE", "WS-TEST-SANDBOX")
        from governance.services.link_result import LinkResult
        assert isinstance(result, LinkResult)
        assert result.success is False
        assert "T-GONE" in result.reason


# ── 7. Backward Compatibility — bool coercion in callers ─────────────────


class TestBackwardCompatibility:
    """Existing callers that do `if result:` must still work."""

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_if_result_true(self, mock_get_client):
        client = MagicMock()
        client.get_task.return_value = MagicMock()
        client.link_task_to_rule.return_value = True
        mock_get_client.return_value = client
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("T-001", "RULE-001")
        # Must be truthy — backward compat with `if result:`
        assert result
        assert bool(result) is True

    @patch("governance.services.tasks_mutations_linking.get_typedb_client")
    def test_if_result_false(self, mock_get_client):
        mock_get_client.return_value = None
        from governance.services.tasks_mutations_linking import link_task_to_rule
        result = link_task_to_rule("T-001", "RULE-001")
        # Must be falsy — backward compat with `if not result:`
        assert not result
        assert bool(result) is False
