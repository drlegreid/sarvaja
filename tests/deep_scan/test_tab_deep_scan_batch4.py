"""
Unit tests for Tab Deep Scan Batch 4 fixes.

Covers:
- BUG-FORM-EDIT-001: Edit form population via trigger (sessions, decisions, rules)
- Sessions detail loaders: add_error_trace on all exception handlers
- Sessions pagination: add_error_trace on timeline/pivot exceptions
- Session close_session_detail properly registered as trigger
- Delete/submit buttons use trigger() pattern

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Sessions: Edit form via trigger ──────────────────────────────────


class TestSessionEditFormTrigger:
    def test_open_session_form_is_trigger(self):
        """open_session_form should be registered as @ctrl.trigger."""
        from agent.governance_ui.controllers.sessions import (
            register_sessions_controllers,
        )

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)

        with patch("agent.governance_ui.controllers.sessions_pagination.register_sessions_pagination",
                    return_value=MagicMock()):
            with patch("agent.governance_ui.controllers.sessions_detail_loaders.register_session_detail_loaders",
                        return_value={"load_evidence": MagicMock(), "load_tasks": MagicMock(),
                                      "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
                                      "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
                                      "load_transcript": MagicMock(), "load_transcript_entry": MagicMock()}):
                register_sessions_controllers(state, ctrl, "http://test:8082")

        assert "open_session_form" in triggers

    def test_open_session_form_edit_populates_fields(self):
        """Edit mode should populate form fields from selected_session."""
        from agent.governance_ui.controllers.sessions import (
            register_sessions_controllers,
        )

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)
        state.selected_session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "description": "Test session",
            "status": "COMPLETED",
            "agent_id": "code-agent",
        }

        with patch("agent.governance_ui.controllers.sessions_pagination.register_sessions_pagination",
                    return_value=MagicMock()):
            with patch("agent.governance_ui.controllers.sessions_detail_loaders.register_session_detail_loaders",
                        return_value={"load_evidence": MagicMock(), "load_tasks": MagicMock(),
                                      "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
                                      "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
                                      "load_transcript": MagicMock(), "load_transcript_entry": MagicMock()}):
                register_sessions_controllers(state, ctrl, "http://test:8082")

        triggers["open_session_form"]("edit")

        assert state.session_form_mode == "edit"
        assert state.form_session_id == "SESSION-2026-02-15-TEST"
        assert state.form_session_description == "Test session"
        assert state.form_session_status == "COMPLETED"
        assert state.form_session_agent_id == "code-agent"
        assert state.show_session_form is True

    def test_open_session_form_create_clears_fields(self):
        """Create mode should clear all form fields."""
        from agent.governance_ui.controllers.sessions import (
            register_sessions_controllers,
        )

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)

        with patch("agent.governance_ui.controllers.sessions_pagination.register_sessions_pagination",
                    return_value=MagicMock()):
            with patch("agent.governance_ui.controllers.sessions_detail_loaders.register_session_detail_loaders",
                        return_value={"load_evidence": MagicMock(), "load_tasks": MagicMock(),
                                      "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
                                      "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
                                      "load_transcript": MagicMock(), "load_transcript_entry": MagicMock()}):
                register_sessions_controllers(state, ctrl, "http://test:8082")

        triggers["open_session_form"]("create")

        assert state.form_session_id == ""
        assert state.form_session_description == ""
        assert state.show_session_form is True


class TestSessionDetailViewTriggers:
    def test_detail_edit_uses_trigger(self):
        """Session detail edit button should use trigger('open_session_form')."""
        from agent.governance_ui.views.sessions import detail

        source = inspect.getsource(detail)
        assert "trigger('open_session_form', ['edit'])" in source
        # Should NOT have inline state manipulation
        assert "session_form_mode = 'edit'; show_session_form = true" not in source

    def test_detail_delete_uses_trigger(self):
        """Session detail delete button should use trigger('delete_session')."""
        from agent.governance_ui.views.sessions import detail

        source = inspect.getsource(detail)
        assert "trigger('delete_session')" in source

    def test_list_add_uses_trigger(self):
        """Session list add button should use trigger('open_session_form')."""
        from agent.governance_ui.views.sessions import list as sessions_list

        source = inspect.getsource(sessions_list)
        assert "trigger('open_session_form', ['create'])" in source

    def test_form_save_uses_trigger(self):
        """Session form save button should use trigger('submit_session_form')."""
        from agent.governance_ui.views.sessions import form

        source = inspect.getsource(form)
        assert "trigger('submit_session_form')" in source

    def test_form_cancel_uses_trigger(self):
        """Session form cancel button should use trigger('close_session_form')."""
        from agent.governance_ui.views.sessions import form

        source = inspect.getsource(form)
        assert "trigger('close_session_form')" in source
        # Should NOT have inline state manipulation
        assert "show_session_form = false" not in source


# ── Decisions: Edit form via trigger ─────────────────────────────────


class TestDecisionEditFormTrigger:
    def test_open_decision_form_is_trigger(self):
        """open_decision_form should be registered as @ctrl.trigger."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert '@ctrl.trigger("open_decision_form")' in source

    def test_detail_edit_uses_trigger(self):
        """Decision detail edit button should use trigger pattern."""
        from agent.governance_ui.views.decisions import detail

        source = inspect.getsource(detail)
        assert "trigger('open_decision_form', ['edit'])" in source
        assert "decision_form_mode = 'edit'; show_decision_form = true" not in source

    def test_detail_delete_uses_trigger(self):
        """Decision detail delete button should use trigger pattern."""
        from agent.governance_ui.views.decisions import detail

        source = inspect.getsource(detail)
        assert "trigger('delete_decision')" in source

    def test_list_add_uses_trigger(self):
        """Decision list add button should use trigger pattern."""
        from agent.governance_ui.views.decisions import list as decisions_list

        source = inspect.getsource(decisions_list)
        assert "trigger('open_decision_form', ['create'])" in source

    def test_form_cancel_uses_trigger(self):
        """Decision form cancel should use trigger."""
        from agent.governance_ui.views.decisions import form

        source = inspect.getsource(form)
        assert "trigger('close_decision_form')" in source
        assert "show_decision_form = false" not in source

    def test_form_save_uses_trigger(self):
        """Decision form save should use trigger."""
        from agent.governance_ui.views.decisions import form

        source = inspect.getsource(form)
        assert "trigger('submit_decision_form')" in source


