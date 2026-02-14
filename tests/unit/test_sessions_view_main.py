"""
Tests for sessions view container.

Batch 168: New coverage for agent/governance_ui/views/sessions_view.py (0->8 tests).
"""
import inspect

import pytest


class TestSessionsViewComponents:
    def test_build_sessions_view_callable(self):
        from agent.governance_ui.views.sessions_view import build_sessions_view
        assert callable(build_sessions_view)


class TestSessionsViewContent:
    def test_imports_list_view(self):
        from agent.governance_ui.views import sessions_view
        source = inspect.getsource(sessions_view)
        assert "build_sessions_list_view" in source

    def test_imports_detail_view(self):
        from agent.governance_ui.views import sessions_view
        source = inspect.getsource(sessions_view)
        assert "build_session_detail_view" in source

    def test_imports_form_view(self):
        from agent.governance_ui.views import sessions_view
        source = inspect.getsource(sessions_view)
        assert "build_session_form_view" in source

    def test_imports_evidence_dialog(self):
        from agent.governance_ui.views import sessions_view
        source = inspect.getsource(sessions_view)
        assert "build_evidence_attach_dialog" in source

    def test_has_module_docstring(self):
        from agent.governance_ui.views import sessions_view
        assert sessions_view.__doc__ is not None

    def test_function_signature(self):
        from agent.governance_ui.views.sessions_view import build_sessions_view
        sig = inspect.signature(build_sessions_view)
        assert len(sig.parameters) == 0
