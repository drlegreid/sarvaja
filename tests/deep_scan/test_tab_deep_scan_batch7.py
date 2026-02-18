"""
Unit tests for Tab Deep Scan Batch 7 fixes.

Covers: Missing state variables (decision options, executive sections),
decision form options/selected_option data flow.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.state.initial import get_initial_state


# ── Missing state variables added to initial.py ───────────────────


class TestDecisionFormStateVars:
    def test_form_decision_options_in_state(self):
        """form_decision_options must be in initial state."""
        state = get_initial_state()
        assert "form_decision_options" in state
        assert state["form_decision_options"] == []

    def test_form_decision_selected_option_in_state(self):
        """form_decision_selected_option must be in initial state."""
        state = get_initial_state()
        assert "form_decision_selected_option" in state
        assert state["form_decision_selected_option"] == ""


class TestExecutiveStateVars:
    def test_executive_expanded_sections_in_state(self):
        """executive_expanded_sections must be in initial state."""
        state = get_initial_state()
        assert "executive_expanded_sections" in state
        assert state["executive_expanded_sections"] == []


# ── Decision form: open_decision_form resets options ──────────────


class TestDecisionFormOpenReset:
    def _make_state_ctrl(self, api_base="http://localhost:8082"):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = _trigger

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, api_base)
        return state, ctrl, triggers

    def test_create_mode_clears_options(self):
        """open_decision_form('create') must clear options list."""
        state, _, triggers = self._make_state_ctrl()
        state.selected_decision = None
        triggers["open_decision_form"]("create")
        assert state.form_decision_options == []
        assert state.form_decision_selected_option == ""

    def test_edit_mode_populates_options(self):
        """open_decision_form('edit') must populate options from selection."""
        state, _, triggers = self._make_state_ctrl()
        state.selected_decision = {
            "decision_id": "DEC-001",
            "name": "Test",
            "options": ["Option A", "Option B"],
            "selected_option": "Option A",
        }
        triggers["open_decision_form"]("edit")
        assert state.form_decision_options == ["Option A", "Option B"]
        assert state.form_decision_selected_option == "Option A"

    def test_edit_mode_missing_options_defaults_empty(self):
        """open_decision_form('edit') handles missing options gracefully."""
        state, _, triggers = self._make_state_ctrl()
        state.selected_decision = {
            "decision_id": "DEC-002",
            "name": "No Options",
        }
        triggers["open_decision_form"]("edit")
        assert state.form_decision_options == []
        assert state.form_decision_selected_option == ""


# ── Decision submit includes options ──────────────────────────────


class TestDecisionSubmitIncludesOptions:
    @patch("agent.governance_ui.controllers.decisions.httpx")
    def test_submit_sends_options(self, mock_httpx):
        """submit_decision_form must include options in payload."""
        mock_resp_create = MagicMock()
        mock_resp_create.status_code = 201
        mock_resp_reload = MagicMock()
        mock_resp_reload.status_code = 200
        mock_resp_reload.json.return_value = {"items": []}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp_create
        mock_client.get.return_value = mock_resp_reload
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        state.is_loading = False
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = _trigger

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")

        state.decision_form_mode = "create"
        state.form_decision_id = "DEC-TEST"
        state.form_decision_name = "Test"
        state.form_decision_context = "ctx"
        state.form_decision_rationale = "reason"
        state.form_decision_status = "APPROVED"
        state.form_decision_options = ["Opt A", "Opt B"]
        state.form_decision_selected_option = "Opt A"

        triggers["submit_decision_form"]()

        # Verify POST was called with options
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else None
        if payload is None:
            payload = call_args.kwargs.get("json", {})
        assert payload.get("options") == ["Opt A", "Opt B"]
        assert payload.get("selected_option") == "Opt A"


# ── Existing state vars still present (regression guard) ──────────


class TestStateVarsNotRemoved:
    """Ensure previously-added state vars weren't accidentally removed."""

    def test_trust_history(self):
        assert "trust_history" in get_initial_state()

    def test_show_agent_registration(self):
        assert "show_agent_registration" in get_initial_state()

    def test_dependency_overview(self):
        assert "dependency_overview" in get_initial_state()

    def test_edit_task_mode(self):
        assert "edit_task_mode" in get_initial_state()

    def test_session_transcript(self):
        assert "session_transcript" in get_initial_state()

    def test_session_transcript_loading(self):
        assert "session_transcript_loading" in get_initial_state()