# ── Rules: consistent trigger pattern ────────────────────────────────


class TestRulesDetailTriggers:
    def test_detail_delete_uses_trigger(self):
        """Rules detail delete button should use trigger pattern."""
        from agent.governance_ui.views import rules_view_detail

        source = inspect.getsource(rules_view_detail)
        assert "trigger('delete_rule')" in source

    def test_detail_back_uses_trigger(self):
        """Rules detail back button should use trigger('close_rule_detail')."""
        from agent.governance_ui.views import rules_view_detail

        source = inspect.getsource(rules_view_detail)
        assert "trigger('close_rule_detail')" in source
        # Should NOT have raw state manipulation for the standard back button
        assert 'click="show_rule_detail = false; selected_rule = null"' not in source

    def test_form_cancel_uses_trigger(self):
        """Rules form cancel should use trigger."""
        from agent.governance_ui.views import rules_view

        source = inspect.getsource(rules_view)
        assert "trigger('close_rule_form')" in source
        assert "show_rule_form = false" not in source

    def test_form_save_uses_trigger(self):
        """Rules form save should use trigger."""
        from agent.governance_ui.views import rules_view

        source = inspect.getsource(rules_view)
        assert "trigger('submit_rule_form')" in source


# ── Sessions Detail Loaders: trace calls ─────────────────────────────


class TestSessionDetailLoadersTrace:
    def test_has_add_error_trace_import(self):
        """sessions_detail_loaders should import add_error_trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "from agent.governance_ui.trace_bar.transforms import add_error_trace" in source

    def test_tool_calls_has_trace(self):
        """load_session_tool_calls exception should trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Load tool calls failed" in source

    def test_thinking_items_has_trace(self):
        """load_session_thinking_items exception should trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Load thinking items failed" in source

    def test_evidence_rendered_has_trace(self):
        """load_session_evidence_rendered exception should trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Load evidence rendered failed" in source

    def test_evidence_files_has_trace(self):
        """load_session_evidence exception should trace (was pass)."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Load evidence files failed" in source

    def test_transcript_has_trace(self):
        """load_session_transcript exception should trace."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Load transcript failed" in source

    def test_transcript_entry_has_trace(self):
        """load_transcript_entry_expanded exception should trace (was pass)."""
        from agent.governance_ui.controllers import sessions_detail_loaders

        source = inspect.getsource(sessions_detail_loaders)
        assert "Expand transcript entry failed" in source


# ── Sessions Pagination: trace calls ─────────────────────────────────


class TestSessionPaginationTrace:
    def test_has_add_error_trace_import(self):
        """sessions_pagination should import add_error_trace."""
        from agent.governance_ui.controllers import sessions_pagination

        source = inspect.getsource(sessions_pagination)
        assert "from agent.governance_ui.trace_bar.transforms import add_error_trace" in source

    def test_timeline_metrics_has_trace(self):
        """_update_timeline_and_metrics exception should trace (was pass)."""
        from agent.governance_ui.controllers import sessions_pagination

        source = inspect.getsource(sessions_pagination)
        assert "Load timeline/metrics failed" in source

    def test_pivot_has_trace(self):
        """_compute_pivot exception should trace."""
        from agent.governance_ui.controllers import sessions_pagination

        source = inspect.getsource(sessions_pagination)
        assert "Compute pivot failed" in source


# ── Sessions.py: select_session trace ────────────────────────────────


class TestSessionSelectTrace:
    def test_select_session_has_trace(self):
        """select_session API error should trace (was pass)."""
        from agent.governance_ui.controllers import sessions

        source = inspect.getsource(sessions)
        assert "Load session detail failed" in source
        assert "add_error_trace" in source
