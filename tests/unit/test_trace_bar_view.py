"""
Tests for trace bar view component.

Per GAP-UI-048: Bottom bar with technical traces.
Batch 160: New coverage for views/trace_bar_view.py (0→10 tests).
"""
import inspect

import pytest


class TestTraceBarView:
    def test_module_has_build_trace_bar(self):
        from agent.governance_ui.views.trace_bar_view import build_trace_bar
        assert callable(build_trace_bar)

    def test_has_trace_bar_testid(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace-bar" in source

    def test_has_total_badge(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace-total-badge" in source

    def test_has_error_badge(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace-error-badge" in source

    def test_has_clear_button(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace-clear-btn" in source

    def test_has_trace_list(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace-list" in source

    def test_has_filter_buttons(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "trace_filter" in source
        assert "api_call" in source
        assert "ui_action" in source

    def test_has_expansion_panels(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "VExpansionPanel" in source

    def test_has_status_code_display(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "status_code" in source

    def test_has_json_payload_display(self):
        from agent.governance_ui.views import trace_bar_view
        source = inspect.getsource(trace_bar_view)
        assert "mdi-code-json" in source
        assert "request_body" in source
        assert "response_body" in source
