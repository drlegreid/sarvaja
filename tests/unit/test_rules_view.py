"""
Tests for rules view component.

Per GAP-MCP-008: Semantic rule ID display support.
Batch 162: New coverage for views/rules_view.py (0→10 tests).
"""
import inspect

import pytest


class TestRulesViewComponents:
    def test_build_rules_view_callable(self):
        from agent.governance_ui.views.rules_view import build_rules_view
        assert callable(build_rules_view)

    def test_build_rules_list_view_callable(self):
        from agent.governance_ui.views.rules_view import build_rules_list_view
        assert callable(build_rules_list_view)

    def test_build_rule_form_view_callable(self):
        from agent.governance_ui.views.rules_view import build_rule_form_view
        assert callable(build_rule_form_view)


class TestRulesViewContent:
    def test_has_rules_list_testid(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "rules-list" in source

    def test_has_add_rule_button(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "rules-add-btn" in source

    def test_has_loading_indicator(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "rules-loading" in source

    def test_has_rule_form_mode(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "rule_form_mode" in source

    def test_references_detail_view(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "build_rule_detail_view" in source

    def test_has_search_field(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "mdi-magnify" in source or "search" in source.lower()

    def test_has_data_table_or_list(self):
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert "VDataTable" in source or "VList" in source
