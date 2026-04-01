"""
Unit tests for Phase 5: Shared Traced HTTP Utilities.

EPIC-PERF-TELEM-V1 P5 — verifies:
1. traced_get records duration + status via add_api_trace
2. traced_get traces errors via add_error_trace and re-raises
3. traced_post captures request body
4. traced_put and traced_delete work
5. _safe_json handles non-JSON responses
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

_MOD = "agent.governance_ui.controllers.traced_http"


def _mock_response(status_code=200, json_data=None, text=""):
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = Exception("No JSON")
    resp.text = text
    return resp


def _mock_client(response=None):
    """Build a mock httpx.Client with configurable response."""
    client = MagicMock()
    if response is None:
        response = _mock_response(200, {"ok": True})
    client.get.return_value = response
    client.post.return_value = response
    client.put.return_value = response
    client.delete.return_value = response
    return client


class TestTracedGet:
    """Tests for traced_get()."""

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_records_duration_and_status(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        client = _mock_client(_mock_response(200, {"items": []}))
        resp, dur = traced_get(state, client, "http://api:8082", "/api/tasks")

        assert resp.status_code == 200
        assert dur >= 0
        mock_trace.assert_called_once()
        args, kwargs = mock_trace.call_args
        assert args[0] is state
        assert args[1] == "/api/tasks"
        assert args[2] == "GET"
        assert args[3] == 200
        assert isinstance(args[4], int)  # duration_ms

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_passes_params_to_client(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        client = _mock_client(_mock_response(200, {}))
        traced_get(state, client, "http://api:8082", "/api/tasks",
                   params={"limit": 20})

        client.get.assert_called_once_with(
            "http://api:8082/api/tasks", params={"limit": 20})

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_traces_errors_and_reraises(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        client = MagicMock()
        client.get.side_effect = ConnectionError("refused")

        with pytest.raises(ConnectionError):
            traced_get(state, client, "http://api:8082", "/api/tasks")

        mock_err.assert_called_once()
        assert "/api/tasks" in mock_err.call_args[0][1]
        mock_trace.assert_not_called()

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_captures_response_body(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        body = {"task_id": "T-1", "status": "DONE"}
        client = _mock_client(_mock_response(200, body))
        traced_get(state, client, "http://api:8082", "/api/tasks/T-1")

        call_kwargs = mock_trace.call_args[1]
        assert call_kwargs["response_body"] == body

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_handles_non_json_response(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_get

        state = MagicMock()
        resp = _mock_response(200, text="<html>error</html>")
        resp.json.side_effect = ValueError("not json")
        client = _mock_client(resp)
        traced_get(state, client, "http://api:8082", "/api/broken")

        call_kwargs = mock_trace.call_args[1]
        rb = call_kwargs["response_body"]
        assert rb is not None
        assert "_raw_text" in rb


class TestTracedPost:
    """Tests for traced_post()."""

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_captures_request_body(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_post

        state = MagicMock()
        req_body = {"description": "New task", "status": "TODO"}
        client = _mock_client(_mock_response(201, {"task_id": "T-NEW"}))
        resp, dur = traced_post(state, client, "http://api:8082",
                                "/api/tasks", json=req_body)

        assert resp.status_code == 201
        mock_trace.assert_called_once()
        args, kwargs = mock_trace.call_args
        assert args[2] == "POST"
        assert kwargs["request_body"] == req_body

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_post_traces_errors(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_post

        state = MagicMock()
        client = MagicMock()
        client.post.side_effect = TimeoutError("timed out")

        with pytest.raises(TimeoutError):
            traced_post(state, client, "http://api:8082", "/api/tasks",
                        json={"x": 1})

        mock_err.assert_called_once()
        assert "POST" in mock_err.call_args[0][1]


class TestTracedPut:
    """Tests for traced_put()."""

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_put_records_trace(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_put

        state = MagicMock()
        req_body = {"status": "DONE"}
        client = _mock_client(_mock_response(200, {"updated": True}))
        resp, dur = traced_put(state, client, "http://api:8082",
                               "/api/tasks/T-1", json=req_body)

        assert resp.status_code == 200
        args, kwargs = mock_trace.call_args
        assert args[2] == "PUT"
        assert kwargs["request_body"] == req_body


class TestTracedDelete:
    """Tests for traced_delete()."""

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_delete_records_trace(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_delete

        state = MagicMock()
        client = _mock_client(_mock_response(204))
        resp, dur = traced_delete(state, client, "http://api:8082",
                                  "/api/tasks/T-1")

        assert resp.status_code == 204
        args, kwargs = mock_trace.call_args
        assert args[1] == "/api/tasks/T-1"
        assert args[2] == "DELETE"
        assert args[3] == 204

    @patch(f"{_MOD}.add_api_trace")
    @patch(f"{_MOD}.add_error_trace")
    def test_delete_traces_errors(self, mock_err, mock_trace):
        from agent.governance_ui.controllers.traced_http import traced_delete

        state = MagicMock()
        client = MagicMock()
        client.delete.side_effect = ConnectionError("gone")

        with pytest.raises(ConnectionError):
            traced_delete(state, client, "http://api:8082", "/api/tasks/T-1")

        mock_err.assert_called_once()


class TestSafeJson:
    """Tests for _safe_json helper."""

    def test_returns_json_on_success(self):
        from agent.governance_ui.controllers.traced_http import _safe_json

        resp = _mock_response(200, {"key": "val"})
        assert _safe_json(resp) == {"key": "val"}

    def test_returns_raw_text_on_json_failure(self):
        from agent.governance_ui.controllers.traced_http import _safe_json

        resp = _mock_response(200, text="plain text body")
        resp.json.side_effect = ValueError("bad json")
        result = _safe_json(resp)
        assert result["_raw_text"] == "plain text body"

    def test_returns_none_on_empty_response(self):
        from agent.governance_ui.controllers.traced_http import _safe_json

        resp = _mock_response(204, text="")
        resp.json.side_effect = ValueError("no content")
        assert _safe_json(resp) is None
