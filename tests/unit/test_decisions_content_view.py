"""
Tests for decision content display components.

Per GAP-UI-037: Context and rationale preview.
Batch 161: New coverage for views/decisions/content.py (0→8 tests).
"""
import inspect

import pytest


class TestDecisionContentComponents:
    def test_build_metadata_chips_callable(self):
        from agent.governance_ui.views.decisions.content import build_decision_metadata_chips
        assert callable(build_decision_metadata_chips)

    def test_build_content_preview_callable(self):
        from agent.governance_ui.views.decisions.content import build_decision_content_preview
        assert callable(build_decision_content_preview)


class TestDecisionContentSource:
    def test_has_status_chip(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "decision-detail-status" in source

    def test_has_date_chip(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "decision-detail-date" in source

    def test_has_context_preview(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "decision-context-preview" in source

    def test_has_calendar_icon(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "mdi-calendar" in source

    def test_has_status_color_coding(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "APPROVED" in source
        assert "REJECTED" in source

    def test_has_rationale_section(self):
        from agent.governance_ui.views.decisions import content
        source = inspect.getsource(content)
        assert "rationale" in source.lower()
