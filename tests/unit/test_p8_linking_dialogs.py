"""
Unit tests for EPIC-TASK-QUALITY-V2 Phase 8: Task Linking Dialogs + Navigation.

Tests:
- BUG-013: Session chip click navigation + back button
- FEAT-011: Link Session picker dialog controller
- FEAT-012: Link Document tree browser controller
- FEAT-013: Auto-assign workspace on task_create
- BUG-DONE-GATE-STALE: Pre-load task from TypeDB before DONE gate

Per TEST-FIX-01-v1: TDD tests written alongside implementation.
"""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest


# =====================================================================
# Helpers
# =====================================================================

def _setup_nav(tasks=None, sessions=None, rules=None):
    """Create mock ctrl + state, register navigation handlers."""
    from agent.governance_ui.controllers.tasks_navigation import (
        register_tasks_navigation,
    )
    ctrl = MagicMock()
    state = MagicMock()
    state.tasks = tasks or []
    state.sessions = sessions or []
    state.rules = rules or []

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)
    register_tasks_navigation(state, ctrl, "http://localhost:8082")
    return ctrl, state, triggers


def _setup_tasks_ctrl():
    """Create mock ctrl + state, register task controllers."""
    from agent.governance_ui.controllers.tasks import (
        register_tasks_controllers,
    )
    ctrl = MagicMock()
    state = MagicMock()
    state.tasks = []
    state.sessions = []
    state.selected_task = {"task_id": "T-001", "id": "T-001", "linked_sessions": []}
    state.is_loading = False
    state.has_error = False
    state.active_view = "tasks"
    state.show_task_detail = True

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    # Mock state.change decorator
    def change_decorator(field_name):
        def wrapper(fn):
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)
    state.change = MagicMock(side_effect=change_decorator)

    with patch("httpx.Client") as mock_client:
        # Mock initial load_tasks_page call
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [], "pagination": {}}
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

    return ctrl, state, triggers


# =====================================================================
# BUG-013: Session chip click navigation
# =====================================================================


class TestBug013SessionNavigation:
    """BUG-013: Clicking session link in task detail navigates to session."""

    def test_navigate_to_session_switches_view(self):
        sessions = [{"session_id": "SESSION-001", "topic": "Test"}]
        _, state, triggers = _setup_nav(sessions=sessions)
        triggers["navigate_to_session"]("SESSION-001", "tasks", "T-001", "Back to T-001")
        assert state.active_view == "sessions"
        assert state.show_task_detail is False

    def test_navigate_to_session_captures_source(self):
        sessions = [{"session_id": "SESSION-001"}]
        _, state, triggers = _setup_nav(sessions=sessions)
        triggers["navigate_to_session"]("SESSION-001", "tasks", "T-001", "Back to T-001")
        assert state.nav_source_view == "tasks"
        assert state.nav_source_id == "T-001"
        assert state.nav_source_label == "Back to T-001"

    def test_navigate_to_session_finds_in_list(self):
        sessions = [{"session_id": "SESSION-001", "topic": "Test"}]
        _, state, triggers = _setup_nav(sessions=sessions)
        triggers["navigate_to_session"]("SESSION-001", "tasks", "T-001", "Back")
        assert state.selected_session == sessions[0]
        assert state.show_session_detail is True

    @patch("httpx.Client")
    def test_navigate_to_session_loads_from_api(self, mock_client):
        _, state, triggers = _setup_nav()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session_id": "SESSION-002", "topic": "API"}
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["navigate_to_session"]("SESSION-002", "tasks", "T-001", "Back")
        assert state.show_session_detail is True

    def test_navigate_to_session_empty_returns_early(self):
        _, state, triggers = _setup_nav()
        state.active_view = "tasks"
        triggers["navigate_to_session"](None)
        # Should not change view
        assert state.active_view == "tasks"

    def test_navigate_to_session_forces_dirty(self):
        """BUG-012: dirty() on detail flags, NOT active_view."""
        sessions = [{"session_id": "SESSION-001"}]
        _, state, triggers = _setup_nav(sessions=sessions)
        triggers["navigate_to_session"]("SESSION-001", "tasks", "T-001", "Back")
        state.dirty.assert_any_call('show_session_detail')
        state.dirty.assert_any_call('show_task_detail')

    @patch("httpx.Client")
    def test_navigate_to_session_restores_on_failure(self, mock_client):
        _, state, triggers = _setup_nav()
        state.active_view = "tasks"
        state.show_task_detail = True
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["navigate_to_session"]("SESSION-XXX", "tasks", "T-001", "Back")
        # Should restore previous view on failure
        assert state.active_view == "tasks"
        assert state.show_task_detail is True


