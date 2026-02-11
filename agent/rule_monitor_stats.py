"""
Rule Monitor Statistics & Rule Tracking (Mixin).

Per DOC-SIZE-01-v1: Extracted from rule_monitor.py (484 lines).
Statistics and per-rule event tracking methods.
"""

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List


class RuleMonitorStatsMixin:
    """Mixin providing statistics and rule-specific tracking.

    Expects host class to provide:
        self._events: List[MonitorEvent]
        self._event_counts: Dict[str, int]
        self._alerts: Dict[str, Alert]
        self._rule_counts: Dict[str, int]
    """

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        total_events = len(self._events)
        active_alerts = sum(1 for a in self._alerts.values() if not a.acknowledged)

        return {
            'total_events': total_events,
            'events_by_type': dict(self._event_counts),
            'active_alerts': active_alerts,
            'total_alerts': len(self._alerts),
            'rules_monitored': len(self._rule_counts),
            'timestamp': datetime.now().isoformat(),
        }

    def get_hourly_stats(self) -> Dict[str, Any]:
        """Get hourly statistics."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        recent_events = [
            e for e in self._events
            if datetime.fromisoformat(e.timestamp) > one_hour_ago
        ]

        hourly_by_type: Dict[str, int] = defaultdict(int)
        for event in recent_events:
            hourly_by_type[event.event_type] += 1

        return {
            'hour': now.strftime('%Y-%m-%d %H:00'),
            'total': len(recent_events),
            'by_type': dict(hourly_by_type),
        }

    def get_rule_events(
        self,
        rule_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get events for a specific rule."""
        events = [
            e for e in self._events
            if e.details.get('rule_id') == rule_id
        ]

        events = events[-limit:][::-1]  # Most recent first
        return [asdict(e) for e in events]

    def get_top_rules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed rules."""
        sorted_rules = sorted(
            self._rule_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        return [
            {'rule_id': rule_id, 'event_count': count}
            for rule_id, count in sorted_rules
        ]
