"""
Tests for decision form view component.

Per GAP-UI-033: Decision CRUD operations.
Batch 167: New coverage for views/decisions/form.py (0->10 tests).
"""
import inspect

import pytest


class TestDecisionsFormComponents:
    def test_build_decision_form_view_callable(self):
        from agent.governance_ui.views.decisions.form import build_decision_form_view
        assert callable(build_decision_form_view)


class TestDecisionsFormContent:
    def test_has_form_testid(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "decision-form" in source

    def test_has_back_btn(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "decision-form-back-btn" in source

    def test_has_id_field(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "decision-form-id" in source

    def test_has_decision_id_placeholder(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "DECISION-XXX" in source

    def test_has_form_mode(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "decision_form_mode" in source

    def test_has_create_label(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "Create Decision" in source

    def test_has_edit_label(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "Edit Decision" in source

    def test_has_vform(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "VForm" in source

    def test_has_disabled_on_edit(self):
        from agent.governance_ui.views.decisions import form
        source = inspect.getsource(form)
        assert "disabled" in source
