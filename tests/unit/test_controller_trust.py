"""
Tests for trust dashboard controller.

Per GAP-AGENT-PAUSE-001: Agent pause/resume toggle.
Batch 163: New coverage for controllers/trust.py (0→18 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register trust controllers."""
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
    ctrl.set = _set

    from agent.governance_ui.controllers.trust import register_trust_controllers
    register_trust_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, setters


class TestRegisterTrustControllers:
    def test_registers_select_agent(self):
        _, _, _, setters = _make_state_ctrl()
        assert "select_agent" in setters

    def test_registers_close_detail(self):
        _, _, _, setters = _make_state_ctrl()
        assert "close_agent_detail" in setters

    def test_registers_toggle_pause(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "toggle_agent_pause" in triggers

    def test_registers_register_agent(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "register_agent" in triggers

    def test_registers_load_trust_history(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "load_trust_history" in triggers

    def test_registers_stop_task(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "stop_agent_task" in triggers

    def test_registers_end_session(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "end_agent_session" in triggers


class TestSelectAgent:
    @patch("agent.governance_ui.controllers.trust.httpx")
    def test_selects_matching_agent(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"sessions": [], "pagination": {"total": 0}}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, _, setters = _make_state_ctrl()
        state.agents = [{"agent_id": "code-agent", "name": "Code"}]
        setters["select_agent"]("code-agent")
        assert state.show_agent_detail is True


class TestCloseAgentDetail:
    def test_closes_detail(self):
        state, _, _, setters = _make_state_ctrl()
        setters["close_agent_detail"]()
        assert state.selected_agent is None
        assert state.show_agent_detail is False


class TestToggleAgentPause:
    def test_empty_id_returns_early(self):
        _, _, triggers, _ = _make_state_ctrl()
        triggers["toggle_agent_pause"]("")

    @patch("agent.governance_ui.controllers.trust.httpx")
    def test_success_updates_agent(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"agent_id": "a1", "status": "ACTIVE"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.put.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.agents = [{"agent_id": "a1", "status": "PAUSED"}]
        triggers["toggle_agent_pause"]("a1")
        assert "ACTIVE" in str(state.status_message)


class TestRegisterAgent:
    def test_no_id_shows_message(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["register_agent"]("", "", "", "", "", "")
        assert "required" in str(state.status_message)

    @patch("agent.governance_ui.controllers.trust.httpx")
    def test_success_hides_form(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        triggers["register_agent"]("new-agent", "New", "custom", "", "", "")
        assert state.show_agent_registration is False


class TestLoadTrustHistory:
    def test_empty_id_returns_early(self):
        _, _, triggers, _ = _make_state_ctrl()
        triggers["load_trust_history"]("")

    @patch("agent.governance_ui.controllers.trust.httpx")
    def test_success_sets_history(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "last_active": "2026-02-13",
            "trust_score": 0.85,
            "tasks_executed": 42,
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        triggers["load_trust_history"]("code-agent")
        assert len(state.trust_history) == 1
        assert state.trust_history[0]["score"] == 0.85
