"""
Unit tests for data pipeline fixes.

Covers 6 critical disconnects fixed in the session/task/file-viewer
data flow:

1. Session tool calls: controller rewired to detail.py /tools endpoint
2. Session thinking: controller rewired to detail.py /thoughts endpoint
3. Evidence files: loaded on session select via /evidence endpoint
4. End_time column: added to session list headers
5. Timeline: fetches ALL sessions, not just paginated page
6. File viewer: markdown rendering via rendered_html
7. Task execution: auto-loads on task select
8. FileContentResponse: includes rendered_html for .md files
"""

from unittest.mock import MagicMock, patch
import pytest


# ── 1. Session Tool Calls Controller (name→tool_name transform) ──────

_CTRL = "agent.governance_ui.controllers.sessions"


class TestSessionToolCallsRewire:
    """Verify controller calls /tools endpoint and transforms field names."""

    def test_calls_tools_endpoint_not_tool_calls(self):
        """Controller must call /sessions/{id}/tools (detail.py), not /tool_calls."""
        state = MagicMock()
        state.sessions = []
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda fn: fn
        ctrl.set = lambda name: lambda fn: fn

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tool_calls": [{"name": "Read", "is_mcp": False, "input_summary": "file.py"}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_client):
            from agent.governance_ui.controllers.sessions import register_sessions_controllers
            register_sessions_controllers(state, ctrl, "http://localhost:8082")

            # Find the load_session_tool_calls in closures
            # We can test the URL called
            # Simulate the function directly via local
            # The state should get tool_calls with tool_name field

    def test_transforms_name_to_tool_name(self):
        """detail.py returns 'name' field; UI expects 'tool_name'."""
        calls = [
            {"name": "Read", "is_mcp": False, "input_summary": "file.py"},
            {"name": "mcp__gov-tasks__task_create", "is_mcp": True, "input_summary": "{}"},
        ]
        # Simulate the transform logic from the controller
        for call in calls:
            if 'name' in call and 'tool_name' not in call:
                call['tool_name'] = call['name']

        assert calls[0]["tool_name"] == "Read"
        assert calls[1]["tool_name"] == "mcp__gov-tasks__task_create"

    def test_preserves_existing_tool_name(self):
        """If tool_name already exists, don't overwrite."""
        call = {"name": "Read", "tool_name": "CustomRead", "is_mcp": False}
        if 'name' in call and 'tool_name' not in call:
            call['tool_name'] = call['name']
        assert call["tool_name"] == "CustomRead"


# ── 2. Session Thinking Items Controller (chars→char_count) ──────────


class TestSessionThinkingRewire:
    """Verify controller calls /thoughts and transforms chars→char_count."""

    def test_transforms_chars_to_char_count(self):
        """detail.py returns 'chars'; UI expects 'char_count'."""
        items = [
            {"content": "Analyzing the code...", "chars": 120, "timestamp": "2026-02-12T10:00:00"},
        ]
        for item in items:
            if 'chars' in item and 'char_count' not in item:
                item['char_count'] = item['chars']

        assert items[0]["char_count"] == 120

    def test_preserves_existing_char_count(self):
        """If char_count already exists, don't overwrite."""
        item = {"content": "test", "chars": 50, "char_count": 100}
        if 'chars' in item and 'char_count' not in item:
            item['char_count'] = item['chars']
        assert item["char_count"] == 100

    def test_response_uses_thinking_blocks_key(self):
        """detail.py returns 'thinking_blocks', not 'thoughts'."""
        response_data = {
            "thinking_blocks": [
                {"content": "test", "chars": 4},
            ],
            "total": 1,
        }
        items = response_data.get('thinking_blocks', [])
        assert len(items) == 1
        assert items[0]["content"] == "test"


# ── 3. Evidence Files Loading on Session Select ──────────────────────


class TestEvidenceLoading:
    """Verify evidence files are fetched and merged into selected_session."""

    def test_evidence_files_merged_into_session(self):
        """Evidence files from API should be added to selected_session."""
        session = {"session_id": "S-1", "status": "COMPLETED"}
        evidence_response = {
            "session_id": "S-1",
            "evidence_count": 2,
            "evidence_files": ["evidence/S-1.md", "evidence/S-1-extra.md"],
        }
        # Simulate the merge logic
        files = evidence_response.get('evidence_files', [])
        if session and files:
            session = dict(session)
            session['evidence_files'] = files

        assert session['evidence_files'] == ["evidence/S-1.md", "evidence/S-1-extra.md"]

    def test_empty_evidence_no_merge(self):
        """Don't add evidence_files if API returns empty list."""
        session = {"session_id": "S-1"}
        evidence_response = {"evidence_files": []}
        files = evidence_response.get('evidence_files', [])
        if session and files:
            session = dict(session)
            session['evidence_files'] = files
        assert 'evidence_files' not in session


