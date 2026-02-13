"""
Tests for session evidence filters and attach dialog.

Per B.4: Session evidence view should have a working search filter.
Per P11.5: Session evidence attachment UI.

Batch 157c deepening (was 2 tests, now 12).
"""
import inspect

import pytest


class TestEvidenceFilter:
    """Tests for evidence file list filtering."""

    def test_evidence_view_has_search_filter(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "evidence_search" in source or "evidence_filter" in source

    def test_evidence_list_uses_filter(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "filter" in source.lower() or "includes" in source

    def test_has_clearable_search(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "clearable" in source

    def test_has_magnify_icon(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "mdi-magnify" in source

    def test_has_testid_for_search_input(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "evidence-search-input" in source

    def test_evidence_file_click_triggers_load(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "load_file_content" in source

    def test_no_evidence_message(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "No evidence files" in source


class TestEvidenceAttachDialog:
    """Tests for evidence attachment dialog (P11.5)."""

    def test_attach_dialog_exists(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_attach_dialog
        assert callable(build_evidence_attach_dialog)

    def test_dialog_has_path_input(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_attach_dialog
        source = inspect.getsource(build_evidence_attach_dialog)
        assert "evidence_attach_path" in source

    def test_dialog_has_confirm_button(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_attach_dialog
        source = inspect.getsource(build_evidence_attach_dialog)
        assert "attach-evidence-confirm-btn" in source

    def test_dialog_triggers_attach_evidence(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_attach_dialog
        source = inspect.getsource(build_evidence_attach_dialog)
        assert "attach_evidence" in source

    def test_dialog_has_cancel(self):
        from agent.governance_ui.views.sessions.evidence import build_evidence_attach_dialog
        source = inspect.getsource(build_evidence_attach_dialog)
        assert "Cancel" in source
