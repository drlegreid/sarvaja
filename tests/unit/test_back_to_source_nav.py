"""TDD Tests: Back-to-source navigation (UI-NAV-01-v1).

Validates that rules and decisions detail views show
"Back to {source}" button when navigated from another view.
"""
import inspect


class TestDecisionDetailBackToSource:
    """Decision detail view supports back-to-source navigation."""

    def test_has_nav_source_conditional_button(self):
        from agent.governance_ui.views.decisions.detail import build_decision_detail_view
        source = inspect.getsource(build_decision_detail_view)
        assert "nav_source_view" in source
        assert "nav_source_label" in source
        assert "decision-detail-back-source-btn" in source

    def test_has_standard_back_button(self):
        from agent.governance_ui.views.decisions.detail import build_decision_detail_view
        source = inspect.getsource(build_decision_detail_view)
        assert "decision-detail-back-btn" in source

    def test_back_source_clears_nav_context(self):
        from agent.governance_ui.views.decisions.detail import build_decision_detail_view
        source = inspect.getsource(build_decision_detail_view)
        assert "nav_source_view = null" in source
        assert "nav_source_id = null" in source
        assert "nav_source_label = null" in source


class TestRuleDetailBackToSource:
    """Rule detail view supports back-to-source navigation."""

    def test_has_nav_source_conditional_button(self):
        from agent.governance_ui.views.rules_view_detail import build_rule_detail_view
        source = inspect.getsource(build_rule_detail_view)
        assert "nav_source_view" in source
        assert "nav_source_label" in source
        assert "rule-detail-back-source-btn" in source

    def test_has_standard_back_button(self):
        from agent.governance_ui.views.rules_view_detail import build_rule_detail_view
        source = inspect.getsource(build_rule_detail_view)
        assert "rule-detail-back-btn" in source

    def test_back_source_clears_nav_context(self):
        from agent.governance_ui.views.rules_view_detail import build_rule_detail_view
        source = inspect.getsource(build_rule_detail_view)
        assert "nav_source_view = null" in source


class TestSessionNavigationSetsContext:
    """Session navigation triggers set proper nav context."""

    def test_navigate_to_rule_source_code(self):
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "nav_source_view" in source
        assert "nav_source_label" in source
        assert "navigate_to_rule_from_session" in source

    def test_navigate_to_decision_source_code(self):
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "navigate_to_decision_from_session" in source
