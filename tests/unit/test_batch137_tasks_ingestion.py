"""Batch 137: Unit tests for tasks controller + CC session ingestion."""
import json
import re
import sys
import types
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ===== Module 1: controllers/tasks.py ========================================

def _make_state(**kw):
    s = MagicMock()
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    c = MagicMock()
    _triggers = {}

    def trigger(name):
        def dec(fn):
            _triggers[name] = fn
            return fn
        return dec

    def set_(name):
        def dec(fn):
            _triggers[name] = fn
            return fn
        return dec

    c.trigger = trigger
    c.set = set_
    c._triggers = _triggers
    return c


def _mock_httpx_client(responses):
    """Create httpx.Client mock with sequential responses."""
    mc = MagicMock()
    mc.__enter__ = MagicMock(return_value=mc)
    mc.__exit__ = MagicMock(return_value=False)
    for method, resp_data in responses.items():
        r = MagicMock(status_code=resp_data["status"])
        r.json.return_value = resp_data.get("data", {})
        setattr(mc, method, MagicMock(return_value=r))
    return mc


class TestSelectTask:
    def setup_method(self):
        self.state = _make_state(tasks=[{"task_id": "T1", "title": "A"}], show_task_detail=False)
        self.ctrl = _make_ctrl()

    @patch("httpx.Client")
    def test_api_success(self, hc):
        mc = _mock_httpx_client({"get": {"status": 200, "data": {"task_id": "T1"}}})
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(self.state, self.ctrl, "http://test:8082")
        self.ctrl._triggers["select_task"]("T1")
        assert self.state.selected_task == {"task_id": "T1"}
        assert self.state.show_task_detail is True

    @patch("httpx.Client")
    def test_api_fail_fallback(self, hc):
        hc.side_effect = ConnectionError("down")
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(self.state, self.ctrl, "http://test:8082")
        self.ctrl._triggers["select_task"]("T1")
        assert self.state.show_task_detail is True


class TestDeleteTask:
    @patch("httpx.Client")
    def test_success(self, hc):
        state = _make_state(
            selected_task={"id": "T1"}, is_loading=False,
            tasks_per_page=20, tasks_page=1, show_task_detail=True,
        )
        ctrl = _make_ctrl()
        del_resp = MagicMock(status_code=204)
        list_resp = MagicMock(status_code=200)
        list_resp.json.return_value = {"items": [], "pagination": {}}
        mc = MagicMock()
        mc.__enter__ = MagicMock(return_value=mc)
        mc.__exit__ = MagicMock(return_value=False)
        mc.delete.return_value = del_resp
        mc.get.return_value = list_resp
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["delete_task"]()
        assert state.show_task_detail is False
        assert state.selected_task is None

    def test_no_selection(self):
        state = _make_state(selected_task=None)
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["delete_task"]()  # should not raise


class TestClaimComplete:
    @patch("httpx.Client")
    def test_claim_success(self, hc):
        state = _make_state(selected_task={"id": "T1"})
        ctrl = _make_ctrl()
        mc = _mock_httpx_client({"post": {"status": 200, "data": {"id": "T1", "status": "IN_PROGRESS"}}})
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["claim_selected_task"]()
        assert state.status_message == "Task T1 claimed"

    @patch("httpx.Client")
    def test_complete_error(self, hc):
        state = _make_state(selected_task={"task_id": "T2"}, has_error=False)
        ctrl = _make_ctrl()
        mc = _mock_httpx_client({"post": {"status": 500}})
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["complete_selected_task"]()
        assert state.has_error is True


class TestEditTask:
    def test_enter_edit_mode(self):
        state = _make_state(selected_task={"description": "Do X", "phase": "P11", "status": "TODO", "agent_id": "a1"})
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["edit_task"]()
        assert state.edit_task_mode is True
        assert state.edit_task_description == "Do X"
        assert state.edit_task_phase == "P11"

    def test_cancel_edit(self):
        state = _make_state(edit_task_mode=True)
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["cancel_task_edit"]()
        assert state.edit_task_mode is False


class TestCreateTask:
    @patch("httpx.Client")
    def test_success(self, hc):
        state = _make_state(
            form_task_id="T-NEW", form_task_description="New task",
            form_task_phase="P10", form_task_agent="code-agent",
            is_loading=False, tasks_per_page=20, tasks_page=1,
            form_task_body="", form_task_priority=None,
            form_task_type=None, form_task_layer=None,
            form_task_concern=None, form_task_method=None,
        )
        ctrl = _make_ctrl()
        create_resp = MagicMock(status_code=201)
        list_resp = MagicMock(status_code=200)
        list_resp.json.return_value = {"items": [{"id": "T-NEW"}], "pagination": {}}
        mc = MagicMock()
        mc.__enter__ = MagicMock(return_value=mc)
        mc.__exit__ = MagicMock(return_value=False)
        mc.post.return_value = create_resp
        mc.get.return_value = list_resp
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["create_task"]()
        assert state.status_message == "Task created successfully"
        assert state.show_task_form is False


class TestPagination:
    def test_prev_page_at_1(self):
        state = _make_state(tasks_page=1)
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["tasks_prev_page"]()
        assert state.tasks_page == 1  # no change

    @patch("httpx.Client")
    def test_next_page(self, hc):
        state = _make_state(
            tasks_page=1, tasks_per_page=20, tasks_pagination={"has_more": True},
            is_loading=False, tasks_status_filter=None, tasks_phase_filter=None,
        )
        ctrl = _make_ctrl()
        mc = _mock_httpx_client({"get": {"status": 200, "data": {"items": [], "pagination": {"has_more": False}}}})
        hc.return_value = mc
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["tasks_next_page"]()
        assert state.tasks_page == 2


