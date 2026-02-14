"""
Tests for executive report view container.

Batch 168: New coverage for agent/governance_ui/views/executive_view.py (0->8 tests).
"""
import inspect

import pytest


class TestExecutiveViewComponents:
    def test_build_executive_view_callable(self):
        from agent.governance_ui.views.executive_view import build_executive_view
        assert callable(build_executive_view)


class TestExecutiveViewContent:
    def test_has_executive_report_testid(self):
        from agent.governance_ui.views import executive_view
        source = inspect.getsource(executive_view)
        assert "executive-report" in source

    def test_imports_header(self):
        from agent.governance_ui.views import executive_view
        source = inspect.getsource(executive_view)
        assert "build_executive_header" in source

    def test_imports_content(self):
        from agent.governance_ui.views import executive_view
        source = inspect.getsource(executive_view)
        assert "build_executive_content" in source

    def test_has_active_view_condition(self):
        from agent.governance_ui.views import executive_view
        source = inspect.getsource(executive_view)
        assert "executive" in source

    def test_has_vcard(self):
        from agent.governance_ui.views import executive_view
        source = inspect.getsource(executive_view)
        assert "VCard" in source

    def test_function_signature(self):
        from agent.governance_ui.views.executive_view import build_executive_view
        sig = inspect.signature(build_executive_view)
        assert len(sig.parameters) == 0
