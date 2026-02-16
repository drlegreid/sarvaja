"""Tests for session enhancement features (2026-02-15 night batch).

- BUG-EVIDENCE-STALE-001: Evidence attach should refresh detail view
- GAP-SESSION-SEARCH-001: Server-side keyword search via API route
- BUG-EVIDENCE-DEDUP-001: Evidence endpoint deduplication
- BUG-TOOL-META-001: Tool call metadata (latency_ms, server_name, tool_category)
"""

from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


class TestSessionSearchRoute:
    """Tests for search parameter in GET /sessions API route."""

    @pytest.mark.asyncio
    async def test_search_param_passed_to_service(self):
        """Search query param should be forwarded to list_sessions service."""
        from governance.routes.sessions.crud import list_sessions as route_handler

        mock_result = {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": 50,
            "has_more": False,
        }

        with patch("governance.routes.sessions.crud.session_service") as mock_svc:
            mock_svc.list_sessions.return_value = mock_result

            await route_handler(
                offset=0, limit=50, sort_by="started_at", order="desc",
                status=None, agent_id=None, date_from=None, date_to=None,
                exclude_test=False, search="dark-mode",
            )

            mock_svc.list_sessions.assert_called_once_with(
                status=None, agent_id=None,
                sort_by="started_at", order="desc",
                offset=0, limit=50,
                date_from=None, date_to=None,
                exclude_test=False,
                search="dark-mode",
            )

    @pytest.mark.asyncio
    async def test_search_none_by_default(self):
        """Search should be None by default (no filtering)."""
        from governance.routes.sessions.crud import list_sessions as route_handler

        mock_result = {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": 50,
            "has_more": False,
        }

        with patch("governance.routes.sessions.crud.session_service") as mock_svc:
            mock_svc.list_sessions.return_value = mock_result

            await route_handler(
                offset=0, limit=50, sort_by="started_at", order="desc",
                status=None, agent_id=None, date_from=None, date_to=None,
                exclude_test=False, search=None,
            )

            call_kwargs = mock_svc.list_sessions.call_args[1]
            assert call_kwargs["search"] is None


class TestEvidenceAttachRefresh:
    """Tests for BUG-EVIDENCE-STALE-001: Refreshing detail after attach."""

    def test_attach_evidence_calls_detail_loaders(self):
        """After successful attach, load_evidence and load_evidence_rendered should be called."""
        from agent.governance_ui.controllers.sessions import register_sessions_controllers

        state = MagicMock()
        ctrl = MagicMock()
        api_base_url = "http://localhost:8082"

        # Track what triggers are registered
        triggers = {}

        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        ctrl.set = mock_trigger

        # Mock detail loaders
        mock_loaders = {
            "load_evidence": MagicMock(),
            "load_evidence_rendered": MagicMock(),
            "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(),
            "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(),
            "load_transcript": MagicMock(),
            "load_transcript_entry": MagicMock(),
        }

        with patch(
            "agent.governance_ui.controllers.sessions.register_sessions_pagination",
            return_value=MagicMock(),
        ), patch(
            "agent.governance_ui.controllers.sessions.register_session_detail_loaders",
            return_value=mock_loaders,
        ):
            register_sessions_controllers(state, ctrl, api_base_url)

        assert "attach_evidence" in triggers

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            triggers["attach_evidence"]("SESSION-123", "evidence/test.md")

        # Verify detail loaders were called after successful attach
        mock_loaders["load_evidence"].assert_called_once_with("SESSION-123")
        mock_loaders["load_evidence_rendered"].assert_called_once_with("SESSION-123")