# =====================================================================
# BUG-013: Back button from session to task
# =====================================================================


class TestBug013BackNavigation:
    """BUG-013: Back button from session detail returns to task detail."""

    def test_back_to_tasks_restores_task_detail(self):
        tasks = [{"task_id": "T-001", "id": "T-001"}]
        _, state, triggers = _setup_nav(tasks=tasks)
        state.nav_source_view = "tasks"
        state.nav_source_id = "T-001"
        state.nav_source_label = "Back to T-001"
        triggers["navigate_back_to_source"]()
        assert state.active_view == "tasks"
        assert state.selected_task == tasks[0]
        assert state.show_task_detail is True

    @patch("httpx.Client")
    def test_back_to_tasks_loads_from_api(self, mock_client):
        _, state, triggers = _setup_nav()
        state.nav_source_view = "tasks"
        state.nav_source_id = "T-002"
        state.nav_source_label = "Back to T-002"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"task_id": "T-002"}
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["navigate_back_to_source"]()
        assert state.active_view == "tasks"
        assert state.show_task_detail is True

    def test_back_to_sessions_still_works(self):
        sessions = [{"session_id": "S-001", "id": "S-001"}]
        _, state, triggers = _setup_nav(sessions=sessions)
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-001"
        state.nav_source_label = "Back to S-001"
        triggers["navigate_back_to_source"]()
        assert state.active_view == "sessions"

    def test_back_clears_nav_context(self):
        _, state, triggers = _setup_nav()
        state.nav_source_view = "tasks"
        state.nav_source_id = "T-001"
        state.nav_source_label = "Back"
        triggers["navigate_back_to_source"]()
        assert state.nav_source_view is None
        assert state.nav_source_id is None
        assert state.nav_source_label is None


# =====================================================================
# FEAT-011: Link Session dialog controller
# =====================================================================


