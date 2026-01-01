"""
Monitoring Controllers (GAP-FILE-005)
=====================================
Controller functions for real-time monitoring dashboard (P9.6).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

from typing import Any

from agent.governance_ui import (
    get_monitor_feed,
    acknowledge_monitor_alert,
    get_monitor_alerts,
)


def register_monitor_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register monitoring controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused but kept for consistency)
    """

    @ctrl.set("filter_monitor_events")
    def filter_monitor_events(event_type):
        """Filter monitoring events by type."""
        state.monitor_filter = event_type
        state.monitor_feed = get_monitor_feed(limit=50, event_type=event_type)

    @ctrl.set("acknowledge_alert")
    def acknowledge_alert(alert_id):
        """Acknowledge a monitoring alert."""
        result = acknowledge_monitor_alert(alert_id)
        if result.get('success'):
            state.monitor_alerts = get_monitor_alerts(acknowledged=False)
            state.status_message = f"Alert {alert_id} acknowledged"

    @ctrl.trigger("toggle_auto_refresh")
    def toggle_auto_refresh():
        """Toggle auto-refresh for monitoring view."""
        state.auto_refresh = not state.auto_refresh