class TestSearchQueryPagination:
    """Tests for search triggering pagination reset in UI controller."""

    def test_search_param_added_to_api_call(self):
        """Sessions pagination should include search param in first API request."""
        from agent.governance_ui.controllers.sessions_pagination import register_sessions_pagination

        state = MagicMock()
        ctrl = MagicMock()
        api_base_url = "http://localhost:8082"

        # Set up state attributes
        state.sessions_page = 1
        state.sessions_per_page = 20
        state.sessions_search_query = "sarvaja"
        state.sessions_filter_status = None
        state.sessions_filter_agent = None
        state.sessions_date_from = None
        state.sessions_date_to = None

        load_fn = register_sessions_pagination(state, ctrl, api_base_url)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [],
            "pagination": {"total": 0, "offset": 0, "limit": 20, "has_more": False, "returned": 0},
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            load_fn()

            # First call = paginated sessions (includes search)
            # Second call = timeline metrics (does NOT include search)
            first_call = mock_client.get.call_args_list[0]
            params = first_call[1].get("params", {})
            assert params.get("search") == "sarvaja"

    def test_empty_search_not_sent(self):
        """Empty search query should not be sent as API param."""
        from agent.governance_ui.controllers.sessions_pagination import register_sessions_pagination

        state = MagicMock()
        ctrl = MagicMock()
        api_base_url = "http://localhost:8082"

        state.sessions_page = 1
        state.sessions_per_page = 20
        state.sessions_search_query = ""
        state.sessions_filter_status = None
        state.sessions_filter_agent = None
        state.sessions_date_from = None
        state.sessions_date_to = None

        load_fn = register_sessions_pagination(state, ctrl, api_base_url)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [],
            "pagination": {"total": 0, "offset": 0, "limit": 20, "has_more": False, "returned": 0},
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            load_fn()

            call_args = mock_client.get.call_args
            params = call_args[1].get("params", {})
            assert "search" not in params


class TestEvidenceDedup:
    """Tests for BUG-EVIDENCE-DEDUP-001: Evidence endpoint deduplication."""

    @pytest.mark.asyncio
    async def test_evidence_deduplicates_results(self):
        """Duplicate evidence paths should be removed."""
        from governance.routes.sessions.relations import get_session_evidence

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.get_session.return_value = mock_session
        # Simulate TypeDB returning duplicates
        mock_client.get_session_evidence.return_value = [
            "evidence/SESSION-123.md",
            "evidence/SESSION-123.md",
            "evidence/DSM-123.md",
        ]

        with patch("governance.routes.sessions.relations.get_typedb_client", return_value=mock_client):
            result = await get_session_evidence("SESSION-123")

        assert result["evidence_count"] == 2
        assert result["evidence_files"] == [
            "evidence/SESSION-123.md",
            "evidence/DSM-123.md",
        ]

    @pytest.mark.asyncio
    async def test_evidence_preserves_order_after_dedup(self):
        """Dedup should preserve first occurrence order."""
        from governance.routes.sessions.relations import get_session_evidence

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.get_session.return_value = mock_session
        mock_client.get_session_evidence.return_value = [
            "evidence/B.md",
            "evidence/A.md",
            "evidence/B.md",
            "evidence/C.md",
            "evidence/A.md",
        ]

        with patch("governance.routes.sessions.relations.get_typedb_client", return_value=mock_client):
            result = await get_session_evidence("SESSION-123")

        assert result["evidence_files"] == [
            "evidence/B.md",
            "evidence/A.md",
            "evidence/C.md",
        ]


class TestClassifyTool:
    """Tests for _classify_tool inline classification."""

    def test_classify_cc_builtin(self):
        from governance.services.cc_session_ingestion import _classify_tool
        assert _classify_tool("Read") == "cc_builtin"
        assert _classify_tool("Write") == "cc_builtin"
        assert _classify_tool("Bash") == "cc_builtin"
        assert _classify_tool("TodoWrite") == "cc_builtin"

    def test_classify_mcp_governance(self):
        from governance.services.cc_session_ingestion import _classify_tool
        assert _classify_tool("mcp__gov-core__rule_get") == "mcp_governance"
        assert _classify_tool("mcp__gov-sessions__session_start") == "mcp_governance"
        assert _classify_tool("mcp__gov-tasks__task_create") == "mcp_governance"

    def test_classify_mcp_other(self):
        from governance.services.cc_session_ingestion import _classify_tool
        assert _classify_tool("mcp__playwright__click") == "mcp_other"
        assert _classify_tool("mcp__claude-mem__query") == "mcp_other"

    def test_classify_chat_command(self):
        from governance.services.cc_session_ingestion import _classify_tool
        assert _classify_tool("/status") == "chat_command"
        assert _classify_tool("/help") == "chat_command"

    def test_classify_unknown(self):
        from governance.services.cc_session_ingestion import _classify_tool
        assert _classify_tool("") == "unknown"
        assert _classify_tool("SomeRandomTool") == "unknown"


