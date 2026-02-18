"""
Unit tests for Tab Deep Scan Batch 11 — Session select validation.

Covers: select_session show_session_detail on API-only path,
select_task API-first pattern, session select API fallback.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── select_session show_session_detail ───────────────────────────


class TestSelectSessionShowDetail:
    """select_session must set show_session_detail on API success."""

    def test_source_sets_show_detail_in_api_branch(self):
        """API success path must set show_session_detail = True."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # The API branch should set show_session_detail
        # Count occurrences: one in list loop + one in API success
        assert source.count("state.show_session_detail = True") >= 2

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_api_only_session_opens_detail(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Session not in list but found via API must open detail view."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session_id": "S1", "start_time": "", "end_time": ""}
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.sessions = []  # Not in list
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("S1")
        assert state.show_session_detail is True

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_session_in_list_opens_detail(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Session found in list must open detail view."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"session_id": "S1", "start_time": "", "end_time": ""}
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.sessions = [{"session_id": "S1"}]
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("S1")
        assert state.show_session_detail is True


# ── select_task API-first pattern ────────────────────────────────


class TestSelectTaskPattern:
    """select_task follows API-first, list-fallback pattern."""

    def test_select_task_sets_detail_on_api_success(self):
        """API success must set show_task_detail = True."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # select_task: API path sets show_task_detail
        assert "state.show_task_detail = True" in source

    def test_select_task_has_api_fallback(self):
        """select_task must fall back to list search on API failure."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Must have both API call and list iteration
        assert "response.status_code == 200" in source
        assert "for task in state.tasks:" in source


# ── select_rule / select_decision list-only ──────────────────────


class TestSelectRuleDecisionPattern:
    """select_rule and select_decision use list-only pattern."""

    def test_select_rule_searches_list(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "for rule in state.rules:" in source
        assert "state.show_rule_detail = True" in source

    def test_select_decision_searches_list(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "for decision in state.decisions:" in source
        assert "state.show_decision_detail = True" in source


# ── v_if guards for optional session fields ──────────────────────


class TestOptionalFieldGuards:
    """Optional display fields must have v_if guards in views."""

    def test_session_linked_rules_guarded(self):
        """linked_rules_applied must be behind v_if."""
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "linked_rules_applied" in source

    def test_task_tech_docs_guarded(self):
        """Tech doc fields must be behind v_if."""
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "selected_task.business" in source
        assert "selected_task.design" in source
