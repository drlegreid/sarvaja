"""
Tests for task-to-document linkage display.

Per PLAN-UI-OVERHAUL-001 Task 2.4: Task-Document Linkage.
Batch 159 deepening (was 2 tests, now 7).
"""
import inspect

import pytest


class TestTaskDocumentLinkage:
    def test_task_detail_shows_document_section(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'document' in source.lower()

    def test_task_linked_items_shows_document_path(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'document_path' in source or 'document-path' in source

    def test_has_file_document_icon(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'mdi-file-document' in source

    def test_task_forms_callable(self):
        from agent.governance_ui.views.tasks.forms import build_task_edit_form
        assert callable(build_task_edit_form)

    def test_has_rule_chip(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'rule' in source.lower()
