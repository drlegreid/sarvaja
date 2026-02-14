"""
Tests for shared dialog components.

Per GAP-UI-038: Document reference viewer.
Per GAP-UI-005: Global error/loading states.
Batch 164: New coverage for views/dialogs.py (0->12 tests).
"""
import inspect

import pytest


class TestDialogsComponents:
    def test_build_file_viewer_dialog_callable(self):
        from agent.governance_ui.views.dialogs import build_file_viewer_dialog
        assert callable(build_file_viewer_dialog)

    def test_build_confirm_dialog_callable(self):
        from agent.governance_ui.views.dialogs import build_confirm_dialog
        assert callable(build_confirm_dialog)

    def test_build_all_dialogs_callable(self):
        from agent.governance_ui.views.dialogs import build_all_dialogs
        assert callable(build_all_dialogs)


class TestFileViewerDialogContent:
    def test_has_dialog_testid(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "file-viewer-dialog" in source

    def test_has_close_btn(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "file-viewer-close-btn" in source

    def test_has_path_display(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "file-viewer-path" in source

    def test_has_html_content(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "file-viewer-html" in source

    def test_has_raw_content(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "file-viewer-content" in source


class TestConfirmDialogContent:
    def test_has_confirm_dialog_testid(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "confirm-dialog" in source

    def test_has_cancel_btn(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "confirm-cancel-btn" in source

    def test_has_ok_btn(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "confirm-ok-btn" in source

    def test_imports_shared_components(self):
        from agent.governance_ui.views import dialogs
        source = inspect.getsource(dialogs)
        assert "build_error_dialog" in source
        assert "build_loading_overlay" in source
