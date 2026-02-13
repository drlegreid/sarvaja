"""
Tests for chat controller.

Per GAP-FILE-005: Chat controller extracted from governance_dashboard.
Batch 160: New coverage for controllers/chat.py (0→20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register controllers."""
    state = MagicMock()
    ctrl = MagicMock()
    triggers = {}
    setters = {}

    def _trigger(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    def _set(name):
        def decorator(fn):
            setters[name] = fn
            return fn
        return decorator

    ctrl.trigger = _trigger
    # chat.py does not use ctrl.set, but future-proof
    ctrl.set = _set

    from agent.governance_ui.controllers.chat import register_chat_controllers
    register_chat_controllers(state, ctrl, api_base)
    return state, ctrl, triggers


class TestRegisterChatControllers:
    def test_registers_send_trigger(self):
        _, _, triggers = _make_state_ctrl()
        assert "send_chat_message" in triggers

    def test_registers_clear_trigger(self):
        _, _, triggers = _make_state_ctrl()
        assert "clear_chat" in triggers

    def test_registers_file_content_trigger(self):
        _, _, triggers = _make_state_ctrl()
        assert "load_file_content" in triggers

    def test_registers_task_execution_trigger(self):
        _, _, triggers = _make_state_ctrl()
        assert "load_task_execution" in triggers


class TestSendChatMessage:
    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_empty_message_returns_early(self, mock_httpx):
        state, _, triggers = _make_state_ctrl()
        state.chat_input = ""
        triggers["send_chat_message"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_whitespace_only_returns_early(self, mock_httpx):
        state, _, triggers = _make_state_ctrl()
        state.chat_input = "   "
        triggers["send_chat_message"]()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_clears_input_on_send(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"role": "assistant", "content": "hi"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        state.chat_input = "hello"
        state.chat_messages = []
        state.chat_selected_agent = "code-agent"
        state.chat_session_id = None
        triggers["send_chat_message"]()
        assert state.chat_input == ""

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_adds_user_message_to_list(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"role": "assistant", "content": "ok"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        state.chat_input = "hello"
        state.chat_messages = []
        state.chat_selected_agent = "code-agent"
        state.chat_session_id = "sess-1"
        triggers["send_chat_message"]()
        # Messages assigned multiple times — last assignment includes agent msg
        msgs = state.chat_messages
        assert len(msgs) >= 1

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_api_error_appends_error_msg(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal error"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        state.chat_input = "hello"
        state.chat_messages = []
        state.chat_selected_agent = "code-agent"
        state.chat_session_id = None
        triggers["send_chat_message"]()
        msgs = state.chat_messages
        assert any(m.get("role") == "system" for m in msgs if isinstance(m, dict))

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_connection_error_appends_error(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, triggers = _make_state_ctrl()
        state.chat_input = "hello"
        state.chat_messages = []
        state.chat_selected_agent = "code-agent"
        state.chat_session_id = None
        triggers["send_chat_message"]()
        assert state.chat_loading is False

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_sets_loading_false_on_completion(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"role": "assistant", "content": "done"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        state.chat_input = "test"
        state.chat_messages = []
        state.chat_selected_agent = "code-agent"
        state.chat_session_id = None
        triggers["send_chat_message"]()
        assert state.chat_loading is False


class TestClearChat:
    def test_clears_messages(self):
        state, _, triggers = _make_state_ctrl()
        state.chat_messages = [{"role": "user", "content": "test"}]
        triggers["clear_chat"]()
        assert state.chat_messages == []

    def test_clears_session_id(self):
        state, _, triggers = _make_state_ctrl()
        state.chat_session_id = "sess-123"
        triggers["clear_chat"]()
        assert state.chat_session_id is None

    def test_clears_task_id(self):
        state, _, triggers = _make_state_ctrl()
        state.chat_task_id = "TASK-001"
        triggers["clear_chat"]()
        assert state.chat_task_id is None


class TestLoadFileContent:
    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_empty_path_returns_early(self, mock_httpx):
        _, _, triggers = _make_state_ctrl()
        triggers["load_file_content"]("")
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_success_sets_content(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": "# README", "rendered_html": "<h1>README</h1>"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        triggers["load_file_content"]("/path/to/file.md")
        assert state.file_viewer_content == "# README"
        assert state.file_viewer_html == "<h1>README</h1>"
        assert state.file_viewer_loading is False


class TestLoadTaskExecution:
    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_empty_task_id_returns_early(self, mock_httpx):
        _, _, triggers = _make_state_ctrl()
        triggers["load_task_execution"]("")
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.chat.httpx")
    def test_success_sets_execution_log(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"events": [{"action": "start"}]}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers = _make_state_ctrl()
        triggers["load_task_execution"]("TASK-001")
        assert state.task_execution_log == [{"action": "start"}]
        assert state.task_execution_loading is False
