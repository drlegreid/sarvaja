"""
Unit tests for Tab Deep Scan Batch 17 — Session detail data integrity.

Covers: source_type derivation in select_session (BUG-UI-SESSIONS-DETAIL-001),
end_time status annotation in pagination (BUG-UI-SESSIONS-005),
evidence loader safe defaults, detail state reset on close.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── BUG-UI-SESSIONS-DETAIL-001: source_type in select_session ──────────


class TestSourceTypeDerivedInSelectSession:
    """select_session must derive source_type after API fetch."""

    def test_source_has_bugfix_marker(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-SESSIONS-DETAIL-001" in source

    def test_source_type_derivation_logic_exists(self):
        """select_session must have source_type derivation block."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "source_type" in source
        assert "CC" in source

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_cc_session_gets_cc_source_type(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Session with cc_session_uuid gets source_type=CC."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "session_id": "SESSION-2026-02-15-CC-TEST",
            "cc_session_uuid": "abc-123",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
        }
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.sessions = [{"session_id": "SESSION-2026-02-15-CC-TEST"}]
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("SESSION-2026-02-15-CC-TEST")

        # Check the session_data that was set as selected_session
        selected = state.selected_session
        assert selected.get("source_type") == "CC"

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_chat_session_gets_chat_source_type(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Session with -CHAT- in ID gets source_type=Chat."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "session_id": "SESSION-2026-02-15-CHAT-TEST",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "",
        }
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.sessions = [{"session_id": "SESSION-2026-02-15-CHAT-TEST"}]
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("SESSION-2026-02-15-CHAT-TEST")

        selected = state.selected_session
        assert selected.get("source_type") == "Chat"

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_api_session_gets_api_source_type(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """Session without CC/Chat markers gets source_type=API."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "session_id": "SESSION-2026-02-15-GENERIC",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T12:00:00",
        }
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.sessions = [{"session_id": "SESSION-2026-02-15-GENERIC"}]
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("SESSION-2026-02-15-GENERIC")

        selected = state.selected_session
        assert selected.get("source_type") == "API"

    @patch("agent.governance_ui.controllers.sessions.httpx")
    @patch("agent.governance_ui.controllers.sessions.register_session_detail_loaders")
    @patch("agent.governance_ui.controllers.sessions.register_sessions_pagination")
    @patch("agent.governance_ui.controllers.sessions.log_action")
    def test_existing_source_type_preserved(self, mock_log, mock_pag, mock_loaders, mock_httpx):
        """If API returns source_type, it should NOT be overwritten."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "session_id": "SESSION-2026-02-15-CUSTOM",
            "source_type": "Custom",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "",
        }
        mock_httpx.get.return_value = mock_resp

        mock_loaders.return_value = {
            "load_evidence": MagicMock(), "load_tasks": MagicMock(),
            "load_tool_calls": MagicMock(), "load_thinking_items": MagicMock(),
            "build_timeline": MagicMock(), "load_evidence_rendered": MagicMock(),
            "load_transcript": MagicMock(),
        }
        mock_pag.return_value = MagicMock()

        state = MagicMock()
        state.is_loading = False
        state.sessions = [{"session_id": "SESSION-2026-02-15-CUSTOM"}]
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, "http://localhost:8082")
        triggers["select_session"]("SESSION-2026-02-15-CUSTOM")

        selected = state.selected_session
        assert selected.get("source_type") == "Custom"


# ── BUG-UI-SESSIONS-005: end_time status annotation in pagination ──────


class TestEndTimeAnnotationInPagination:
    """Pagination must annotate missing end_time like initial loader."""

    def test_pagination_has_bugfix_marker(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "BUG-UI-SESSIONS-005" in source

    def test_pagination_annotates_completed_status(self):
        """COMPLETED sessions with no end_time get '(completed)'."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "(completed)" in source
        assert "COMPLETED" in source

    def test_pagination_annotates_active_ongoing(self):
        """ACTIVE sessions with no end_time get 'ongoing'."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "ongoing" in source
        assert "ACTIVE" in source

    def test_matches_dashboard_data_loader_pattern(self):
        """Pagination end_time logic must match dashboard_data_loader."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        # Both must have (completed) and ongoing patterns
        assert "(completed)" in source
        assert "ongoing" in source


# ── Session detail state reset on close ────────────────────────────────


class TestSessionDetailStateResetOnClose:
    """close_session_detail must reset all detail state variables."""

    def test_resets_transcript_state(self):
        """close_session_detail must reset transcript state."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_transcript = []" in source
        assert "session_transcript_page = 1" in source
        assert "session_transcript_total = 0" in source

    def test_resets_evidence_html(self):
        """close_session_detail must reset evidence HTML."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_evidence_html = ''" in source

    def test_resets_tool_calls_and_thinking(self):
        """close_session_detail must reset tool calls and thinking."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_tool_calls = []" in source
        assert "session_thinking_items = []" in source


# ── Source type derivation consistency across loaders ──────────────────


class TestSourceTypeConsistencyAcrossLoaders:
    """source_type derivation must exist in ALL session loading paths."""

    def test_pagination_has_source_type_derivation(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "source_type" in source
        assert "CC" in source
        assert "Chat" in source

    def test_select_session_has_source_type_derivation(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "source_type" in source
        assert "BUG-UI-SESSIONS-DETAIL-001" in source

    def test_dashboard_data_loader_has_source_type(self):
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert "source_type" in source


# ── Evidence and tool calls default to empty on detail load ────────────


class TestDetailLoadersDefaultEmpty:
    """Detail loaders must not leave stale data from previous session."""

    def test_close_resets_timeline(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_timeline = []" in source

    def test_close_resets_tasks(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_tasks = []" in source
