"""
Real-Time Monitoring Functions (GAP-FILE-006)
==============================================
Real-time monitoring for P9.6.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

from typing import Dict, List, Any, Optional

# Singleton monitor instance
_monitor_instance = None


def get_rule_monitor():
    """
    Get or create singleton RuleMonitor instance.

    Returns:
        RuleMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        from agent.rule_monitor import create_rule_monitor
        _monitor_instance = create_rule_monitor()
    return _monitor_instance


def get_monitor_feed(limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get monitoring event feed.

    Args:
        limit: Maximum events to return
        event_type: Optional filter by event type

    Returns:
        List of events (newest first)
    """
    monitor = get_rule_monitor()
    return monitor.get_feed(limit=limit, event_type=event_type)


def get_monitor_alerts(acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Get active monitoring alerts.

    Args:
        acknowledged: Optional filter by acknowledged status

    Returns:
        List of alerts
    """
    monitor = get_rule_monitor()
    return monitor.get_alerts(acknowledged=acknowledged)


def get_monitor_stats() -> Dict[str, Any]:
    """
    Get monitoring statistics.

    Returns:
        Stats dict with event counts, alerts, etc.
    """
    monitor = get_rule_monitor()
    return monitor.get_statistics()


def log_monitor_event(
    event_type: str,
    source: str,
    details: Dict[str, Any],
    severity: str = "INFO"
) -> Dict[str, Any]:
    """
    Log a governance event.

    Args:
        event_type: Type of event (rule_query, violation, rule_change, etc.)
        source: Event source (agent ID, user, etc.)
        details: Event details
        severity: Event severity (INFO, WARNING, CRITICAL)

    Returns:
        Event record
    """
    monitor = get_rule_monitor()
    return monitor.log_event(event_type, source, details, severity)


def acknowledge_monitor_alert(alert_id: str) -> Dict[str, Any]:
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Result dict
    """
    monitor = get_rule_monitor()
    return monitor.acknowledge_alert(alert_id)


def get_top_monitored_rules(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most frequently accessed rules.

    Args:
        limit: Number of rules to return

    Returns:
        List of rules with access counts
    """
    monitor = get_rule_monitor()
    return monitor.get_top_rules(limit=limit)


def get_hourly_monitor_stats() -> Dict[str, Any]:
    """
    Get hourly monitoring statistics.

    Returns:
        Hourly stats dict
    """
    monitor = get_rule_monitor()
    return monitor.get_hourly_stats()
