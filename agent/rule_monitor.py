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
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class MonitorEvent:
    """A monitored governance event."""
    event_id: str
    event_type: str
    source: str
    details: Dict[str, Any]
    timestamp: str
    severity: str  # INFO, WARNING, CRITICAL


@dataclass
class Alert:
    """An active alert."""
    alert_id: str
    event_id: str
    rule_id: Optional[str]
    message: str
    severity: str
    acknowledged: bool
    timestamp: str


class RuleMonitor:
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
        """
        Initialize Rule Monitor.

        Args:
            max_events: Maximum events to keep in memory
        """
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
        severity: str = "INFO"
    ) -> Dict[str, Any]:
        """
        Log a governance event.

        Args:
            event_type: Type of event
            source: Event source (agent ID, user, etc.)
            details: Event details
            severity: Event severity

        Returns:
            Event record
        """
        event_id = str(uuid.uuid4())[:8]

        event = MonitorEvent(
            event_id=event_id,
            event_type=event_type,
            source=source,
            details=details,
            timestamp=datetime.now().isoformat(),
            severity=severity if event_type != 'violation' else 'CRITICAL'
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
            'event_type': event_type
        }

    # =========================================================================
    # EVENT FEED
    # =========================================================================

    def get_feed(
        self,
        limit: int = 50,
        event_type: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get event feed.

        Args:
            limit: Maximum events to return
            event_type: Filter by event type
            source: Filter by source

        Returns:
            List of events (newest first)
        """
        events = self._events[::-1]  # Reverse for newest first

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
            timestamp=event.timestamp
        )

        self._alerts[alert_id] = alert
        return alert

    def get_alerts(
        self,
        acknowledged: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts.

        Args:
            acknowledged: Filter by acknowledged status

        Returns:
            List of alerts
        """
        alerts = list(self._alerts.values())

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        # Sort by timestamp descending
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return [asdict(a) for a in alerts]

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge

        Returns:
            Result dict
        """
        if alert_id in self._alerts:
            self._alerts[alert_id].acknowledged = True
            return {'success': True, 'alert_id': alert_id}
        return {'success': False, 'error': 'Alert not found'}

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.

        Returns:
            Statistics dict
        """
        total_events = len(self._events)
        active_alerts = sum(1 for a in self._alerts.values() if not a.acknowledged)

        return {
            'total_events': total_events,
            'events_by_type': dict(self._event_counts),
            'active_alerts': active_alerts,
            'total_alerts': len(self._alerts),
            'rules_monitored': len(self._rule_counts),
            'timestamp': datetime.now().isoformat()
        }

    def get_hourly_stats(self) -> Dict[str, Any]:
        """
        Get hourly statistics.

        Returns:
            Hourly stats dict
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        recent_events = [
            e for e in self._events
            if datetime.fromisoformat(e.timestamp) > one_hour_ago
        ]

        hourly_by_type = defaultdict(int)
        for event in recent_events:
            hourly_by_type[event.event_type] += 1

        return {
            'hour': now.strftime('%Y-%m-%d %H:00'),
            'total': len(recent_events),
            'by_type': dict(hourly_by_type)
        }

    # =========================================================================
    # RULE-SPECIFIC TRACKING
    # =========================================================================

    def get_rule_events(
        self,
        rule_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific rule.

        Args:
            rule_id: Rule ID to filter by
            limit: Maximum events

        Returns:
            List of events for the rule
        """
        events = [
            e for e in self._events
            if e.details.get('rule_id') == rule_id
        ]

        events = events[-limit:][::-1]  # Most recent first
        return [asdict(e) for e in events]

    def get_top_rules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently accessed rules.

        Args:
            limit: Number of rules to return

        Returns:
            List of rules with counts
        """
        sorted_rules = sorted(
            self._rule_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {'rule_id': rule_id, 'event_count': count}
            for rule_id, count in sorted_rules
        ]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_rule_monitor(max_events: int = 1000, seed_demo_data: bool = True) -> RuleMonitor:
    """
    Factory function to create Rule Monitor.

    Args:
        max_events: Maximum events to keep
        seed_demo_data: Whether to add demo events for UI display

    Returns:
        RuleMonitor instance
    """
    monitor = RuleMonitor(max_events=max_events)

    # Add demo events so the monitor tab shows data (GAP-UI-051)
    if seed_demo_data:
        _seed_demo_events(monitor)

    return monitor


def _seed_demo_events(monitor: RuleMonitor) -> None:
    """Seed demo events for UI demonstration (GAP-UI-051)."""
    from datetime import datetime, timedelta

    # Sample events for demonstration
    demo_events = [
        {
            "event_type": "rule_query",
            "source": "claude-code",
            "details": {"rule_id": "RULE-001", "query_type": "get"},
            "severity": "INFO"
        },
        {
            "event_type": "compliance_check",
            "source": "task-orchestrator",
            "details": {"rule_id": "RULE-007", "result": "PASS"},
            "severity": "INFO"
        },
        {
            "event_type": "rule_query",
            "source": "rules-curator",
            "details": {"rule_id": "RULE-012", "query_type": "dependencies"},
            "severity": "INFO"
        },
        {
            "event_type": "trust_increase",
            "source": "task-orchestrator",
            "details": {"agent_id": "code-agent", "old_trust": 0.85, "new_trust": 0.88},
            "severity": "INFO"
        },
        {
            "event_type": "rule_change",
            "source": "admin",
            "details": {"rule_id": "RULE-024", "change": "status update"},
            "severity": "WARNING"
        },
        {
            "event_type": "compliance_check",
            "source": "research-agent",
            "details": {"rule_id": "RULE-021", "result": "PASS"},
            "severity": "INFO"
        },
        {
            "event_type": "violation",
            "source": "external-api",
            "details": {"rule_id": "RULE-007", "violation": "missing MCP healthcheck"},
            "severity": "CRITICAL"
        },
        {
            "event_type": "trust_decrease",
            "source": "governance-system",
            "details": {"agent_id": "external-api", "old_trust": 0.75, "new_trust": 0.60},
            "severity": "WARNING"
        },
    ]

    for event in demo_events:
        monitor.log_event(
            event_type=event["event_type"],
            source=event["source"],
            details=event["details"],
            severity=event["severity"]
        )


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
            source=args.source
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
            {'rule_id': args.rule} if args.rule else {}
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