class TestToolCallMetadata:
    """Tests for BUG-TOOL-META-001: tool_category in session detail."""

    def test_tool_calls_include_category(self):
        """Tool calls from JSONL should include tool_category field."""
        from governance.services.cc_session_ingestion import get_session_detail
        from governance.session_metrics.models import ParsedEntry, ToolUseInfo

        mock_session = {"status": "COMPLETED", "description": "test",
                        "start_time": "", "end_time": "",
                        "cc_session_uuid": None, "cc_project_slug": None,
                        "cc_git_branch": None, "cc_tool_count": None,
                        "cc_thinking_chars": None, "cc_compaction_count": None}

        entries = [
            ParsedEntry(
                timestamp=datetime(2026, 2, 15, 10, 0, 0),
                entry_type="assistant",
                tool_uses=[
                    ToolUseInfo(name="Read", input_summary='{"file": "test.py"}', is_mcp=False, tool_use_id="tu_1"),
                    ToolUseInfo(name="mcp__gov-core__rule_get", input_summary='{"id": "R-1"}', is_mcp=True, tool_use_id="tu_2"),
                ],
            ),
        ]

        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value="/tmp/test.jsonl"), \
             patch("governance.services.cc_session_ingestion.parse_log_file", return_value=iter(entries)):
            mock_svc.get_session.return_value = mock_session
            result = get_session_detail("SESSION-TEST", zoom=2)

        calls = result["tool_calls"]
        assert len(calls) == 2
        assert calls[0]["tool_category"] == "cc_builtin"
        assert calls[1]["tool_category"] == "mcp_governance"

    def test_tool_calls_correlate_latency_and_server(self):
        """Tool results should populate latency_ms and server_name."""
        from governance.services.cc_session_ingestion import get_session_detail
        from governance.session_metrics.models import ParsedEntry, ToolUseInfo, ToolResultInfo

        mock_session = {"status": "COMPLETED", "description": "test",
                        "start_time": "", "end_time": "",
                        "cc_session_uuid": None, "cc_project_slug": None,
                        "cc_git_branch": None, "cc_tool_count": None,
                        "cc_thinking_chars": None, "cc_compaction_count": None}

        entries = [
            # Assistant sends tool_use
            ParsedEntry(
                timestamp=datetime(2026, 2, 15, 10, 0, 0),
                entry_type="assistant",
                tool_uses=[
                    ToolUseInfo(name="mcp__playwright__click", input_summary='{}', is_mcp=True, tool_use_id="tu_abc"),
                ],
            ),
            # User returns tool_result 500ms later
            ParsedEntry(
                timestamp=datetime(2026, 2, 15, 10, 0, 0, 500000),
                entry_type="user",
                tool_results=[
                    ToolResultInfo(tool_use_id="tu_abc", server_name="playwright"),
                ],
            ),
        ]

        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value="/tmp/test.jsonl"), \
             patch("governance.services.cc_session_ingestion.parse_log_file", return_value=iter(entries)):
            mock_svc.get_session.return_value = mock_session
            result = get_session_detail("SESSION-TEST", zoom=2)

        calls = result["tool_calls"]
        assert len(calls) == 1
        assert calls[0]["server_name"] == "playwright"
        assert calls[0]["latency_ms"] == 500
        # Internal field should be stripped
        assert "_use_ts" not in calls[0]

    def test_store_fallback_includes_category(self):
        """Chat-bridge store fallback should also include tool_category."""
        from governance.services.cc_session_ingestion import _collect_tool_calls_from_store

        store_data = {
            "tool_calls": [
                {"tool_name": "Read", "arguments": {}, "timestamp": "2026-02-15T10:00:00"},
                {"tool_name": "mcp__gov-tasks__task_create", "arguments": {"name": "test"}, "timestamp": "2026-02-15T10:01:00"},
            ]
        }

        calls = _collect_tool_calls_from_store(store_data)
        assert calls[0]["tool_category"] == "cc_builtin"
        assert calls[1]["tool_category"] == "mcp_governance"

    def test_uncorrelated_tool_has_no_latency(self):
        """Tool uses without matching results should not have latency_ms."""
        from governance.services.cc_session_ingestion import get_session_detail
        from governance.session_metrics.models import ParsedEntry, ToolUseInfo

        mock_session = {"status": "COMPLETED", "description": "test",
                        "start_time": "", "end_time": "",
                        "cc_session_uuid": None, "cc_project_slug": None,
                        "cc_git_branch": None, "cc_tool_count": None,
                        "cc_thinking_chars": None, "cc_compaction_count": None}

        entries = [
            ParsedEntry(
                timestamp=datetime(2026, 2, 15, 10, 0, 0),
                entry_type="assistant",
                tool_uses=[
                    ToolUseInfo(name="Bash", input_summary='{"cmd": "ls"}', is_mcp=False, tool_use_id="tu_orphan"),
                ],
            ),
            # No matching tool_result entry
        ]

        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value="/tmp/test.jsonl"), \
             patch("governance.services.cc_session_ingestion.parse_log_file", return_value=iter(entries)):
            mock_svc.get_session.return_value = mock_session
            result = get_session_detail("SESSION-TEST", zoom=2)

        calls = result["tool_calls"]
        assert len(calls) == 1
        assert "latency_ms" not in calls[0]
        assert "server_name" not in calls[0]


