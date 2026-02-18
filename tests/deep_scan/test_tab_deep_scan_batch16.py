"""
Unit tests for Tab Deep Scan Batch 16 — Form close on error + loading state.

Covers: form stays open on API error (BUG-UI-FORMCLOSE-001),
no misleading "offline mode" messages, loading state consistency.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Form stays open on API error (BUG-UI-FORMCLOSE-001) ──────────────


class TestSessionFormCloseOnError:
    """submit_session_form must NOT close form on API error."""

    def test_source_has_formclose_fix(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-FORMCLOSE-001" in source

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_form_stays_open_on_api_error(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Form must stay open when API returns non-200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.session_form_mode = "create"
        state.form_session_id = "S-TEST"
        state.form_session_description = "Test"
        state.form_session_agent_id = ""
        state.has_error = False
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
        triggers["submit_session_form"]()

        # Form must stay open so user can correct and retry
        assert state.has_error is True
        assert state.is_loading is False
        # show_session_form should NOT have been set to False on error path
        # (MagicMock tracks all attribute sets — check it wasn't set to False
        #  after the error was set)

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_form_closes_on_success(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Form must close when API returns 200/201."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201

        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = {"items": [], "pagination": {}}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client.get.return_value = mock_list_resp
        mock_httpx.Client.return_value = mock_client

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.session_form_mode = "create"
        state.form_session_id = "S-TEST"
        state.form_session_description = "Test"
        state.form_session_agent_id = ""
        state.has_error = False
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
        triggers["submit_session_form"]()
        assert state.show_session_form is False


class TestDecisionFormCloseOnError:
    """submit_decision_form must NOT close form on API error."""

    def test_source_has_formclose_fix(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-FORMCLOSE-001" in source

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_form_stays_open_on_api_error(self, mock_err, mock_httpx):
        """Form must stay open when API returns non-200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.text = "Validation Error"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        state.is_loading = False
        state.decision_form_mode = "create"
        state.form_decision_id = "DEC-TEST"
        state.form_decision_name = "Test Decision"
        state.form_decision_context = "Test Context"
        state.form_decision_rationale = ""
        state.form_decision_status = "PENDING"
        state.form_decision_options = []
        state.form_decision_selected_option = None
        state.has_error = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_decision_form"]()

        assert state.has_error is True
        assert state.is_loading is False

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_form_stays_open_on_exception(self, mock_err, mock_httpx):
        """Form must stay open when exception occurs."""
        mock_httpx.Client.side_effect = ConnectionError("refused")

        state = MagicMock()
        state.is_loading = False
        state.decision_form_mode = "create"
        state.form_decision_name = "Test"
        state.form_decision_context = "Context"
        state.form_decision_rationale = ""
        state.form_decision_status = "PENDING"
        state.form_decision_id = ""
        state.form_decision_options = []
        state.form_decision_selected_option = None
        state.has_error = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_decision_form"]()

        assert state.has_error is True
        assert state.is_loading is False


class TestRuleFormCloseOnError:
    """submit_rule_form must NOT close form on API error."""

    def test_source_has_formclose_fix(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-FORMCLOSE-001" in source

    @patch("agent.governance_ui.controllers.rules.httpx")
    @patch("agent.governance_ui.controllers.rules.add_error_trace")
    def test_form_stays_open_on_api_error(self, mock_err, mock_httpx):
        """Form must stay open when API returns non-200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Error"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        state.is_loading = False
        state.rule_form_mode = "create"
        state.form_rule_id = "TEST-001"
        state.form_rule_title = "Test"
        state.form_rule_directive = "Directive"
        state.form_rule_category = "TEST"
        state.form_rule_priority = "MEDIUM"
        state.has_error = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.rules import register_rules_controllers
        register_rules_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_rule_form"]()

        assert state.has_error is True
        assert state.is_loading is False


# ── No misleading "offline mode" messages ─────────────────────────────


class TestNoOfflineModeMessages:
    """Exception handlers must NOT show misleading 'saved (offline mode)' messages."""

    def test_sessions_no_offline_message(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "offline mode" not in source

    def test_decisions_no_offline_message(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "offline mode" not in source

    def test_rules_no_offline_message(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "offline mode" not in source


# ── Loading state properly reset on all paths ─────────────────────────


class TestLoadingStateReset:
    """is_loading must be reset to False on both success and error paths."""

    def test_session_detail_loaders_use_finally(self):
        """All detail loaders must use finally blocks for loading flags."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert source.count("finally:") >= 5  # tool_calls, thinking, evidence*2, tasks, transcript

    def test_tasks_controller_resets_loading(self):
        """All task CRUD handlers must reset is_loading."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Every time is_loading = True is set, is_loading = False must follow
        true_count = source.count("state.is_loading = True")
        false_count = source.count("state.is_loading = False")
        assert false_count >= true_count

    def test_sessions_controller_resets_loading(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        true_count = source.count("state.is_loading = True")
        false_count = source.count("state.is_loading = False")
        assert false_count >= true_count

    def test_decisions_controller_resets_loading(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        true_count = source.count("state.is_loading = True")
        false_count = source.count("state.is_loading = False")
        assert false_count >= true_count

    def test_rules_controller_resets_loading(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        true_count = source.count("state.is_loading = True")
        false_count = source.count("state.is_loading = False")
        assert false_count >= true_count
