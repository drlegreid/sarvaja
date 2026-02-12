"""
Unit tests for Session Detail Lazy Loading (Phase 2).

Per feedback #2: Claude thoughts & MCP tool calls lazy loading
with paginated endpoints and markdown rendering support.
Tests: zoom=2/3 in get_session_detail, paginated tools/thoughts,
       chat-bridge session tool_calls/thoughts exposure, markdown.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

_SVC = "governance.services.cc_session_ingestion"
_STORES = "governance.stores"


def _make_tool_use(name="Read", input_summary='{"path":"f.py"}', is_mcp=False):
    tu = MagicMock()
    tu.name = name
    tu.input_summary = input_summary
    tu.is_mcp = is_mcp
    tu.tool_use_id = "tu_123"
    return tu


def _make_entry(tool_uses=None, thinking_chars=0, thinking_content=None,
                timestamp=None, entry_type="assistant", text_content=None):
    entry = MagicMock()
    entry.tool_uses = tool_uses or []
    entry.tool_results = []
    entry.thinking_chars = thinking_chars
    entry.thinking_content = thinking_content
    entry.timestamp = timestamp or datetime(2026, 2, 11, 10, 0)
    entry.entry_type = entry_type
    entry.text_content = text_content
    entry.is_compaction = False
    entry.is_api_error = False
    entry.model = "claude-opus-4-6"
    return entry


# ── get_session_detail zoom=2 ────────────────────────────


class TestSessionDetailZoom2:
    """zoom=2: Individual tool calls with inputs."""

    @patch(f"{_SVC}.parse_log_file")
    @patch(f"{_SVC}._find_jsonl_for_session")
    @patch(f"{_SVC}.session_service")
    def test_zoom2_includes_tool_calls(self, mock_svc, mock_find, mock_parse):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {
            "session_id": "S-1", "status": "COMPLETED",
        }
        mock_find.return_value = "/tmp/test.jsonl"
        mock_parse.return_value = iter([
            _make_entry(tool_uses=[
                _make_tool_use("Read", '{"path":"a.py"}'),
                _make_tool_use("mcp__gov__rule_get", '{"id":"R1"}', is_mcp=True),
            ]),
            _make_entry(tool_uses=[_make_tool_use("Write", '{"path":"b.py"}')]),
        ])

        result = get_session_detail("S-1", zoom=2)
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 3
        assert result["tool_calls"][0]["name"] == "Read"
        assert result["tool_calls"][1]["is_mcp"] is True

    @patch(f"{_SVC}.parse_log_file")
    @patch(f"{_SVC}._find_jsonl_for_session")
    @patch(f"{_SVC}.session_service")
    def test_zoom2_paginated_default(self, mock_svc, mock_find, mock_parse):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {"session_id": "S-1", "status": "COMPLETED"}
        mock_find.return_value = "/tmp/test.jsonl"
        # 30 tool calls
        entries = [_make_entry(tool_uses=[_make_tool_use(f"Tool{i}")]) for i in range(30)]
        mock_parse.return_value = iter(entries)

        result = get_session_detail("S-1", zoom=2, page=1, per_page=20)
        assert len(result["tool_calls"]) == 20
        assert result["tool_calls_total"] == 30
        assert result["tool_calls_page"] == 1


# ── get_session_detail zoom=3 ────────────────────────────


class TestSessionDetailZoom3:
    """zoom=3: Full thinking content included."""

    @patch(f"{_SVC}.parse_log_file")
    @patch(f"{_SVC}._find_jsonl_for_session")
    @patch(f"{_SVC}.session_service")
    def test_zoom3_includes_thinking_blocks(self, mock_svc, mock_find, mock_parse):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {"session_id": "S-1", "status": "COMPLETED"}
        mock_find.return_value = "/tmp/test.jsonl"
        mock_parse.return_value = iter([
            _make_entry(thinking_chars=500, thinking_content="Deep reasoning about X"),
            _make_entry(thinking_chars=300, thinking_content="Analyzing Y"),
        ])

        result = get_session_detail("S-1", zoom=3)
        assert "thinking_blocks" in result
        assert len(result["thinking_blocks"]) == 2
        assert "Deep reasoning" in result["thinking_blocks"][0]["content"]

    @patch(f"{_SVC}.parse_log_file")
    @patch(f"{_SVC}._find_jsonl_for_session")
    @patch(f"{_SVC}.session_service")
    def test_zoom3_paginated(self, mock_svc, mock_find, mock_parse):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {"session_id": "S-1", "status": "COMPLETED"}
        mock_find.return_value = "/tmp/test.jsonl"
        entries = [_make_entry(thinking_chars=100, thinking_content=f"Block {i}")
                   for i in range(25)]
        mock_parse.return_value = iter(entries)

        result = get_session_detail("S-1", zoom=3, page=1, per_page=10)
        assert len(result["thinking_blocks"]) == 10
        assert result["thinking_blocks_total"] == 25


# ── Chat bridge tool calls/thoughts in detail ───────────


class TestChatBridgeSessionDetail:
    """For chat-bridge sessions, expose tool_calls/thoughts from _sessions_store."""

    @patch(f"{_SVC}._find_jsonl_for_session", return_value=None)
    @patch(f"{_SVC}.session_service")
    def test_zoom2_falls_back_to_sessions_store(self, mock_svc, mock_find):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {
            "session_id": "SESSION-2026-02-11-CHAT-TEST",
            "status": "COMPLETED",
        }

        # Patch at the import binding in cc_session_ingestion, not governance.stores
        with patch(f"{_SVC}._sessions_store", {
            "SESSION-2026-02-11-CHAT-TEST": {
                "session_id": "SESSION-2026-02-11-CHAT-TEST",
                "tool_calls": [
                    {"tool_name": "/status", "timestamp": "2026-02-11T10:00:00"},
                    {"tool_name": "query_llm", "timestamp": "2026-02-11T10:01:00"},
                ],
                "thoughts": [
                    {"thought": "Reasoning about query", "thought_type": "reasoning"},
                ],
            }
        }):
            result = get_session_detail("SESSION-2026-02-11-CHAT-TEST", zoom=2)
            assert "tool_calls" in result
            assert len(result["tool_calls"]) == 2

    @patch(f"{_SVC}._find_jsonl_for_session", return_value=None)
    @patch(f"{_SVC}.session_service")
    def test_zoom3_falls_back_to_thoughts(self, mock_svc, mock_find):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {
            "session_id": "SESSION-2026-02-11-CHAT-X",
            "status": "COMPLETED",
        }

        with patch(f"{_SVC}._sessions_store", {
            "SESSION-2026-02-11-CHAT-X": {
                "session_id": "SESSION-2026-02-11-CHAT-X",
                "thoughts": [
                    {"thought": "Analysis of issue", "thought_type": "reasoning"},
                ],
            }
        }):
            result = get_session_detail("SESSION-2026-02-11-CHAT-X", zoom=3)
            assert "thinking_blocks" in result
            assert len(result["thinking_blocks"]) == 1


# ── zoom=0 and zoom=1 unchanged ─────────────────────────


class TestSessionDetailBasicZooms:
    """Verify zoom=0 and zoom=1 still work as before."""

    @patch(f"{_SVC}.session_service")
    def test_zoom0_summary_only(self, mock_svc):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {
            "session_id": "S-1", "status": "ACTIVE",
            "description": "Test", "start_time": "2026-02-11T10:00:00",
        }
        result = get_session_detail("S-1", zoom=0)
        assert result["zoom"] == 0
        assert "summary" in result
        assert "tool_breakdown" not in result

    @patch(f"{_SVC}.parse_log_file")
    @patch(f"{_SVC}._find_jsonl_for_session")
    @patch(f"{_SVC}.session_service")
    def test_zoom1_tool_breakdown(self, mock_svc, mock_find, mock_parse):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = {
            "session_id": "S-1", "status": "COMPLETED",
        }
        mock_find.return_value = "/tmp/test.jsonl"
        mock_parse.return_value = iter([
            _make_entry(tool_uses=[_make_tool_use("Read")], thinking_chars=100),
        ])

        result = get_session_detail("S-1", zoom=1)
        assert "tool_breakdown" in result
        assert result["tool_breakdown"]["Read"] == 1

    @patch(f"{_SVC}.session_service")
    def test_not_found(self, mock_svc):
        from governance.services.cc_session_ingestion import get_session_detail

        mock_svc.get_session.return_value = None
        result = get_session_detail("MISSING", zoom=0)
        assert result is None


# ── Paginated API routes ─────────────────────────────────


class TestDetailRouteParams:
    """Verify detail route accepts page/per_page params."""

    def test_route_exists(self):
        from governance.routes.sessions.detail import router
        routes = [r.path for r in router.routes]
        assert "/sessions/{session_id}/detail" in routes

    def test_tools_endpoint_exists(self):
        from governance.routes.sessions.detail import router
        routes = [r.path for r in router.routes]
        assert "/sessions/{session_id}/tools" in routes

    def test_thoughts_endpoint_exists(self):
        from governance.routes.sessions.detail import router
        routes = [r.path for r in router.routes]
        assert "/sessions/{session_id}/thoughts" in routes


# ── Markdown rendering endpoint ──────────────────────────


class TestMarkdownEndpoint:
    """Verify markdown rendering for evidence files."""

    def test_markdown_to_html_basic(self):
        from governance.services.cc_session_ingestion import render_markdown
        html = render_markdown("# Title\n\nSome **bold** text")
        assert "<h1>" in html or "<h1" in html
        assert "<strong>" in html or "bold" in html

    def test_markdown_code_blocks(self):
        from governance.services.cc_session_ingestion import render_markdown
        html = render_markdown("```python\nprint('hello')\n```")
        assert "print" in html
        assert "<code" in html or "<pre" in html

    def test_markdown_empty(self):
        from governance.services.cc_session_ingestion import render_markdown
        html = render_markdown("")
        assert html == "" or html.strip() == ""
