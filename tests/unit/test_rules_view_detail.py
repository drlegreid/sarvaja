"""
Tests for rule detail view component.

Per DOC-SIZE-01-v1: Extracted from rules_view.py.
Batch 167: New coverage for views/rules_view_detail.py (0->10 tests).
"""
import inspect

import pytest


class TestRulesViewDetailComponents:
    def test_build_rule_detail_view_callable(self):
        from agent.governance_ui.views.rules_view_detail import build_rule_detail_view
        assert callable(build_rule_detail_view)


class TestRulesViewDetailContent:
    def test_has_detail_testid(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "rule-detail" in source

    def test_has_back_btn(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "rule-detail-back-btn" in source

    def test_has_id_display(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "rule-detail-id" in source

    def test_has_edit_btn(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "rule-detail-edit-btn" in source

    def test_has_delete_btn(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "rule-detail-delete-btn" in source

    def test_has_pencil_icon(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "mdi-pencil" in source

    def test_has_delete_icon(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "mdi-delete" in source

    def test_has_back_arrow(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "mdi-arrow-left" in source

    def test_has_edit_rule_trigger(self):
        from agent.governance_ui.views import rules_view_detail
        source = inspect.getsource(rules_view_detail)
        assert "edit_rule" in source
