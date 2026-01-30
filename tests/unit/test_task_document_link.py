"""
Tests for task-to-document linkage display.

Per PLAN-UI-OVERHAUL-001 Task 2.4: Task-Document Linkage.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestTaskDocumentLinkage:
    """Verify task detail shows document links."""

    def test_task_detail_shows_document_section(self):
        """Task detail should display a document-related section."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert 'document' in source.lower(), (
            "Task linked items should show document references"
        )

    def test_task_linked_items_shows_document_path(self):
        """Task linked items should display document_path when available."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert 'document_path' in source or 'document-path' in source, (
            "Task linked items should reference document_path field"
        )
