"""
Monitoring Controllers (GAP-FILE-005)
=====================================
Controller functions for real-time monitoring dashboard (P9.6).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per MULTI-007: Observability Infrastructure

Created: 2024-12-28
Updated: 2026-01-20 - Added load_monitor_data trigger
"""

from typing import Any

from agent.governance_ui import (
    get_monitor_feed,
    acknowledge_monitor_alert,
    get_monitor_alerts,
    get_monitor_stats,
    get_top_monitored_rules,
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

    @ctrl.trigger("load_monitor_data")
    def load_monitor_data():
        """
        Load all monitor data (feed, alerts, stats, top rules).

        Per MULTI-007: Complete data binding for observability dashboard.
        """
        try:
            # Load event feed
            state.monitor_feed = get_monitor_feed(
                limit=50,
                event_type=state.monitor_filter
            )
            # Load active alerts
            state.monitor_alerts = get_monitor_alerts(acknowledged=False)
            # Load statistics
            state.monitor_stats = get_monitor_stats()
            # Load top monitored rules
            state.top_rules = get_top_monitored_rules(limit=10)
        except Exception as e:
            state.status_message = f"Monitor load failed: {str(e)[:50]}"
