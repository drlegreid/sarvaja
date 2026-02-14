"""
Tests for executive report sections component.

Batch 168: New coverage for agent/governance_ui/views/executive/sections.py (0->8 tests).
"""
import inspect

import pytest


class TestExecutiveSectionsComponents:
    def test_build_report_sections_callable(self):
        from agent.governance_ui.views.executive.sections import build_report_sections
        assert callable(build_report_sections)


class TestExecutiveSectionsContent:
    def test_has_sections_testid(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "executive-sections" in source

    def test_has_expansion_panels(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "VExpansionPanels" in source

    def test_has_dynamic_icons(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "mdi-clipboard-text" in source
        assert "mdi-check-decagram" in source

    def test_has_status_chip(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "section.status" in source

    def test_has_metrics_chips(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "section.metrics" in source

    def test_has_section_content(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "section.content" in source

    def test_has_pre_wrap_style(self):
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert "pre-wrap" in source
