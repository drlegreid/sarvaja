"""
Unit tests for previously unhandled UI triggers.

Batch 133: Tests for 6 triggers that had no controller backing.
- trust.py: stop_agent_task, end_agent_session, register_agent, load_trust_history
- projects.py: select_project, create_project
"""

from unittest.mock import patch, MagicMock, PropertyMock
import pytest


# ── Agent control triggers (trust.py) ───────────────────


class TestStopAgentTask:

    def test_sets_status_message(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["stop_agent_task"]("code-agent")
        assert "stop" in state.status_message.lower() or "PAUSED" in state.status_message

    def test_noop_without_agent_id(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["stop_agent_task"](None)


class TestEndAgentSession:

    def test_sets_status_message(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["end_agent_session"]("code-agent")
        assert "session" in state.status_message.lower() or "PAUSED" in state.status_message


class TestRegisterAgent:

    @patch("httpx.Client")
    def test_success(self, mock_client_cls):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["register_agent"]("new-agent", "New Agent", "custom", "", "", "")
        assert "registered" in state.status_message

    def test_missing_name(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["register_agent"]("", "", "", "", "", "")
        assert "required" in state.status_message.lower()


class TestLoadTrustHistory:

    @patch("httpx.Client")
    def test_success(self, mock_client_cls):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect
        ctrl.set = trigger_side_effect

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "trust_score": 0.92,
            "tasks_executed": 15,
            "last_active": "2026-02-12T10:00:00",
        }
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        triggers["load_trust_history"]("code-agent")
        assert len(state.trust_history) == 1
        assert state.trust_history[0]["score"] == 0.92


# ── Project triggers (projects.py) ──────────────────────


class TestSelectProject:

    @patch("httpx.Client")
    def test_success(self, mock_client_cls):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        proj_response = MagicMock()
        proj_response.status_code = 200
        proj_response.json.return_value = {
            "project_id": "PROJ-1", "name": "Test"
        }

        sess_response = MagicMock()
        sess_response.status_code = 200
        sess_response.json.return_value = {"items": [{"session_id": "S-1"}]}

        mock_client.get.side_effect = [proj_response, sess_response]
        mock_client_cls.return_value = mock_client

        from agent.governance_ui.controllers.projects import register_project_controllers
        register_project_controllers(state, ctrl, "http://test:8082")

        triggers["select_project"]("PROJ-1")
        assert state.selected_project == {"project_id": "PROJ-1", "name": "Test"}
        assert state.project_sessions == [{"session_id": "S-1"}]

    def test_noop_without_project_id(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect

        from agent.governance_ui.controllers.projects import register_project_controllers
        register_project_controllers(state, ctrl, "http://test:8082")

        triggers["select_project"](None)


class TestCreateProject:

    def test_sets_status_message(self):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_side_effect(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_side_effect

        from agent.governance_ui.controllers.projects import register_project_controllers
        register_project_controllers(state, ctrl, "http://test:8082")

        triggers["create_project"]()
        assert "MCP" in state.status_message or "project" in state.status_message.lower()