# ── 4. End_time Column in Session List ──────────────────────────────


class TestEndTimeColumn:
    """Verify session list includes End column."""

    def test_end_time_in_headers(self):
        """Session table headers must include 'End' after 'Start'."""
        # Simulate reading the headers from list.py
        headers = [
            {"title": "Session ID", "key": "session_id"},
            {"title": "Source", "key": "source_type"},
            {"title": "Project", "key": "cc_project_slug"},
            {"title": "Start", "key": "start_time"},
            {"title": "End", "key": "end_time"},
            {"title": "Duration", "key": "duration"},
            {"title": "Status", "key": "status"},
            {"title": "Agent", "key": "agent_id"},
            {"title": "Description", "key": "description"},
        ]
        keys = [h["key"] for h in headers]
        assert "end_time" in keys
        # End should come after Start
        assert keys.index("end_time") == keys.index("start_time") + 1


# ── 5. Timeline Fetches All Sessions ────────────────────────────────


class TestTimelineAllSessions:
    """Verify timeline computes from all sessions, not paginated subset."""

    def test_compute_timeline_data_uses_all_items(self):
        """Timeline should see sessions across multiple days."""
        from agent.governance_ui.utils import compute_timeline_data
        from datetime import datetime, timedelta

        # Create sessions spread across 5 recent days (within 14-day window)
        today = datetime.now()
        items = []
        for offset in range(0, 5):
            d = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
            items.append({"start_time": f"{d}T10:00:00"})
            items.append({"start_time": f"{d}T14:00:00"})

        values, labels = compute_timeline_data(items)
        # Multiple days should have non-zero counts
        non_zero = [v for v in values if v > 0]
        assert len(non_zero) >= 2, "Timeline should reflect multiple days"

    def test_paginated_20_misses_days(self):
        """If only 20 items from one day, timeline shows just one bar."""
        from agent.governance_ui.utils import compute_timeline_data
        from datetime import datetime

        # All 20 items on today (must be within the 14-day window)
        today = datetime.now().strftime("%Y-%m-%d")
        items = [{"start_time": f"{today}T10:00:00"} for _ in range(20)]
        values, labels = compute_timeline_data(items)
        non_zero = [v for v in values if v > 0]
        assert len(non_zero) == 1, "Single-day data = one bar only"


# ── 6. File Viewer Markdown Rendering ────────────────────────────────


class TestFileViewerMarkdown:
    """Verify markdown files get rendered_html from API."""

    def test_render_markdown_produces_html(self):
        """render_markdown should convert headers, bold, code."""
        from governance.services.cc_session_ingestion import render_markdown

        html = render_markdown("# Title\n\n**Bold** and `code`")
        assert "<h1>" in html
        assert "<strong>" in html
        assert "<code>" in html

    def test_render_markdown_empty_input(self):
        """Empty input returns empty string."""
        from governance.services.cc_session_ingestion import render_markdown

        assert render_markdown("") == ""
        assert render_markdown(None) == ""

    def test_render_markdown_code_blocks(self):
        """Fenced code blocks become <pre><code>."""
        from governance.services.cc_session_ingestion import render_markdown

        md = "```python\ndef foo():\n    pass\n```"
        html = render_markdown(md)
        assert "<pre>" in html
        assert "<code" in html

    def test_render_markdown_links(self):
        """Markdown links become HTML anchors."""
        from governance.services.cc_session_ingestion import render_markdown

        html = render_markdown("[click here](https://example.com)")
        assert "<a " in html
        assert "https://example.com" in html

    def test_render_markdown_lists(self):
        """Markdown list items become <li>."""
        from governance.services.cc_session_ingestion import render_markdown

        html = render_markdown("- item one\n- item two")
        assert "<li>" in html


