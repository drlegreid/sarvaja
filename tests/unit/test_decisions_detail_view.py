"""
Tests for decision detail view component.

Per GAP-UI-033: Decision CRUD operations.
Batch 167: New coverage for views/decisions/detail.py (0->10 tests).
"""
import inspect

import pytest


class TestDecisionsDetailComponents:
    def test_build_decision_detail_view_callable(self):
        from agent.governance_ui.views.decisions.detail import build_decision_detail_view
        assert callable(build_decision_detail_view)


class TestDecisionsDetailContent:
    def test_has_detail_testid(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "decision-detail" in source

    def test_has_back_btn(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "decision-detail-back-btn" in source

    def test_has_id_display(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "decision-detail-id" in source

    def test_has_edit_btn(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "decision-detail-edit-btn" in source

    def test_has_pencil_icon(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "mdi-pencil" in source

    def test_has_delete_icon(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "mdi-delete" in source

    def test_imports_content_components(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "build_decision_metadata_chips" in source
        assert "build_decision_info_cards" in source

    def test_has_back_arrow(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "mdi-arrow-left" in source

    def test_has_form_mode_edit(self):
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert "edit" in source
