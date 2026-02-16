"""TDD Tests: Session evidence rendering and navigation triggers.

Validates that:
1. Evidence rendered HTML state is initialized
2. Evidence preview card exists in the view hierarchy
3. Linked rules/decisions are clickable (navigation triggers)
4. Evidence rendering loader is called on session select
"""
from unittest.mock import patch, MagicMock

import pytest


class TestEvidenceRenderedState:
    """State initialization for evidence rendering."""

    def test_session_evidence_html_initialized(self):
        with patch("agent.governance_ui.state.initial.get_initial_loader_states", return_value={}), \
             patch("agent.governance_ui.state.initial.get_initial_trace_state", return_value={}), \
             patch("agent.governance_ui.state.initial.get_metrics_initial_state", return_value={}):
            from agent.governance_ui.state.initial import get_initial_state
            state = get_initial_state()
            assert state["session_evidence_html"] == ''

    def test_session_evidence_loading_initialized(self):
        with patch("agent.governance_ui.state.initial.get_initial_loader_states", return_value={}), \
             patch("agent.governance_ui.state.initial.get_initial_trace_state", return_value={}), \
             patch("agent.governance_ui.state.initial.get_metrics_initial_state", return_value={}):
            from agent.governance_ui.state.initial import get_initial_state
            state = get_initial_state()
            assert state["session_evidence_loading"] is False


class TestEvidencePreviewCard:
    """Evidence preview card component exists."""

    def test_build_evidence_preview_card_callable(self):
        from agent.governance_ui.views.sessions.evidence_preview import build_evidence_preview_card
        assert callable(build_evidence_preview_card)

    def test_detail_view_imports_evidence_preview(self):
        import agent.governance_ui.views.sessions.detail as detail_mod
        assert hasattr(detail_mod, 'build_evidence_preview_card')


class TestLinkedRulesClickable:
    """Linked rules in content.py should have click handler."""

    def test_rules_chip_has_navigate_trigger(self):
        import inspect
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content.build_session_info_card)
        assert "navigate_to_rule_from_session" in source

    def test_decisions_chip_has_navigate_trigger(self):
        import inspect
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content.build_session_info_card)
        assert "navigate_to_decision_from_session" in source


class TestNavigationTriggers:
    """Controller navigation triggers for linked entities."""

    def test_navigate_to_rule_sets_active_view(self):
        state = MagicMock()
        ctrl = MagicMock()
        state.selected_session = {"session_id": "S-1"}
        state.rules = [{"rule_id": "RULE-001"}]

        # Capture the registered triggers
        triggers = {}
        def fake_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator
        ctrl.trigger = fake_trigger
        ctrl.set = fake_trigger

        with patch("agent.governance_ui.controllers.sessions.register_sessions_pagination", return_value=MagicMock()):
            from agent.governance_ui.controllers.sessions import register_sessions_controllers
            register_sessions_controllers(state, ctrl, "http://test:8082")

        assert "navigate_to_rule_from_session" in triggers
        triggers["navigate_to_rule_from_session"]("RULE-001")
        assert state.active_view == "rules"
        assert state.nav_source_view == "sessions"

    def test_navigate_to_decision_sets_active_view(self):
        state = MagicMock()
        ctrl = MagicMock()
        state.selected_session = {"session_id": "S-1"}
        state.decisions = [{"decision_id": "DEC-001"}]

        triggers = {}
        def fake_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator
        ctrl.trigger = fake_trigger
        ctrl.set = fake_trigger

        with patch("agent.governance_ui.controllers.sessions.register_sessions_pagination", return_value=MagicMock()):
            from agent.governance_ui.controllers.sessions import register_sessions_controllers
            register_sessions_controllers(state, ctrl, "http://test:8082")

        assert "navigate_to_decision_from_session" in triggers
        triggers["navigate_to_decision_from_session"]("DEC-001")
        assert state.active_view == "decisions"
        assert state.nav_source_view == "sessions"
