"""
Unit tests for Tab Deep Scan Batch 18 — Sessions UI regression recheck.

Covers: sessions_headers in state, end_time annotation consistency,
source_type derivation across all loaders, session detail reset completeness.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Sessions headers declared in initial state ──────────────────────────


class TestSessionsHeadersInState:
    """sessions_headers and sessions_pivot_headers must be in initial state."""

    def test_sessions_headers_declared(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert "sessions_headers" in INITIAL_STATE

    def test_sessions_pivot_headers_declared(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert "sessions_pivot_headers" in INITIAL_STATE

    def test_sessions_headers_has_session_id(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_headers"]
        keys = [h["key"] for h in headers]
        assert "session_id" in keys

    def test_sessions_headers_has_source_type(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_headers"]
        keys = [h["key"] for h in headers]
        assert "source_type" in keys

    def test_sessions_headers_has_duration(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_headers"]
        keys = [h["key"] for h in headers]
        assert "duration" in keys

    def test_sessions_headers_has_status(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_headers"]
        keys = [h["key"] for h in headers]
        assert "status" in keys

    def test_sessions_pivot_headers_has_group(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_pivot_headers"]
        keys = [h["key"] for h in headers]
        assert "group" in keys

    def test_sessions_pivot_headers_has_count(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        headers = INITIAL_STATE["sessions_pivot_headers"]
        keys = [h["key"] for h in headers]
        assert "count" in keys

    def test_headers_match_list_view(self):
        """State headers must match list.py VDataTable headers."""
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        from agent.governance_ui.views.sessions import list as slist
        source = inspect.getsource(slist)
        state_keys = [h["key"] for h in INITIAL_STATE["sessions_headers"]]
        # Each state header key must appear in the list view source
        for key in state_keys:
            assert key in source, f"Header key '{key}' not in list.py"


# ── End-time annotation consistency ────────────────────────────────────


class TestEndTimeAnnotationConsistency:
    """Pagination and initial loader must have same end_time pattern."""

    def test_both_have_completed_pattern(self):
        from agent.governance_ui.controllers import sessions_pagination
        from agent.governance_ui import dashboard_data_loader
        pag_source = inspect.getsource(sessions_pagination)
        dl_source = inspect.getsource(dashboard_data_loader)
        assert "(completed)" in pag_source
        assert "(completed)" in dl_source

    def test_both_have_ongoing_pattern(self):
        from agent.governance_ui.controllers import sessions_pagination
        from agent.governance_ui import dashboard_data_loader
        pag_source = inspect.getsource(sessions_pagination)
        dl_source = inspect.getsource(dashboard_data_loader)
        assert "ongoing" in pag_source
        assert "ongoing" in dl_source

    def test_pagination_checks_status_for_completed(self):
        """Must check session status, not just presence of end_time."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        # Must check status field for COMPLETED/CLOSED
        assert "COMPLETED" in source
        assert "CLOSED" in source

    def test_pagination_checks_active_for_ongoing(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "ACTIVE" in source


# ── Source type derivation completeness ─────────────────────────────────


class TestSourceTypeDerivationCompleteness:
    """source_type must be derived in ALL session load paths."""

    def test_pagination_derives_source_type(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "source_type" in source
        assert "BUG-UI-SESSIONS-003" in source

    def test_select_session_derives_source_type(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-SESSIONS-DETAIL-001" in source

    def test_dashboard_data_loader_derives_source_type(self):
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert "source_type" in source

    def test_all_three_check_cc_session_uuid(self):
        """All loaders must check cc_session_uuid for CC type."""
        from agent.governance_ui.controllers import sessions_pagination, sessions
        from agent.governance_ui import dashboard_data_loader
        for mod in [sessions_pagination, sessions, dashboard_data_loader]:
            source = inspect.getsource(mod)
            assert "cc_session_uuid" in source, f"{mod.__name__} missing cc_session_uuid check"

    def test_all_three_check_chat_pattern(self):
        """All loaders must check -CHAT- pattern for Chat type."""
        from agent.governance_ui.controllers import sessions_pagination, sessions
        from agent.governance_ui import dashboard_data_loader
        for mod in [sessions_pagination, sessions, dashboard_data_loader]:
            source = inspect.getsource(mod)
            assert "-CHAT-" in source, f"{mod.__name__} missing -CHAT- check"


# ── Session detail close resets all state ───────────────────────────────


class TestSessionDetailCloseResetsAllState:
    """close_session_detail must reset ALL detail state variables."""

    def _get_close_source(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Extract just the close_session_detail function
        start = source.index("def close_session_detail")
        end = source.index("\n    @", start + 1)
        return source[start:end]

    def test_resets_selected_session(self):
        src = self._get_close_source()
        assert "selected_session = None" in src

    def test_resets_show_detail(self):
        src = self._get_close_source()
        assert "show_session_detail = False" in src

    def test_resets_tool_calls(self):
        src = self._get_close_source()
        assert "session_tool_calls = []" in src

    def test_resets_thinking(self):
        src = self._get_close_source()
        assert "session_thinking_items = []" in src

    def test_resets_timeline(self):
        src = self._get_close_source()
        assert "session_timeline = []" in src

    def test_resets_tasks(self):
        src = self._get_close_source()
        assert "session_tasks = []" in src

    def test_resets_evidence_html(self):
        src = self._get_close_source()
        assert "session_evidence_html = ''" in src

    def test_resets_transcript(self):
        src = self._get_close_source()
        assert "session_transcript = []" in src

    def test_resets_transcript_page(self):
        src = self._get_close_source()
        assert "session_transcript_page = 1" in src

    def test_resets_transcript_expanded(self):
        src = self._get_close_source()
        assert "session_transcript_expanded_entry = None" in src


# ── Sessions pagination state properly initialized ──────────────────────


class TestSessionsPaginationStateInit:
    """Sessions pagination must have proper defaults."""

    def test_sessions_page_default(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert INITIAL_STATE["sessions_page"] == 1

    def test_sessions_per_page_default(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert INITIAL_STATE["sessions_per_page"] == 20

    def test_sessions_pagination_has_total(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert "total" in INITIAL_STATE["sessions_pagination"]

    def test_sessions_pagination_has_has_more(self):
        from agent.governance_ui.state.initial import get_initial_state as _get_initial_state; INITIAL_STATE = _get_initial_state()
        assert "has_more" in INITIAL_STATE["sessions_pagination"]
