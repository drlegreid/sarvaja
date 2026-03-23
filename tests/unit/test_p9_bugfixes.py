"""
Tests for P9 bugfixes — P8 issues discovered during DSE assessment.

BUG-014: link_session_to_task() does not close dialog after success
BUG-015: open_link_document_dialog() calls GET /api/documents which doesn't exist
BUG-016: GET /api/documents endpoint missing — needs new REST route

Per TEST-FIX-01-v1: TDD — failing tests FIRST, then implement.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import httpx


# ---- BUG-014: Dialog close after session link ----

class TestBug014DialogCloseAfterLink:
    """link_session_to_task() must close dialog on success."""

    def _make_controller_state(self):
        """Create mock state + ctrl for task controller registration."""
        state = MagicMock()
        state.selected_task = {"task_id": "SRVJ-BUG-014", "id": "SRVJ-BUG-014"}
        state.show_link_session_dialog = True
        state.link_session_search = "test"
        ctrl = MagicMock()
        triggers = {}

        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        return state, ctrl, triggers

    @patch("httpx.Client")
    def test_dialog_closes_on_successful_link(self, mock_client_cls):
        """After successful POST /tasks/{id}/sessions/{sid}, dialog must close."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()

        # Mock successful link + task refresh
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_resp_201 = MagicMock(status_code=201)
        mock_resp_200 = MagicMock(status_code=200)
        mock_resp_200.json.return_value = {
            "task_id": "SRVJ-BUG-014",
            "linked_sessions": ["SESSION-X"]
        }
        mock_client.post.return_value = mock_resp_201
        mock_client.get.return_value = mock_resp_200
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        # Call the handler
        triggers["link_session_to_task"]("SESSION-X")

        # Dialog MUST close after successful link
        assert state.show_link_session_dialog is False, \
            "BUG-014: Dialog must close after successful session link"

    @patch("httpx.Client")
    def test_dialog_closes_on_failed_link(self, mock_client_cls):
        """Dialog should close even on failure (don't trap user)."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=500)
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["link_session_to_task"]("SESSION-FAIL")

        # Dialog should still close on failure
        assert state.show_link_session_dialog is False, \
            "BUG-014: Dialog must close even after failed session link"


# ---- BUG-015: Document dialog should use correct endpoint ----

class TestBug015DocumentDialogEndpoint:
    """open_link_document_dialog() must use an endpoint that exists."""

    def _make_controller_state(self):
        state = MagicMock()
        state.selected_task = {"task_id": "SRVJ-BUG-015", "id": "SRVJ-BUG-015"}
        ctrl = MagicMock()
        triggers = {}

        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        return state, ctrl, triggers

    @patch("httpx.Client")
    def test_document_dialog_uses_workspace_scan(self, mock_client_cls):
        """Document dialog must use workspace scan endpoint, not /api/documents."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {"path": "docs/rules/leaf/TEST-E2E-01-v1.md"},
            {"path": "evidence/test.md"},
        ]
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["open_link_document_dialog"]()

        # Verify the URL called — must use /api/files/list, NOT /api/documents
        call_args = mock_client.get.call_args
        url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
        assert "/api/files/list" in url, \
            f"BUG-015: Must call /api/files/list (not /api/documents). Called: {url}"


# ---- BUG-016: GET /api/documents endpoint ----

class TestBug016FilesListEndpoint:
    """GET /api/files/list endpoint for workspace document listing."""

    @pytest.fixture
    def app_client(self):
        """Create test client for FastAPI."""
        from governance.routes.files import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_files_list_endpoint_exists(self, app_client):
        """GET /files/list must return 200."""
        response = app_client.get("/files/list")
        assert response.status_code == 200

    def test_files_list_returns_list(self, app_client):
        """GET /files/list must return a list of file objects."""
        response = app_client.get("/files/list")
        data = response.json()
        assert isinstance(data, list), "Response must be a list"

    def test_files_list_items_have_path(self, app_client):
        """Each file item must have a 'path' field."""
        response = app_client.get("/files/list")
        data = response.json()
        if data:
            assert "path" in data[0], "File items must have 'path' field"

    def test_files_list_recursive(self, app_client):
        """Recursive search must find more files."""
        non_recursive = app_client.get("/files/list", params={"directory": "docs", "recursive": "false"})
        recursive = app_client.get("/files/list", params={"directory": "docs", "recursive": "true"})
        assert len(recursive.json()) >= len(non_recursive.json())

    def test_files_list_rejects_traversal(self, app_client):
        """Path traversal must be rejected."""
        response = app_client.get("/files/list", params={"directory": "../../../etc"})
        assert response.status_code in (403, 404)


# ---- Regression: P8 handlers still work ----

class TestP8HandlersRegression:
    """Ensure P8 handlers still register and function."""

    def _make_controller_state(self):
        state = MagicMock()
        state.selected_task = None
        ctrl = MagicMock()
        triggers = {}

        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        return state, ctrl, triggers

    def test_all_p8_handlers_registered(self):
        """All 4 P8 handlers must be registered."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()
        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        expected = [
            "open_link_session_dialog",
            "link_session_to_task",
            "open_link_document_dialog",
            "link_documents_to_task",
        ]
        for name in expected:
            assert name in triggers, f"P8 handler '{name}' not registered"

    @patch("httpx.Client")
    def test_open_session_dialog_sets_loading(self, mock_client_cls):
        """open_link_session_dialog must set loading state."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["open_link_session_dialog"]()

        # After call completes, loading should be False (finally block)
        assert state.link_session_loading is False

    @patch("httpx.Client")
    def test_link_session_noop_without_task(self, mock_client_cls):
        """link_session_to_task should no-op if no task selected."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()
        state.selected_task = None

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["link_session_to_task"]("SESSION-X")

        # Should not call any HTTP
        mock_client_cls.assert_not_called()
