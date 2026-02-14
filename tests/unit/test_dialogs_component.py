"""
Tests for dialog components.

Per RULE-019: UI/UX Standards - consistent dialog patterns.
Batch 165: New coverage for components/dialogs.py (0->8 tests).
"""
import inspect

import pytest


class TestDialogComponents:
    def test_build_confirm_dialog_callable(self):
        from agent.governance_ui.components.dialogs import build_confirm_dialog
        assert callable(build_confirm_dialog)

    def test_build_error_dialog_callable(self):
        from agent.governance_ui.components.dialogs import build_error_dialog
        assert callable(build_error_dialog)

    def test_build_loading_overlay_callable(self):
        from agent.governance_ui.components.dialogs import build_loading_overlay
        assert callable(build_loading_overlay)


class TestConfirmDialogSignature:
    def test_has_required_params(self):
        from agent.governance_ui.components.dialogs import build_confirm_dialog
        sig = inspect.signature(build_confirm_dialog)
        params = list(sig.parameters.keys())
        assert "v_model" in params
        assert "title" in params
        assert "message" in params
        assert "confirm_action" in params

    def test_has_optional_cancel(self):
        from agent.governance_ui.components.dialogs import build_confirm_dialog
        sig = inspect.signature(build_confirm_dialog)
        assert sig.parameters["cancel_action"].default is None

    def test_default_confirm_color(self):
        from agent.governance_ui.components.dialogs import build_confirm_dialog
        sig = inspect.signature(build_confirm_dialog)
        assert sig.parameters["confirm_color"].default == "error"


class TestErrorDialogContent:
    def test_has_error_icon(self):
        from agent.governance_ui.components import dialogs
        source = inspect.getsource(dialogs)
        assert "mdi-alert-circle" in source

    def test_has_has_error_state(self):
        from agent.governance_ui.components import dialogs
        source = inspect.getsource(dialogs)
        assert "has_error" in source