# ===== Module 2: cc_session_ingestion.py ====================================

class TestIngestSession:
    @patch("governance.services.cc_session_ingestion.session_service")
    @patch("governance.services.cc_session_ingestion._scan_jsonl_metadata")
    def test_no_metadata(self, scan, svc):
        scan.return_value = None
        from governance.services.cc_session_ingestion import ingest_session
        assert ingest_session(Path("/tmp/test.jsonl")) is None

    @patch("governance.services.cc_session_ingestion.session_service")
    @patch("governance.services.cc_session_ingestion._scan_jsonl_metadata")
    @patch("governance.services.cc_session_ingestion._derive_project_slug")
    @patch("governance.services.cc_session_ingestion._build_session_id")
    def test_existing_skips(self, build, slug, scan, svc):
        scan.return_value = {"slug": "test", "user_count": 1, "assistant_count": 1, "tool_use_count": 5}
        slug.return_value = "test-proj"
        build.return_value = "SESSION-2026-02-12-CC-TEST"
        svc.get_session.return_value = {"session_id": "SESSION-2026-02-12-CC-TEST"}
        from governance.services.cc_session_ingestion import ingest_session
        assert ingest_session(Path("/tmp/test.jsonl")) is None

    @patch("governance.services.cc_session_ingestion.session_service")
    @patch("governance.services.cc_session_ingestion._scan_jsonl_metadata")
    @patch("governance.services.cc_session_ingestion._derive_project_slug")
    @patch("governance.services.cc_session_ingestion._build_session_id")
    def test_dry_run(self, build, slug, scan, svc):
        scan.return_value = {
            "slug": "test", "user_count": 1, "assistant_count": 2,
            "tool_use_count": 10, "session_uuid": "abc", "file_path": "/tmp/x.jsonl",
            "thinking_chars": 500, "compaction_count": 1,
        }
        slug.return_value = "test-proj"
        build.return_value = "SESSION-2026-02-12-CC-TEST"
        svc.get_session.return_value = None
        from governance.services.cc_session_ingestion import ingest_session
        r = ingest_session(Path("/tmp/test.jsonl"), dry_run=True)
        assert r["dry_run"] is True
        assert r["cc_tool_count"] == 10
        svc.create_session.assert_not_called()


class TestRenderMarkdown:
    def test_empty(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert render_markdown("") == ""

    def test_headers(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert "<h1>Title</h1>" in render_markdown("# Title")
        assert "<h2>Sub</h2>" in render_markdown("## Sub")

    def test_bold_italic(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert "<strong>bold</strong>" in render_markdown("**bold**")
        assert "<em>italic</em>" in render_markdown("*italic*")

    def test_inline_code(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert "<code>foo</code>" in render_markdown("`foo`")

    def test_link(self):
        from governance.services.cc_session_ingestion import render_markdown
        html = render_markdown("[text](http://example.com)")
        assert 'href="http://example.com"' in html
        assert ">text<" in html

    def test_list_items(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert "<li>item</li>" in render_markdown("- item")


class TestCollectFromStore:
    def test_tool_calls(self):
        from governance.services.cc_session_ingestion import _collect_tool_calls_from_store
        data = {"tool_calls": [
            {"tool_name": "mcp__gov-tasks__task_get", "arguments": {"id": "T1"}, "timestamp": "2026-01-01"},
            {"tool_name": "Read", "arguments": {"path": "/a"}, "timestamp": "2026-01-02"},
        ]}
        calls = _collect_tool_calls_from_store(data)
        assert len(calls) == 2
        assert calls[0]["is_mcp"] is True
        assert calls[1]["is_mcp"] is False

    def test_thinking_blocks(self):
        from governance.services.cc_session_ingestion import _collect_thinking_from_store
        data = {"thoughts": [{"thought": "I need to...", "timestamp": "2026-01-01"}]}
        blocks = _collect_thinking_from_store(data)
        assert len(blocks) == 1
        assert blocks[0]["chars"] == len("I need to...")

    def test_empty_store(self):
        from governance.services.cc_session_ingestion import _collect_tool_calls_from_store
        assert _collect_tool_calls_from_store({}) == []


class TestGetSessionDetail:
    @patch("governance.services.cc_session_ingestion.session_service")
    def test_no_session(self, svc):
        svc.get_session.return_value = None
        from governance.services.cc_session_ingestion import get_session_detail
        assert get_session_detail("NONE") is None

    @patch("governance.services.cc_session_ingestion._find_jsonl_for_session")
    @patch("governance.services.cc_session_ingestion.session_service")
    def test_zoom_0(self, svc, find):
        svc.get_session.return_value = {"status": "COMPLETED", "description": "Test"}
        find.return_value = None
        from governance.services.cc_session_ingestion import get_session_detail
        r = get_session_detail("S1", zoom=0)
        assert r["zoom"] == 0
        assert "tool_breakdown" not in r

    @patch("governance.services.cc_session_ingestion._sessions_store", {"S1": {"tool_calls": [
        {"tool_name": "Read", "arguments": {}, "timestamp": "2026-01-01"},
    ]}})
    @patch("governance.services.cc_session_ingestion._find_jsonl_for_session")
    @patch("governance.services.cc_session_ingestion.session_service")
    def test_zoom_2_fallback(self, svc, find):
        svc.get_session.return_value = {"status": "ACTIVE"}
        find.return_value = None
        from governance.services.cc_session_ingestion import get_session_detail
        r = get_session_detail("S1", zoom=2)
        assert r["tool_calls_total"] == 1
        assert r["tool_calls"][0]["name"] == "Read"
