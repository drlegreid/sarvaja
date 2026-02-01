"""
Tests for task create form/dialog.

Per B.1: Fix task create dialog.
Verifies:
- build_task_create_dialog function exists
- Dialog is bound to show_task_form state
- Submit triggers create_task controller
- Form has required fields (task_id, description, phase, agent)

Created: 2026-02-01
"""
import pytest
import inspect


class TestTaskCreateDialog:
    """Tests for task create dialog component."""

    def test_build_task_create_dialog_exists(self):
        """build_task_create_dialog should exist in forms module."""
        from agent.governance_ui.views.tasks.forms import build_task_create_dialog
        assert callable(build_task_create_dialog)

    def test_build_task_create_dialog_exported(self):
        """build_task_create_dialog should be importable from tasks package."""
        from agent.governance_ui.views.tasks import build_task_create_dialog
        assert callable(build_task_create_dialog)

    def test_form_source_references_show_task_form(self):
        """Dialog should be bound to show_task_form state variable."""
        from agent.governance_ui.views.tasks.forms import build_task_create_dialog
        source = inspect.getsource(build_task_create_dialog)
        assert "show_task_form" in source

    def test_form_source_references_create_task(self):
        """Submit button should trigger create_task."""
        from agent.governance_ui.views.tasks.forms import build_task_create_dialog
        source = inspect.getsource(build_task_create_dialog)
        assert "create_task" in source

    def test_form_has_required_fields(self):
        """Form should reference all required state fields."""
        from agent.governance_ui.views.tasks.forms import build_task_create_dialog
        source = inspect.getsource(build_task_create_dialog)
        assert "form_task_id" in source
        assert "form_task_description" in source
        assert "form_task_phase" in source