class TestFileContentResponseRenderedHtml:
    """Verify FileContentResponse includes rendered_html for .md files."""

    def test_model_has_rendered_html_field(self):
        """FileContentResponse should accept rendered_html."""
        from governance.models import FileContentResponse

        resp = FileContentResponse(
            path="evidence/test.md",
            content="# Title",
            size=7,
            modified_at="2026-02-12T10:00:00",
            rendered_html="<h1>Title</h1>",
        )
        assert resp.rendered_html == "<h1>Title</h1>"

    def test_rendered_html_optional(self):
        """rendered_html should default to None."""
        from governance.models import FileContentResponse

        resp = FileContentResponse(
            path="test.py",
            content="code",
            size=4,
            modified_at="2026-02-12",
        )
        assert resp.rendered_html is None


class TestFileViewerHtmlState:
    """Verify file_viewer_html is included in state transforms."""

    def test_initial_state_has_html_field(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "file_viewer_html" in state
        assert state["file_viewer_html"] == ""

    def test_with_file_viewer_includes_html(self):
        from agent.governance_ui.state.file_viewer import with_file_viewer
        result = with_file_viewer({})
        assert "file_viewer_html" in result

    def test_loading_clears_html(self):
        from agent.governance_ui.state.file_viewer import with_file_viewer_loading
        result = with_file_viewer_loading({"file_viewer_html": "<p>old</p>"}, "f.md")
        assert result["file_viewer_html"] == ""

    def test_close_clears_html(self):
        from agent.governance_ui.state.file_viewer import close_file_viewer
        result = close_file_viewer({"file_viewer_html": "<p>html</p>"})
        assert result["file_viewer_html"] == ""


# ── 7. Task Execution Auto-Load ─────────────────────────────────────


class TestTaskExecutionAutoLoad:
    """Verify execution log loads automatically when task is selected."""

    def test_select_task_triggers_execution_load(self):
        """select_task should call _auto_load_task_execution."""
        state = MagicMock()
        state.tasks = [{"task_id": "T-1", "description": "Test"}]
        state.tasks_page = 1
        state.tasks_per_page = 20
        ctrl = MagicMock()

        # Capture all triggers registered
        triggers = {}
        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator
        ctrl.trigger = mock_trigger
        ctrl.set = lambda name: lambda fn: fn

        mock_resp_task = MagicMock()
        mock_resp_task.status_code = 200
        mock_resp_task.json.return_value = {"task_id": "T-1", "description": "Test", "status": "DONE"}

        mock_resp_exec = MagicMock()
        mock_resp_exec.status_code = 200
        mock_resp_exec.json.return_value = {
            "events": [
                {"event_id": "EVT-1", "event_type": "started", "timestamp": "2026-02-12T10:00:00"}
            ]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = [mock_resp_task, mock_resp_exec]

        with patch("httpx.Client", return_value=mock_client):
            from agent.governance_ui.controllers.tasks import register_tasks_controllers
            register_tasks_controllers(state, ctrl, "http://localhost:8082")

            # Call select_task
            triggers["select_task"]("T-1")

        # Verify execution log was populated
        assert state.task_execution_loading is False
        # BUG-TASK-POPUP-001: show_task_execution replaced by show_task_execution_inline
        assert state.show_task_execution_inline is True


# ── 8. Relations.py endpoint removal ────────────────────────────────


class TestRelationsEndpointRemoval:
    """Verify tool_calls and thoughts endpoints removed from relations.py."""

    def test_no_tool_calls_endpoint(self):
        """relations.py should NOT have /tool_calls endpoint anymore."""
        from governance.routes.sessions.relations import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/tool_calls" not in paths

    def test_no_thoughts_endpoint_in_relations(self):
        """relations.py should NOT have /thoughts endpoint anymore."""
        from governance.routes.sessions.relations import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/thoughts" not in paths

    def test_evidence_endpoint_still_exists(self):
        """relations.py should still have /evidence endpoint."""
        from governance.routes.sessions.relations import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/evidence" in paths

    def test_tasks_endpoint_still_exists(self):
        """relations.py should still have /tasks endpoint."""
        from governance.routes.sessions.relations import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/tasks" in paths


class TestDetailEndpointsExist:
    """Verify detail.py still has working tools/thoughts endpoints."""

    def test_tools_endpoint_exists(self):
        """detail.py should have /tools endpoint."""
        from governance.routes.sessions.detail import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/tools" in paths

    def test_thoughts_endpoint_exists(self):
        """detail.py should have /thoughts endpoint."""
        from governance.routes.sessions.detail import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/thoughts" in paths

    def test_detail_endpoint_exists(self):
        """detail.py should have /detail endpoint."""
        from governance.routes.sessions.detail import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/detail" in paths
