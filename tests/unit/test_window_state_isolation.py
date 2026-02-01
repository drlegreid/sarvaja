"""
Tests for window state isolation completeness.

Per PLAN-UI-OVERHAUL-001 Task 0.3: Window State Isolation.
Per GAP-UI-AUDIT-002: v6 Proxy-based isolator in JS file.

The isolator logic is in static/window_isolator.js, not window_state.py
(which is a no-op kept for backward compatibility).
"""

import os

import pytest

JS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "agent", "governance_ui", "static", "window_isolator.js",
)


def _read_isolator_js() -> str:
    """Read the window isolator JS source."""
    with open(os.path.normpath(JS_PATH)) as f:
        return f.read()


class TestWindowStateIsolation:
    """Verify window state isolator covers all navigation states."""

    def test_isolator_covers_active_view(self):
        """Window isolator should cover active_view."""
        source = _read_isolator_js()
        assert "active_view" in source

    def test_isolator_covers_agent_detail(self):
        """Window isolator should cover agent detail state."""
        source = _read_isolator_js()
        assert "show_agent_detail" in source, (
            "Window isolator should cover show_agent_detail"
        )

    def test_isolator_covers_agent_selection(self):
        """Window isolator should cover agent selection."""
        source = _read_isolator_js()
        assert "selected_agent" in source, (
            "Window isolator should cover selected_agent"
        )

    def test_isolator_covers_session_form(self):
        """Window isolator should cover session form state."""
        source = _read_isolator_js()
        assert "show_session_form" in source, (
            "Window isolator should cover show_session_form"
        )

    def test_isolator_covers_agent_registration(self):
        """Window isolator should cover agent registration state."""
        source = _read_isolator_js()
        assert "show_agent_registration" in source, (
            "Window isolator should cover show_agent_registration"
        )

    def test_isolator_uses_proxy(self):
        """v6 isolator should use Proxy-based interception."""
        source = _read_isolator_js()
        assert "new Proxy" in source, "v6 should use JS Proxy"

    def test_isolator_has_local_change_detection(self):
        """Isolator should detect local user interactions."""
        source = _read_isolator_js()
        assert "localChangeInProgress" in source
        assert "markLocalChange" in source

    def test_isolator_blocks_remote_writes(self):
        """Isolator should block remote state writes for isolated keys."""
        source = _read_isolator_js()
        assert "Blocked remote write" in source
