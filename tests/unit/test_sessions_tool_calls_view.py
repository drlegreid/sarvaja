"""
Tests for session tool calls drill-down view.

Per PLAN-UI-OVERHAUL-001 Task 5.2: Session Drill-Down.
Batch 167: New coverage for views/sessions/tool_calls.py (0->8 tests).
"""
import inspect

import pytest


class TestSessionsToolCallsComponents:
    def test_build_tool_calls_card_callable(self):
        from agent.governance_ui.views.sessions.tool_calls import build_tool_calls_card
        assert callable(build_tool_calls_card)


class TestSessionsToolCallsContent:
    def test_has_tool_calls_testid(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "session-tool-calls" in source

    def test_has_tools_icon(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "mdi-tools" in source

    def test_has_loading_state(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "session_tool_calls_loading" in source

    def test_has_empty_message(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "No tool call data" in source

    def test_has_expansion_panels(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "VExpansionPanels" in source

    def test_has_count_chip(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "session_tool_calls.length" in source

    def test_has_title_label(self):
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert "Tool Calls" in source
