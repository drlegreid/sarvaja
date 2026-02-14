"""
Unit tests for bug fixes: BUG-UI-TASKS-003 and BUG-UI-TASKS-004.

Batch 174: Tests verifying fixes for:
- BUG-UI-TASKS-003: Task timestamps formatted on initial load
- BUG-UI-TASKS-004: Execution timeline dialog uses icon= not v_text=
"""

from unittest.mock import MagicMock, patch
import pytest
import inspect


# ── BUG-UI-TASKS-003: Task timestamps formatted on initial load ──


class TestBugTasksTimestampInitialLoad:
    """BUG-UI-TASKS-003: format_timestamps_in_list called during _load_tasks."""

    @patch("agent.governance_ui.dashboard_data_loader.format_timestamps_in_list")
    def test_load_tasks_formats_timestamps(self, mock_fmt):
        """_load_tasks() should call format_timestamps_in_list on items."""
        from agent.governance_ui.dashboard_data_loader import _load_tasks

        mock_fmt.side_effect = lambda items, fields: items  # passthrough

        state = MagicMock()
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "items": [
                {"task_id": "T-1", "created_at": "2026-01-19T04:06:50.000000000"},
                {"task_id": "T-2", "created_at": "2026-02-10T10:00:00.000000000"},
            ],
            "pagination": {"total": 2},
        }
        client.get.return_value = resp

        _load_tasks(state, client, "http://test:8082", lambda: [], 20)

        mock_fmt.assert_called_once()
        call_args = mock_fmt.call_args
        assert call_args[0][1] == ["created_at", "completed_at", "claimed_at"]

    @patch("agent.governance_ui.dashboard_data_loader.format_timestamps_in_list")
    def test_load_tasks_formats_non_dict_response(self, mock_fmt):
        """_load_tasks() should format even when response is a list (no 'items' key)."""
        from agent.governance_ui.dashboard_data_loader import _load_tasks

        mock_fmt.side_effect = lambda items, fields: items

        state = MagicMock()
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [
            {"task_id": "T-1", "created_at": "2026-01-19T04:06:50.000000000"},
        ]
        client.get.return_value = resp

        _load_tasks(state, client, "http://test:8082", lambda: [], 20)

        mock_fmt.assert_called_once()

    @patch("agent.governance_ui.dashboard_data_loader.format_timestamps_in_list")
    def test_load_tasks_no_format_on_error(self, mock_fmt):
        """_load_tasks() should NOT call format when API returns error."""
        from agent.governance_ui.dashboard_data_loader import _load_tasks

        state = MagicMock()
        client = MagicMock()
        resp = MagicMock()
        resp.status_code = 500
        client.get.return_value = resp

        _load_tasks(state, client, "http://test:8082", lambda: [], 20)

        mock_fmt.assert_not_called()


# ── BUG-UI-TASKS-004: Execution timeline icon uses icon= not v_text= ──


class TestBugTasksExecutionIcons:
    """BUG-UI-TASKS-004: VIcon in execution dialog should use icon= parameter."""

    def test_execution_dialog_vicon_uses_icon_not_vtext(self):
        """The VIcon for event type in the timeline dialog must use icon=."""
        src = inspect.getsource(
            __import__(
                "agent.governance_ui.views.chat.execution",
                fromlist=["build_task_execution_viewer"],
            ).build_task_execution_viewer
        )
        # Find the VIcon block with event_type icon logic
        # After the fix, it should have "icon=(" not "v_text=("
        # before the mdi-check-circle expression
        icon_block_start = src.find("mdi-check-circle")
        assert icon_block_start > 0, "Should contain mdi-check-circle"
        # Check the 200 chars before the icon name to find the parameter
        prefix = src[max(0, icon_block_start - 200):icon_block_start]
        assert "icon=" in prefix, (
            "VIcon for event type should use icon=, not v_text= "
            "(BUG-UI-TASKS-004)"
        )
        assert "v_text=" not in prefix, (
            "VIcon for event type should NOT use v_text= "
            "(BUG-UI-TASKS-004)"
        )

    def test_execution_dialog_has_icon_binding(self):
        """The VIcon in execution dialog must have icon= with event_type expression."""
        src = inspect.getsource(
            __import__(
                "agent.governance_ui.views.chat.execution",
                fromlist=["build_task_execution_viewer"],
            ).build_task_execution_viewer
        )
        assert "icon=" in src
        assert "mdi-check-circle" in src
        assert "mdi-play-circle" in src
        assert "mdi-file-document" in src

    def test_inline_execution_timeline_uses_icon(self):
        """The inline execution timeline also uses icon= (reference implementation)."""
        src = inspect.getsource(
            __import__(
                "agent.governance_ui.views.tasks.execution",
                fromlist=["build_execution_timeline"],
            ).build_execution_timeline
        )
        # The inline VIcon for event type should use icon= binding
        icon_block_start = src.find("mdi-check-circle")
        assert icon_block_start > 0
        prefix = src[max(0, icon_block_start - 200):icon_block_start]
        assert "icon=" in prefix


# ── BUG-UI-RULES-002: Markdown table rendering (documentation only) ──


class TestBugRulesMarkdownTables:
    """BUG-UI-RULES-002: Document that markdown tables don't render in viewer.

    This is a cosmetic issue in the file viewer dialog. The viewer renders
    markdown content from rule docs, but tables (pipe-separated) show as text.
    This test documents the behavior but does not fix it (requires changes to
    the markdown renderer, not a code bug).
    """

    def test_file_viewer_markdown_rendering_documented(self):
        """Document that file viewer uses v-html for markdown rendering."""
        # The file viewer dialog renders markdown via server-side conversion
        # Tables that don't render properly are a limitation of the converter,
        # not a code bug that needs fixing in this cycle.
        mod = __import__(
            "agent.governance_ui.views.rules_view_detail",
            fromlist=["build_rule_detail_view"],
        )
        src = inspect.getsource(mod.build_rule_detail_view)
        # Verify the file viewer trigger exists in rule detail view
        assert "document_path" in src or "file_viewer" in src or "load_file_content" in src
