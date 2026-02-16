"""
Unit tests for Tab Deep Scan Batch 5 fixes.

Covers:
- data_loaders.py: Untraced exceptions (proposals, escalated_proposals, backlog)
- data_loaders_refresh.py: load_sessions_list untraced exception
- trust.py: @ctrl.set → @ctrl.trigger for select_agent, close_agent_detail
- decisions.py: @ctrl.set → @ctrl.trigger for select_decision, close_decision_detail
- monitor.py: @ctrl.set → @ctrl.trigger for filter_monitor_events, acknowledge_alert
- impact.py: @ctrl.set → @ctrl.trigger for toggle_graph_view
- rules.py: show_rule_form → open_rule_form with form field clearing
- Agent views: inline state manipulation → trigger() calls
- Decision list: inline state manipulation → trigger() for select
- Trust panels: inline state manipulation → trigger() for select
- Monitor view: inline state manipulation → trigger() for filter/acknowledge

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── data_loaders.py: traced exceptions ───────────────────────────────


class TestDataLoadersTraceExceptions:
    def test_proposals_has_trace(self):
        """get_proposals() failure should trace."""
        from agent.governance_ui.controllers import data_loaders

        source = inspect.getsource(data_loaders)
        assert "Load proposals failed" in source

    def test_escalated_proposals_has_trace(self):
        """get_escalated_proposals() failure should trace."""
        from agent.governance_ui.controllers import data_loaders

        source = inspect.getsource(data_loaders)
        assert "Load escalated proposals failed" in source

    def test_backlog_has_trace(self):
        """load_backlog_data() failure should trace."""
        from agent.governance_ui.controllers import data_loaders

        source = inspect.getsource(data_loaders)
        assert "Load backlog failed" in source


class TestDataLoadersRefreshTrace:
    def test_load_sessions_list_has_trace(self):
        """load_sessions_list() failure should trace."""
        from agent.governance_ui.controllers import data_loaders_refresh

        source = inspect.getsource(data_loaders_refresh)
        assert "Load sessions list failed" in source


# ── trust.py: @ctrl.trigger conversions ──────────────────────────────


class TestTrustTriggerConversions:
    def test_select_agent_is_trigger(self):
        """select_agent should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import trust

        source = inspect.getsource(trust)
        assert '@ctrl.trigger("select_agent")' in source
        assert '@ctrl.set("select_agent")' not in source

    def test_close_agent_detail_is_trigger(self):
        """close_agent_detail should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import trust

        source = inspect.getsource(trust)
        assert '@ctrl.trigger("close_agent_detail")' in source
        assert '@ctrl.set("close_agent_detail")' not in source


# ── decisions.py: @ctrl.trigger conversions ──────────────────────────


class TestDecisionsTriggerConversions:
    def test_select_decision_is_trigger(self):
        """select_decision should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert '@ctrl.trigger("select_decision")' in source
        assert '@ctrl.set("select_decision")' not in source

    def test_close_decision_detail_is_trigger(self):
        """close_decision_detail should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert '@ctrl.trigger("close_decision_detail")' in source
        assert '@ctrl.set("close_decision_detail")' not in source


# ── monitor.py: @ctrl.trigger conversions ────────────────────────────


class TestMonitorTriggerConversions:
    def test_filter_monitor_events_is_trigger(self):
        """filter_monitor_events should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import monitor

        source = inspect.getsource(monitor)
        assert '@ctrl.trigger("filter_monitor_events")' in source
        assert '@ctrl.set("filter_monitor_events")' not in source

    def test_acknowledge_alert_is_trigger(self):
        """acknowledge_alert should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import monitor

        source = inspect.getsource(monitor)
        assert '@ctrl.trigger("acknowledge_alert")' in source
        assert '@ctrl.set("acknowledge_alert")' not in source


# ── impact.py: @ctrl.trigger conversion ──────────────────────────────


class TestImpactTriggerConversion:
    def test_toggle_graph_view_is_trigger(self):
        """toggle_graph_view should be @ctrl.trigger, not @ctrl.set."""
        from agent.governance_ui.controllers import impact

        source = inspect.getsource(impact)
        assert '@ctrl.trigger("toggle_graph_view")' in source
        assert '@ctrl.set("toggle_graph_view")' not in source


# ── rules.py: open_rule_form with field clearing ─────────────────────


class TestRulesOpenFormTrigger:
    def test_open_rule_form_is_trigger(self):
        """open_rule_form should be @ctrl.trigger (renamed from show_rule_form)."""
        from agent.governance_ui.controllers import rules

        source = inspect.getsource(rules)
        assert '@ctrl.trigger("open_rule_form")' in source
        assert '@ctrl.set("show_rule_form")' not in source

    def test_open_rule_form_clears_fields_on_create(self):
        """Create mode should clear all form fields."""
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def fake_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator
        ctrl.trigger = fake_trigger
        ctrl.set = fake_trigger

        def fake_change(*names):
            def decorator(fn):
                return fn
            return decorator
        state.change = fake_change

        with patch("agent.governance_ui.controllers.rules.httpx"):
            from agent.governance_ui.controllers.rules import register_rules_controllers
            register_rules_controllers(state, ctrl, "http://test:8082")

        triggers["open_rule_form"]("create")
        assert state.form_rule_id == ""
        assert state.form_rule_title == ""
        assert state.form_rule_directive == ""
        assert state.show_rule_form is True

    def test_open_rule_form_populates_on_edit(self):
        """Edit mode should populate form from selected_rule."""
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def fake_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator
        ctrl.trigger = fake_trigger
        ctrl.set = fake_trigger

        def fake_change(*names):
            def decorator(fn):
                return fn
            return decorator
        state.change = fake_change

        with patch("agent.governance_ui.controllers.rules.httpx"):
            from agent.governance_ui.controllers.rules import register_rules_controllers
            register_rules_controllers(state, ctrl, "http://test:8082")

        state.selected_rule = {
            "rule_id": "TEST-001",
            "name": "Test Rule",
            "directive": "Always test",
            "category": "technical",
            "priority": "HIGH",
            "applicability": "MANDATORY",
        }
        triggers["open_rule_form"]("edit")
        assert state.form_rule_id == "TEST-001"
        assert state.form_rule_title == "Test Rule"
        assert state.form_rule_directive == "Always test"
        assert state.form_rule_category == "technical"
        assert state.form_rule_priority == "HIGH"
        assert state.show_rule_form is True


# ── Agent views: trigger() calls ─────────────────────────────────────


class TestAgentViewTriggerCalls:
    def test_agents_detail_back_uses_trigger(self):
        """Agents detail back button should use trigger('close_agent_detail')."""
        from agent.governance_ui.views.agents import detail

        source = inspect.getsource(detail)
        assert "trigger('close_agent_detail')" in source
        assert "show_agent_detail = false" not in source

    def test_agents_list_select_uses_trigger(self):
        """Agents list select should use trigger('select_agent')."""
        from agent.governance_ui.views.agents import list as agents_list

        source = inspect.getsource(agents_list)
        assert "trigger('select_agent'" in source
        assert "selected_agent = agent; show_agent_detail = true" not in source

    def test_trust_detail_back_uses_trigger(self):
        """Trust agent detail back button should use trigger('close_agent_detail')."""
        from agent.governance_ui.views.trust import agent_detail

        source = inspect.getsource(agent_detail)
        assert "trigger('close_agent_detail')" in source
        assert "close_agent_detail()" not in source

    def test_trust_panels_select_uses_trigger(self):
        """Trust panels agent select should use trigger('select_agent')."""
        from agent.governance_ui.views.trust import panels

        source = inspect.getsource(panels)
        assert "trigger('select_agent'" in source
        assert "selected_agent = agent; show_agent_detail = true" not in source


# ── Decision views: trigger() calls ──────────────────────────────────


class TestDecisionViewTriggerCalls:
    def test_decision_list_select_uses_trigger(self):
        """Decision list select should use trigger('select_decision')."""
        from agent.governance_ui.views.decisions import list as decisions_list

        source = inspect.getsource(decisions_list)
        assert "trigger('select_decision'" in source
        assert "selected_decision = decision; show_decision_detail = true" not in source

    def test_decision_detail_back_uses_trigger(self):
        """Decision detail back button should use trigger('close_decision_detail')."""
        from agent.governance_ui.views.decisions import detail

        source = inspect.getsource(detail)
        assert "trigger('close_decision_detail')" in source
        assert "close_decision_detail()" not in source


# ── Monitor view: trigger() calls ────────────────────────────────────


class TestMonitorViewTriggerCalls:
    def test_filter_uses_trigger(self):
        """Monitor filter should use trigger('filter_monitor_events')."""
        from agent.governance_ui.views import monitor_view

        source = inspect.getsource(monitor_view)
        assert "trigger('filter_monitor_events'" in source
        assert "filter_monitor_events($event)" not in source

    def test_acknowledge_uses_trigger(self):
        """Monitor acknowledge should use trigger('acknowledge_alert')."""
        from agent.governance_ui.views import monitor_view

        source = inspect.getsource(monitor_view)
        assert "trigger('acknowledge_alert'" in source
        assert "acknowledge_alert(alert.alert_id)" not in source


# ── Rules view: trigger() calls ──────────────────────────────────────


class TestRulesViewTriggerCalls:
    def test_add_rule_uses_trigger(self):
        """Rules list add button should use trigger('open_rule_form', ['create'])."""
        from agent.governance_ui.views import rules_view

        source = inspect.getsource(rules_view)
        assert "trigger('open_rule_form', ['create'])" in source
        assert "rule_form_mode = 'create'; show_rule_form = true" not in source
