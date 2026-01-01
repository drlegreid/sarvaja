"""
Real-time Monitoring State (P9.6)
=================================
State transforms and helpers for real-time monitoring.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

from .constants import EVENT_TYPE_COLORS, EVENT_TYPE_ICONS, SEVERITY_COLORS


# =============================================================================
# STATE TRANSFORMS
# =============================================================================

def with_monitor_feed(state: Dict[str, Any], feed: List[Dict]) -> Dict[str, Any]:
    """Return new state with monitor feed."""
    return {**state, 'monitor_feed': feed}


def with_monitor_alerts(state: Dict[str, Any], alerts: List[Dict]) -> Dict[str, Any]:
    """Return new state with monitor alerts."""
    return {**state, 'monitor_alerts': alerts}


def with_monitor_stats(state: Dict[str, Any], stats: Dict) -> Dict[str, Any]:
    """Return new state with monitor stats."""
    return {**state, 'monitor_stats': stats}


def with_monitor_filter(state: Dict[str, Any], event_type: Optional[str]) -> Dict[str, Any]:
    """Return new state with monitor filter."""
    return {**state, 'monitor_filter': event_type}


def with_auto_refresh(state: Dict[str, Any], enabled: bool) -> Dict[str, Any]:
    """Return new state with auto-refresh toggle."""
    return {**state, 'auto_refresh': enabled}


def with_top_rules(state: Dict[str, Any], top_rules: List[Dict]) -> Dict[str, Any]:
    """Return new state with top monitored rules."""
    return {**state, 'top_rules': top_rules}


def with_hourly_stats(state: Dict[str, Any], hourly: Dict) -> Dict[str, Any]:
    """Return new state with hourly stats."""
    return {**state, 'hourly_stats': hourly}


# =============================================================================
# UI HELPERS
# =============================================================================

def get_event_type_color(event_type: str) -> str:
    """Get color for event type (pure function)."""
    return EVENT_TYPE_COLORS.get(event_type, 'grey')


def get_event_type_icon(event_type: str) -> str:
    """Get icon for event type (pure function)."""
    return EVENT_TYPE_ICONS.get(event_type, 'mdi-information')


def get_severity_color(severity: str) -> str:
    """Get color for severity (pure function)."""
    return SEVERITY_COLORS.get(severity, 'info')


def format_event_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format event data for display.

    Pure function: same input -> same output.

    Args:
        event: Event dict from monitor

    Returns:
        Formatted event for UI
    """
    event_type = event.get('event_type', 'unknown')
    severity = event.get('severity', 'INFO')

    return {
        'event_id': event.get('event_id', 'Unknown'),
        'event_type': event_type,
        'source': event.get('source', 'Unknown'),
        'timestamp': event.get('timestamp', ''),
        'severity': severity,
        'icon': get_event_type_icon(event_type),
        'color': get_severity_color(severity),
        'rule_id': event.get('details', {}).get('rule_id', ''),
        'details': event.get('details', {}),
    }


def format_alert_item(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format alert data for display.

    Pure function: same input -> same output.

    Args:
        alert: Alert dict from monitor

    Returns:
        Formatted alert for UI
    """
    severity = alert.get('severity', 'INFO')
    acknowledged = alert.get('acknowledged', False)

    return {
        'alert_id': alert.get('alert_id', 'Unknown'),
        'message': alert.get('message', ''),
        'rule_id': alert.get('rule_id', ''),
        'severity': severity,
        'color': get_severity_color(severity),
        'acknowledged': acknowledged,
        'ack_color': 'grey' if acknowledged else 'error',
        'timestamp': alert.get('timestamp', ''),
    }
