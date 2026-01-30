"""
Tests for monitor grid view.

Per PLAN-UI-OVERHAUL-001 Task 6.2: Monitor Grid view.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestMonitorGridView:
    """Verify monitor uses data table for events."""

    def test_monitor_uses_data_table(self):
        """Monitor view should use VDataTable for events."""
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'VDataTable' in source or 'DataTable' in source, (
            "Monitor view should use VDataTable for event grid"
        )

    def test_monitor_has_event_columns(self):
        """Monitor data table should have event-related columns."""
        from agent.governance_ui.views import monitor_view
        source = inspect.getsource(monitor_view)
        assert 'headers' in source, (
            "Monitor data table should define column headers"
        )
