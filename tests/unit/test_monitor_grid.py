"""
Tests for monitor grid view.

Per PLAN-UI-OVERHAUL-001 Task 6.2: Monitor Grid view.
Batch 159 deepening (was 2 tests, now 8).
"""
import inspect

import pytest


class TestMonitorGridView:
    def test_monitor_uses_data_table(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'VDataTable' in source or 'DataTable' in source

    def test_monitor_has_event_columns(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'headers' in source

    def test_has_filter_testid(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'monitor-filter' in source

    def test_has_auto_refresh(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'auto_refresh' in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'mdi-refresh' in source

    def test_build_monitor_header_callable(self):
        from agent.governance_ui.views.monitor_view import build_monitor_header
        assert callable(build_monitor_header)
