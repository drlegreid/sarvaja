"""
Tests for Task Detail UX improvements.

3 issues from operator review (2026-03-22):
1. "Attach Document" misleads — should be "Link Document" + add "Link Session"
2. Empty sessions should show "No sessions" with link action, not hide section
3. Task heading should use summary (short), body should use full description

TDD-first: written BEFORE implementation.
"""

import inspect
import unittest


class TestDocumentButtonWording(unittest.TestCase):
    """Issue 1: Button should say 'Link Document' not 'Attach Document'."""

    def test_no_attach_document_text(self):
        """'Attach Document' wording must not appear in task forms."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert "Attach Document" not in source, (
            "forms.py still contains 'Attach Document' — should be 'Link Document'"
        )

    def test_link_document_text_present(self):
        """'Link Document' wording must appear in task forms."""
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert "Link Document" in source

    def test_link_icon_is_reference_not_paperclip(self):
        """Icon should suggest referencing (link), not uploading (paperclip)."""
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert "mdi-link-variant" in source or "mdi-file-link" in source


class TestSessionLinkVisibility(unittest.TestCase):
    """Issue 2: Sessions section visible even when empty, with link action."""

    def test_link_session_button_exists(self):
        """A 'Link Session' button must exist in task forms."""
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert "Link Session" in source

    def test_sessions_section_always_visible(self):
        """Sessions section must render even when linked_sessions is empty."""
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        # The old pattern: v_if="selected_task.linked_sessions?.length > 0"
        # Should NOT be the only condition — section should always show
        assert "No linked sessions" in source or "no sessions" in source.lower()


class TestHeadingUsesSummary(unittest.TestCase):
    """Issue 3: Heading shows summary (short), body shows full description."""

    def test_heading_prefers_summary(self):
        """Task detail heading should use summary field first."""
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        # H2 heading should reference summary before description
        assert "selected_task.summary" in source

    def test_content_preview_shows_body(self):
        """Content section still shows full body text."""
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert "selected_task.body" in source

    def test_summary_auto_generated_in_service(self):
        """Service layer generates summary from description if not provided."""
        from governance.services.tasks import _generate_summary
        # Long description → truncated summary
        long_desc = "Fix BUG-TASK-UI-001 (MCP-created tasks don't appear in Dashboard). " \
                     "Add search/filter controls for task_type, priority, phase, status."
        summary = _generate_summary(long_desc)
        assert len(summary) <= 80
        assert summary.endswith("...")

    def test_summary_preserves_explicit(self):
        """Explicit summary is not overwritten."""
        from governance.services.tasks import _generate_summary
        # Short description → kept as-is
        short = "Fix login bug"
        summary = _generate_summary(short)
        assert summary == "Fix login bug"


class TestSummaryBackfill(unittest.TestCase):
    """Backfill null summaries for existing tasks."""

    def test_backfill_generates_from_description(self):
        """Tasks with null summary get one generated from description."""
        from scripts.remediate_task_cleanup import backfill_summaries
        tasks = [
            {"task_id": "T-1", "summary": None,
             "description": "Very long description that exceeds eighty characters and needs truncation for display purposes in the table"},
            {"task_id": "T-2", "summary": "Already has summary",
             "description": "Full description"},
            {"task_id": "T-3", "summary": None, "description": None},
        ]
        result = backfill_summaries(tasks)
        assert result["found"] == 1  # Only T-1 (T-2 has summary, T-3 has no desc)
        assert len(result["details"][0]["summary"]) <= 80

    def test_backfill_skips_existing_summary(self):
        from scripts.remediate_task_cleanup import backfill_summaries
        tasks = [{"task_id": "T-1", "summary": "Existing", "description": "Full desc"}]
        result = backfill_summaries(tasks)
        assert result["found"] == 0


if __name__ == "__main__":
    unittest.main()