class TestFeat011LinkSessionDialog:
    """FEAT-011: Link Session picker dialog."""

    @patch("httpx.Client")
    def test_open_link_session_dialog_fetches_sessions(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"session_id": "S-001", "topic": "Test"},
            {"session_id": "S-002", "topic": "Work"},
        ]
        mock_ctx = MagicMock()
        mock_ctx.get = MagicMock(return_value=mock_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["open_link_session_dialog"]()
        assert state.show_link_session_dialog is True
        assert state.link_session_loading is False

    @patch("httpx.Client")
    def test_open_link_session_dialog_handles_dict_response(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [{"session_id": "S-001"}]}
        mock_ctx = MagicMock()
        mock_ctx.get = MagicMock(return_value=mock_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["open_link_session_dialog"]()
        assert state.link_session_items == [{"session_id": "S-001"}]

    @patch("httpx.Client")
    def test_link_session_to_task_posts_and_refreshes(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        mock_link_resp = MagicMock()
        mock_link_resp.status_code = 201
        mock_detail_resp = MagicMock()
        mock_detail_resp.status_code = 200
        mock_detail_resp.json.return_value = {"task_id": "T-001", "linked_sessions": ["S-001"]}
        mock_ctx = MagicMock()
        mock_ctx.post = MagicMock(return_value=mock_link_resp)
        mock_ctx.get = MagicMock(return_value=mock_detail_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["link_session_to_task"]("S-001")
        mock_ctx.post.assert_called_once_with("http://localhost:8082/api/tasks/T-001/sessions/S-001")

    def test_link_session_no_task_returns(self):
        _, state, triggers = _setup_tasks_ctrl()
        state.selected_task = None
        triggers["link_session_to_task"]("S-001")
        # Should return without error
        assert not state.has_error

    def test_link_session_no_session_id_returns(self):
        _, state, triggers = _setup_tasks_ctrl()
        triggers["link_session_to_task"](None)
        assert not state.has_error


# =====================================================================
# FEAT-012: Link Document tree browser controller
# =====================================================================


class TestFeat012LinkDocumentDialog:
    """FEAT-012: Link Document tree browser dialog."""

    @patch("httpx.Client")
    def test_open_link_document_dialog_fetches_docs(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"path": "docs/rules/leaf/TEST-E2E-01-v1.md"},
            {"path": ".claude/plans/plan.md"},
        ]
        mock_ctx = MagicMock()
        mock_ctx.get = MagicMock(return_value=mock_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["open_link_document_dialog"]()
        assert state.show_link_document_dialog is True
        assert state.link_document_loading is False
        assert state.link_document_selected == []

    @patch("httpx.Client")
    def test_open_link_document_dialog_normalizes_strings(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = ["path/a.md", "path/b.md"]
        mock_ctx = MagicMock()
        mock_ctx.get = MagicMock(return_value=mock_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["open_link_document_dialog"]()
        assert state.link_document_items == [{"path": "path/a.md"}, {"path": "path/b.md"}]

    @patch("httpx.Client")
    def test_link_documents_to_task_batch_posts(self, mock_client):
        _, state, triggers = _setup_tasks_ctrl()
        state.link_document_selected = ["doc1.md", "doc2.md"]
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 201
        mock_detail_resp = MagicMock()
        mock_detail_resp.status_code = 200
        mock_detail_resp.json.return_value = {"task_id": "T-001", "linked_documents": ["doc1.md", "doc2.md"]}
        mock_ctx = MagicMock()
        mock_ctx.post = MagicMock(return_value=mock_post_resp)
        mock_ctx.get = MagicMock(return_value=mock_detail_resp)
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        triggers["link_documents_to_task"]()
        assert mock_ctx.post.call_count == 2
        assert state.show_link_document_dialog is False
        assert state.link_document_selected == []

    def test_link_documents_no_task_returns(self):
        _, state, triggers = _setup_tasks_ctrl()
        state.selected_task = None
        triggers["link_documents_to_task"]()
        assert not state.has_error

    def test_link_documents_empty_selection_returns(self):
        _, state, triggers = _setup_tasks_ctrl()
        state.link_document_selected = []
        triggers["link_documents_to_task"]()
        assert not state.has_error


# =====================================================================
# FEAT-013: Auto-assign workspace on task_create
# =====================================================================


class TestFeat013AutoAssignWorkspace:
    """FEAT-013: task_create auto-assigns DEFAULT_WORKSPACE_ID."""

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.task_to_response")
    def test_create_task_assigns_default_workspace(self, mock_resp, mock_sid, mock_client):
        from governance.services.tasks import create_task
        mock_cl = MagicMock()
        mock_cl.get_task.return_value = None  # Task doesn't exist
        mock_task = MagicMock()
        mock_cl.insert_task.return_value = mock_task
        mock_client.return_value = mock_cl
        mock_resp.return_value = {"task_id": "SRVJ-TEST-099", "workspace_id": "WS-9147535A"}
        result = create_task(
            task_id="SRVJ-TEST-099",
            description="Test > Data > Workspace",
            task_type="test",
            # NO workspace_id — should auto-assign
        )
        # Verify insert_task was called with default workspace
        call_kwargs = mock_cl.insert_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") == "WS-9147535A"

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.task_to_response")
    def test_create_task_keeps_explicit_workspace(self, mock_resp, mock_sid, mock_client):
        from governance.services.tasks import create_task
        mock_cl = MagicMock()
        mock_cl.get_task.return_value = None
        mock_task = MagicMock()
        mock_cl.insert_task.return_value = mock_task
        mock_client.return_value = mock_cl
        mock_resp.return_value = {"task_id": "SRVJ-TEST-100", "workspace_id": "WS-CUSTOM"}
        result = create_task(
            task_id="SRVJ-TEST-100",
            description="Test > Data > Custom Workspace",
            task_type="test",
            workspace_id="WS-CUSTOM",
        )
        call_kwargs = mock_cl.insert_task.call_args
        assert call_kwargs.kwargs.get("workspace_id") == "WS-CUSTOM"


# =====================================================================
# BUG-DONE-GATE-STALE: Pre-load from TypeDB before DONE gate
# =====================================================================


class TestDoneGatePreload:
    """DONE gate should pre-load task from TypeDB when not in _tasks_store."""

    @patch("governance.services.tasks_preload.get_typedb_client")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_gate_preloads_from_typedb(self, mock_client, mock_preload_client):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        # Clear _tasks_store for this test
        _tasks_store.pop("T-PRELOAD", None)

        mock_task = MagicMock()
        mock_task.name = "Preload Test"
        mock_task.phase = "P8"
        mock_task.status = "IN_PROGRESS"
        mock_task.agent_id = "code-agent"
        mock_task.created_at = MagicMock()
        mock_task.created_at.isoformat.return_value = "2026-03-23T10:00:00"
        mock_task.claimed_at = None
        mock_task.completed_at = None
        mock_task.body = "test body"
        mock_task.gap_id = None
        mock_task.priority = "HIGH"
        mock_task.task_type = "bug"
        mock_task.evidence = "Tests pass: verified"  # bug DoD requires evidence
        mock_task.resolution = None
        mock_task.document_path = None
        mock_task.linked_rules = []
        mock_task.linked_sessions = ["SESSION-001"]
        mock_task.linked_commits = []
        mock_task.linked_documents = ["plan.md"]
        mock_task.summary = "Preload Test"
        mock_task.workspace_id = "WS-9147535A"

        # update_task_status returns updated task
        mock_updated = MagicMock()
        mock_updated.status = "DONE"
        mock_updated.agent_id = "code-agent"

        mock_cl = MagicMock()
        mock_cl.get_task.return_value = mock_task
        mock_cl.update_task_status.return_value = mock_updated
        mock_client.return_value = mock_cl
        mock_preload_client.return_value = mock_cl

        # Should NOT raise ValueError now that pre-load is in place
        result = update_task("T-PRELOAD", status="DONE")
        assert result is not None

        # Clean up
        _tasks_store.pop("T-PRELOAD", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_gate_still_works_with_tasks_store(self, mock_client):
        from governance.services.tasks_mutations import update_task, _tasks_store
        # Pre-populate _tasks_store
        _tasks_store["T-CACHED"] = {
            "task_id": "T-CACHED",
            "description": "Cached",
            "summary": "Cached Test",
            "agent_id": "code-agent",
            "completed_at": "2026-03-23T10:00:00",
            "linked_sessions": ["SESSION-001"],
            "linked_documents": ["doc.md"],
            "status": "IN_PROGRESS",
            "phase": "P8",
        }

        mock_task = MagicMock()
        mock_task.status = "IN_PROGRESS"
        mock_task.agent_id = "code-agent"
        mock_updated = MagicMock()
        mock_updated.status = "DONE"
        mock_updated.agent_id = "code-agent"

        mock_cl = MagicMock()
        mock_cl.get_task.return_value = mock_task
        mock_cl.update_task_status.return_value = mock_updated
        mock_client.return_value = mock_cl

        result = update_task("T-CACHED", status="DONE")
        assert result is not None

        # Clean up
        _tasks_store.pop("T-CACHED", None)


# =====================================================================
# View component tests
# =====================================================================


class TestLinkSessionDialogView:
    """FEAT-011: Link Session dialog renders."""

    def test_build_link_session_dialog_importable(self):
        from agent.governance_ui.views.tasks.link_session_dialog import (
            build_link_session_dialog,
        )
        assert callable(build_link_session_dialog)

    def test_tasks_init_exports_link_session(self):
        from agent.governance_ui.views.tasks import build_link_session_dialog
        assert callable(build_link_session_dialog)


class TestLinkDocumentDialogView:
    """FEAT-012: Link Document dialog renders."""

    def test_build_link_document_dialog_importable(self):
        from agent.governance_ui.views.tasks.link_document_dialog import (
            build_link_document_dialog,
        )
        assert callable(build_link_document_dialog)

    def test_tasks_init_exports_link_document(self):
        from agent.governance_ui.views.tasks import build_link_document_dialog
        assert callable(build_link_document_dialog)


class TestTasksViewWiring:
    """Tasks view wires in new dialogs."""

    def test_tasks_view_imports_new_dialogs(self):
        from agent.governance_ui.views.tasks_view import build_tasks_view
        assert callable(build_tasks_view)


# =====================================================================
# State initialization tests
# =====================================================================


class TestStateInit:
    """New state variables are initialized."""

    def test_link_session_state_vars(self):
        from agent.governance_ui.state.initial import get_initial_state
        init = get_initial_state()
        assert 'show_link_session_dialog' in init
        assert init['show_link_session_dialog'] is False
        assert 'link_session_search' in init
        assert 'link_session_items' in init
        assert 'link_session_loading' in init

    def test_link_document_state_vars(self):
        from agent.governance_ui.state.initial import get_initial_state
        init = get_initial_state()
        assert 'show_link_document_dialog' in init
        assert init['show_link_document_dialog'] is False
        assert 'link_document_search' in init
        assert 'link_document_items' in init
        assert 'link_document_selected' in init
        assert 'link_document_loading' in init


# =====================================================================
# Constants test
# =====================================================================


class TestConstants:
    """FEAT-013: DEFAULT_WORKSPACE_ID constant exists."""

    def test_default_workspace_id_defined(self):
        from agent.governance_ui.state.constants import DEFAULT_WORKSPACE_ID
        assert DEFAULT_WORKSPACE_ID == "WS-9147535A"
