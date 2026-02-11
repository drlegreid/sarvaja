"""
Real-time Rule Monitoring (P9.6)
Created: 2024-12-25

Active governance feed and rule monitoring:
- Event logging
- Alert generation
- Statistics tracking
- Rule-specific monitoring

Per RULE-001: Session Evidence Logging
Per RULE-011: Multi-Agent Governance
Per DOC-SIZE-01-v1: Models in rule_monitor_models.py, stats in rule_monitor_stats.py.

Usage:
    monitor = RuleMonitor()
    monitor.log_event("rule_query", "agent-001", {"rule_id": "RULE-001"})
    feed = monitor.get_feed(limit=50)
    alerts = monitor.get_alerts()
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict

from .rule_monitor_models import MonitorEvent, Alert, seed_demo_events  # noqa: F401
from .rule_monitor_models import DEMO_EVENTS  # noqa: F401 — re-export
from .rule_monitor_stats import RuleMonitorStatsMixin  # noqa: F401 — re-export

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


class RuleMonitor(RuleMonitorStatsMixin):
    """
    Real-time Rule Monitoring.

    Features:
    - Event logging for all governance activities
    - Alert generation for violations
    - Statistics and metrics
    - Rule-specific event tracking

    Event Types:
    - rule_query: Rule was queried
    - rule_change: Rule was modified
    - violation: Rule was violated
    - compliance_check: Compliance was checked

    Example:
        monitor = RuleMonitor()
        monitor.log_event("rule_query", "agent-001", {"rule_id": "RULE-001"})
        alerts = monitor.get_alerts()
    """

    # Event types that generate alerts
    ALERT_EVENTS = ['violation', 'rule_change', 'trust_decrease']

    def __init__(self, max_events: int = 1000):
        """Initialize Rule Monitor."""
        self.max_events = max_events
        self._events: List[MonitorEvent] = []
        self._alerts: Dict[str, Alert] = {}
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._rule_counts: Dict[str, int] = defaultdict(int)

    # =========================================================================
    # EVENT LOGGING
    # =========================================================================

    def log_event(
        self,
        event_type: str,
        source: str,
        details: Dict[str, Any],
        severity: str = "INFO",
    ) -> Dict[str, Any]:
        """Log a governance event."""
        event_id = str(uuid.uuid4())[:8]

        event = MonitorEvent(
            event_id=event_id,
            event_type=event_type,
            source=source,
            details=details,
            timestamp=datetime.now().isoformat(),
            severity=severity if event_type != 'violation' else 'CRITICAL',
        )

        self._events.append(event)
        self._event_counts[event_type] += 1

        # Track rule-specific events
        rule_id = details.get('rule_id')
        if rule_id:
            self._rule_counts[rule_id] += 1

        # Generate alert for certain events
        if event_type in self.ALERT_EVENTS:
            self._create_alert(event)

        # Trim old events
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]

        return {
            'success': True,
            'event_id': event_id,
            'event_type': event_type,
        }

    # =========================================================================
    # EVENT FEED
    # =========================================================================

    def get_feed(
        self,
        limit: int = 50,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get event feed (newest first)."""
        events = self._events[::-1]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        events = events[:limit]
        return [asdict(e) for e in events]

    # =========================================================================
    # ALERTS
    # =========================================================================

    def _create_alert(self, event: MonitorEvent) -> Alert:
        """Create an alert from an event."""
        alert_id = str(uuid.uuid4())[:8]
        rule_id = event.details.get('rule_id')

        if event.event_type == 'violation':
            message = f"Rule violation by {event.source}"
            if rule_id:
                message += f" on {rule_id}"
        elif event.event_type == 'rule_change':
            message = f"Rule {rule_id or 'unknown'} was modified"
        else:
            message = f"{event.event_type} event from {event.source}"

        alert = Alert(
            alert_id=alert_id,
            event_id=event.event_id,
            rule_id=rule_id,
            message=message,
            severity=event.severity,
            acknowledged=False,
            timestamp=event.timestamp,
        )

        self._alerts[alert_id] = alert
        return alert

    def get_alerts(
        self,
        acknowledged: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Get active alerts."""
        alerts = list(self._alerts.values())

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return [asdict(a) for a in alerts]

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an alert."""
        if alert_id in self._alerts:
            self._alerts[alert_id].acknowledged = True
            return {'success': True, 'alert_id': alert_id}
        return {'success': False, 'error': 'Alert not found'}


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_rule_monitor(
    max_events: int = 1000,
    seed_demo_data: bool = True,
) -> RuleMonitor:
    """Factory function to create Rule Monitor."""
    monitor = RuleMonitor(max_events=max_events)
    if seed_demo_data:
        seed_demo_events(monitor)
    return monitor


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for rule monitor."""
    import argparse

    parser = argparse.ArgumentParser(description="Rule Monitor")
    parser.add_argument("command", choices=["feed", "alerts", "stats", "log"])
    parser.add_argument("--type", "-t", help="Event type")
    parser.add_argument("--source", "-s", help="Event source")
    parser.add_argument("--rule", "-r", help="Rule ID")
    parser.add_argument("--limit", "-l", type=int, default=20)
    args = parser.parse_args()

    monitor = create_rule_monitor()

    if args.command == "feed":
        feed = monitor.get_feed(
            limit=args.limit,
            event_type=args.type,
            source=args.source,
        )
        for event in feed:
            print(f"{event['timestamp']} | {event['event_type']} | {event['source']}")

    elif args.command == "alerts":
        alerts = monitor.get_alerts()
        for alert in alerts:
            status = "ACK" if alert['acknowledged'] else "NEW"
            print(f"[{status}] {alert['message']}")

    elif args.command == "stats":
        stats = monitor.get_statistics()
        print(json.dumps(stats, indent=2))

    elif args.command == "log" and args.type and args.source:
        result = monitor.log_event(
            args.type,
            args.source,
            {'rule_id': args.rule} if args.rule else {},
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
