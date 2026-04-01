"""
Unit tests for Phase 5: Task CRUD Tracing + Dashboard Audit Logging.

EPIC-PERF-TELEM-V1 P5 — verifies:
1. select_task emits api trace for /api/tasks/{id}
2. select_task calls log_action("tasks", "select")
3. create_task emits trace for POST /api/tasks
4. create_task calls log_action("tasks", "create")
5. submit_task_edit emits trace for PUT /api/tasks/{id}
6. submit_task_edit calls log_action("tasks", "update")
7. delete_task emits trace for DELETE /api/tasks/{id}
8. delete_task calls log_action("tasks", "delete")
9. Session detail loaders emit api traces
"""

from unittest.mock import MagicMock, patch, call

import pytest

_MOD = "agent.governance_ui.controllers.tasks_crud"
_TRACED = "agent.governance_ui.controllers.traced_http"


def _make_mock_httpx(responses=None, task_id="T-1"):
    """Build injectable httpx module with configurable per-URL responses."""
    defaults = {
        f"/api/tasks/{task_id}/execution": (200, {"events": [{"event": "started"}]}),
        f"/api/tasks/{task_id}/evidence/rendered": (200, {"evidence_files": []}),
        f"/api/tasks/{task_id}/timeline": (200, {"entries": [], "total": 0, "has_more": False}),
        f"/api/tasks/{task_id}/comments": (200, {"comments": []}),
        f"/api/tasks/{task_id}": (200, {"task_id": task_id, "title": "Test"}),
        "/api/tasks": (200, {"items": [], "pagination": {"total": 0}}),
    }
    if responses:
        defaults.update(responses)

    def _mock_get(url, **kwargs):
        resp = MagicMock()
        path = url.split("?")[0]
        for substr in sorted(defaults.keys(), key=len, reverse=True):
            if path.endswith(substr):
                code, data = defaults[substr]
                resp.status_code = code
                resp.json.return_value = data
                resp.text = ""
                return resp
        resp.status_code = 404
        resp.json.return_value = {}
        resp.text = ""
        return resp

    def _mock_post(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 201
        resp.json.return_value = {"task_id": "T-NEW"}
        resp.text = ""
        return resp

    def _mock_put(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"task_id": task_id, "status": "DONE"}
        resp.text = ""
        return resp

    def _mock_delete(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 204
        resp.json.return_value = {}
        resp.text = ""
        return resp

    mock_httpx = MagicMock()
    mock_client = MagicMock()
    mock_client.get.side_effect = _mock_get
    mock_client.post.side_effect = _mock_post
    mock_client.put.side_effect = _mock_put
    mock_client.delete.side_effect = _mock_delete
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_httpx.Client.return_value = mock_client
    return mock_httpx


def _make_state(**overrides):
    """Build a mock Trame state."""
    state = MagicMock()
    state.tasks = []
    state.is_loading = False
    state.selected_task = {"task_id": "T-1", "id": "T-1", "title": "Test"}
    state.edit_task_description = "Updated"
    state.edit_task_phase = "P10"
    state.edit_task_status = "TODO"
    state.edit_task_agent = ""
    state.edit_task_body = ""
    state.form_task_id = "T-NEW"
    state.form_task_description = "New task"
    state.form_task_phase = "P10"
    state.form_task_type = "bug"
    state.form_task_agent = ""
    state.form_task_body = ""
    state.form_task_priority = None
    state.tasks_per_page = 20
    state.tasks_page = 1
    for k, v in overrides.items():
        setattr(state, k, v)
    return state


def _make_ctrl():
    """Build mock ctrl that captures trigger registrations."""
    ctrl = MagicMock()
    triggers = {}

    def _trigger(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = _trigger
    ctrl._triggers = triggers
    return ctrl


def _register(state=None, responses=None, task_id="T-1"):
    """Register tasks_crud and return (state, ctrl, triggers, mock_trace, mock_log)."""
    from agent.governance_ui.controllers.tasks_crud import register_tasks_crud

    if state is None:
        state = _make_state()
    ctrl = _make_ctrl()
    mock_httpx = _make_mock_httpx(responses, task_id)
    mock_error_trace = MagicMock()

    register_tasks_crud(state, ctrl, "http://api:8082",
                        httpx_mod=mock_httpx, error_trace_fn=mock_error_trace)
    return state, ctrl, ctrl._triggers, mock_error_trace


class TestSelectTaskTracing:
    """select_task should emit API traces and log_action."""

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_select_task_emits_api_trace(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["select_task"]("T-1")

        # traced_get calls add_api_trace for each HTTP call
        assert mock_trace.call_count >= 1
        endpoints = [c[0][1] for c in mock_trace.call_args_list]
        assert any("/api/tasks/T-1" in ep for ep in endpoints)

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_select_task_calls_log_action(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["select_task"]("T-1")

        mock_log.assert_called_once_with("tasks", "select", task_id="T-1")

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_select_task_traces_all_sub_loaders(self, mock_log, mock_trace):
        """All 4 parallel sub-loaders should produce traces."""
        state, ctrl, triggers, _ = _register()
        triggers["select_task"]("T-1")

        endpoints = [c[0][1] for c in mock_trace.call_args_list]
        assert any("execution" in ep for ep in endpoints)
        assert any("evidence" in ep for ep in endpoints)
        assert any("timeline" in ep for ep in endpoints)
        assert any("comments" in ep for ep in endpoints)


class TestCreateTaskTracing:
    """create_task should emit API traces and log_action."""

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_create_task_emits_trace(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["create_task"]()

        assert mock_trace.call_count >= 1
        methods = [c[0][2] for c in mock_trace.call_args_list]
        assert "POST" in methods

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_create_task_calls_log_action(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["create_task"]()

        mock_log.assert_called_once_with("tasks", "create")


class TestSubmitTaskEditTracing:
    """submit_task_edit should emit API traces and log_action."""

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_submit_edit_emits_trace(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["submit_task_edit"]()

        assert mock_trace.call_count >= 1
        methods = [c[0][2] for c in mock_trace.call_args_list]
        assert "PUT" in methods

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_submit_edit_calls_log_action(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["submit_task_edit"]()

        mock_log.assert_called_once_with("tasks", "update", task_id="T-1")


class TestDeleteTaskTracing:
    """delete_task should emit API traces and log_action."""

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_delete_emits_trace(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["delete_task"]()

        assert mock_trace.call_count >= 1
        methods = [c[0][2] for c in mock_trace.call_args_list]
        assert "DELETE" in methods

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_MOD}.log_action")
    def test_delete_calls_log_action(self, mock_log, mock_trace):
        state, ctrl, triggers, _ = _register()
        triggers["delete_task"]()

        mock_log.assert_called_once_with("tasks", "delete", task_id="T-1")


class TestSessionDetailLoaderTracing:
    """All 8 session detail loaders should emit API traces."""

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_TRACED}.add_error_trace")
    def test_fetch_tool_calls_emits_trace(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        state.session_transcript_include_thinking = True
        state.session_transcript_include_user = True
        loaders = register_session_detail_loaders(state, "http://api:8082")

        with patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx") as mock_httpx:
            mock_client = MagicMock()
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"tool_calls": []}
            resp.text = ""
            mock_client.get.return_value = resp
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_httpx.Client.return_value = mock_client

            loaders["fetch_tool_calls"]("SESSION-TEST-1")

        assert mock_trace.call_count >= 1
        endpoints = [c[0][1] for c in mock_trace.call_args_list]
        assert any("/tools" in ep for ep in endpoints)

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_TRACED}.add_error_trace")
    def test_fetch_evidence_rendered_emits_trace(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        loaders = register_session_detail_loaders(state, "http://api:8082")

        with patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx") as mock_httpx:
            mock_client = MagicMock()
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"html": "<p>evidence</p>"}
            resp.text = ""
            mock_client.get.return_value = resp
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_httpx.Client.return_value = mock_client

            loaders["fetch_evidence_rendered"]("SESSION-TEST-1")

        assert mock_trace.call_count >= 1
        endpoints = [c[0][1] for c in mock_trace.call_args_list]
        assert any("evidence/rendered" in ep for ep in endpoints)

    @patch(f"{_TRACED}.add_api_trace")
    @patch(f"{_TRACED}.add_error_trace")
    def test_fetch_tasks_emits_trace(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )

        state = MagicMock()
        loaders = register_session_detail_loaders(state, "http://api:8082")

        with patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx") as mock_httpx:
            mock_client = MagicMock()
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"tasks": []}
            resp.text = ""
            mock_client.get.return_value = resp
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_httpx.Client.return_value = mock_client

            loaders["fetch_tasks"]("SESSION-TEST-1")

        assert mock_trace.call_count >= 1