class TestDetailBackButton:
    """Tests for BUG-DETAIL-STALE-001: Back button should use close_session_detail."""

    def test_back_button_uses_trigger(self):
        """Detail view back button should call trigger('close_session_detail')."""
        from pathlib import Path

        detail_py = Path("agent/governance_ui/views/sessions/detail.py").read_text()
        # Verify close_session_detail trigger is used, not raw state manipulation
        assert "trigger('close_session_detail')" in detail_py
        # Verify old pattern is NOT present
        assert "show_session_detail = false; selected_session = null" not in detail_py

    def test_close_session_detail_resets_all_state(self):
        """close_session_detail should reset all detail-related state variables."""
        from agent.governance_ui.controllers.sessions import register_sessions_controllers

        state = MagicMock()
        ctrl = MagicMock()
        api_base_url = "http://localhost:8082"

        # Pre-populate state with stale data
        state.show_session_detail = True
        state.selected_session = {"session_id": "STALE"}
        state.session_tool_calls = [{"name": "old"}]
        state.session_thinking_items = [{"content": "old"}]
        state.session_timeline = [{"type": "old"}]
        state.session_tasks = [{"task_id": "old"}]
        state.session_evidence_html = "<p>old</p>"
        state.session_transcript = [{"content": "old"}]

        registered = {}

        def mock_trigger(name):
            def decorator(fn):
                registered[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        ctrl.set = mock_trigger

        with patch(
            "agent.governance_ui.controllers.sessions.register_sessions_pagination",
            return_value=MagicMock(),
        ), patch(
            "agent.governance_ui.controllers.sessions.register_session_detail_loaders",
            return_value={
                "load_evidence": MagicMock(), "load_evidence_rendered": MagicMock(),
                "load_tasks": MagicMock(), "load_tool_calls": MagicMock(),
                "load_thinking_items": MagicMock(), "build_timeline": MagicMock(),
                "load_transcript": MagicMock(), "load_transcript_entry": MagicMock(),
            },
        ):
            register_sessions_controllers(state, ctrl, api_base_url)

        assert "close_session_detail" in registered
        registered["close_session_detail"]()

        assert state.show_session_detail is False
        assert state.selected_session is None
        assert state.session_tool_calls == []
        assert state.session_thinking_items == []
        assert state.session_timeline == []
        assert state.session_tasks == []
        assert state.session_evidence_html == ''
        assert state.session_transcript == []
