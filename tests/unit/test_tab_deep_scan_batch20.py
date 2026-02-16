"""
Unit tests for Tab Deep Scan Batch 20 — Cross-tab staleness + state cleanup.

Covers: on_view_change detail clearing (BUG-UI-STALE-DETAIL-001),
select_session pre-clear (BUG-UI-STALE-DETAIL-003),
error handling consistency.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── BUG-UI-STALE-DETAIL-001: on_view_change clears detail state ────────


class TestOnViewChangeClearsDetailState:
    """on_view_change must close all detail views and forms."""

    def test_source_has_stale_detail_fix(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "BUG-UI-STALE-DETAIL-001" in source

    def test_clears_session_detail(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_session_detail = False" in source

    def test_clears_task_detail(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_task_detail = False" in source

    def test_clears_rule_detail(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_rule_detail = False" in source

    def test_clears_decision_detail(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_decision_detail = False" in source

    def test_clears_session_form(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_session_form = False" in source

    def test_clears_rule_form(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "show_rule_form = False" in source

    def test_clears_error_state(self):
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "has_error = False" in source


# ── BUG-UI-STALE-DETAIL-003: select_session clears prior detail ────────


class TestSelectSessionClearsPriorDetail:
    """select_session must clear stale detail before loading new session."""

    def test_source_has_stale_detail_fix(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-STALE-DETAIL-003" in source

    def test_clears_tool_calls_before_load(self):
        """Tool calls from prior session must be cleared."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Extract select_session function
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        # Clear must come before loaders
        clear_pos = fn_src.index("session_tool_calls = []")
        load_pos = fn_src.index("load_evidence")
        assert clear_pos < load_pos

    def test_clears_thinking_items(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "session_thinking_items = []" in fn_src

    def test_clears_evidence_html(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "session_evidence_html = ''" in fn_src

    def test_clears_evidence_search(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "evidence_search = ''" in fn_src

    def test_clears_transcript(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "session_transcript = []" in fn_src

    def test_resets_transcript_page(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "session_transcript_page = 1" in fn_src


# ── Error handling patterns ─────────────────────────────────────────────


class TestErrorHandlingPatterns:
    """CRUD controllers must use consistent error handling."""

    def test_sessions_crud_uses_add_error_trace(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert source.count("add_error_trace") >= 3

    def test_decisions_crud_uses_add_error_trace(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert source.count("add_error_trace") >= 2

    def test_rules_crud_uses_add_error_trace(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert source.count("add_error_trace") >= 2

    def test_tasks_crud_uses_add_error_trace(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert source.count("add_error_trace") >= 3

    def test_detail_loaders_use_add_error_trace(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert source.count("add_error_trace") >= 5


# ── Cross-navigation state management ──────────────────────────────────


class TestCrossNavigationState:
    """Cross-tab navigation must close source detail view."""

    def test_navigate_to_rule_closes_session_detail(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def navigate_to_rule_from_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "show_session_detail = False" in fn_src

    def test_navigate_to_decision_closes_session_detail(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def navigate_to_decision_from_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "show_session_detail = False" in fn_src

    def test_navigate_to_rule_sets_nav_source(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "nav_source_view" in source
        assert "nav_source_id" in source
