"""
Tests for session drill-down with tool call metadata.

Per PLAN-UI-OVERHAUL-001 Task 5.2: Session Drill-Down.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestSessionToolCallsView:
    """Verify session detail shows tool calls section."""

    def test_session_detail_has_tool_calls_card(self):
        """Session detail should include a tool calls component."""
        from agent.governance_ui.views.sessions import detail
        source = inspect.getsource(detail)
        assert 'tool_call' in source.lower(), (
            "Session detail should reference tool calls component"
        )

    def test_tool_calls_component_exists(self):
        """A tool_calls module should exist in sessions views."""
        from agent.governance_ui.views.sessions import tool_calls
        assert hasattr(tool_calls, 'build_tool_calls_card'), (
            "tool_calls module should export build_tool_calls_card"
        )

    def test_tool_calls_card_uses_expansion_panels(self):
        """Tool calls should use expansion panels for drill-down."""
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert 'VExpansionPanel' in source or 'expansion' in source.lower(), (
            "Tool calls should use expansion panels for collapsible drill-down"
        )

    def test_tool_calls_shows_thinking_items(self):
        """Tool calls section should also show thinking/reasoning items."""
        from agent.governance_ui.views.sessions import tool_calls
        source = inspect.getsource(tool_calls)
        assert 'thinking' in source.lower(), (
            "Tool calls section should include thinking items display"
        )
