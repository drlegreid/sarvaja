"""
Tests for real-time monitoring view.

Per RULE-021: MCP Healthcheck Protocol.
Batch 167: New coverage for views/monitor_view.py (0->10 tests).
"""
import inspect

import pytest


class TestMonitorViewComponents:
    def test_build_monitor_header_callable(self):
        from agent.governance_ui.views.monitor_view import build_monitor_header
        assert callable(build_monitor_header)


class TestMonitorViewContent:
    def test_has_filter_testid(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "monitor-filter" in source

    def test_has_auto_refresh_testid(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "monitor-auto-refresh" in source

    def test_has_event_types(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "rule_query" in source
        assert "violation" in source

    def test_has_pause_icon(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "mdi-pause-circle" in source

    def test_has_play_icon(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "mdi-play-circle" in source

    def test_has_trust_events(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "trust_decrease" in source
        assert "trust_increase" in source

    def test_has_compliance_check(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "compliance_check" in source

    def test_has_refresh_trigger(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "toggle_auto_refresh" in source

    def test_has_monitoring_title(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert "Real-time Rule Monitoring" in source
