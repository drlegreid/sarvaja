"""
Unit tests for Rule Monitor Statistics Mixin.

Per DOC-SIZE-01-v1: Tests for extracted rule_monitor_stats.py module.
Tests: get_statistics, get_hourly_stats, get_rule_events, get_top_rules.
"""

import pytest
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.rule_monitor_stats import RuleMonitorStatsMixin


@dataclass
class MockMonitorEvent:
    event_type: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MockAlert:
    alert_id: str
    acknowledged: bool = False


class MockRuleMonitor(RuleMonitorStatsMixin):
    """Host class for mixin testing."""

    def __init__(self):
        self._events: List[MockMonitorEvent] = []
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._alerts: Dict[str, MockAlert] = {}
        self._rule_counts: Dict[str, int] = defaultdict(int)


@pytest.fixture
def monitor():
    return MockRuleMonitor()


class TestGetStatistics:
    """Tests for get_statistics()."""

    def test_empty_state(self, monitor):
        stats = monitor.get_statistics()
        assert stats["total_events"] == 0
        assert stats["active_alerts"] == 0
        assert stats["total_alerts"] == 0
        assert stats["rules_monitored"] == 0
        assert "timestamp" in stats

    def test_with_events(self, monitor):
        monitor._events = [
            MockMonitorEvent("rule_read", datetime.now().isoformat()),
            MockMonitorEvent("rule_update", datetime.now().isoformat()),
        ]
        monitor._event_counts = {"rule_read": 3, "rule_update": 2}
        stats = monitor.get_statistics()
        assert stats["total_events"] == 2
        assert stats["events_by_type"]["rule_read"] == 3

    def test_with_alerts(self, monitor):
        monitor._alerts = {
            "a1": MockAlert("a1", acknowledged=False),
            "a2": MockAlert("a2", acknowledged=True),
            "a3": MockAlert("a3", acknowledged=False),
        }
        stats = monitor.get_statistics()
        assert stats["active_alerts"] == 2
        assert stats["total_alerts"] == 3

    def test_with_rule_counts(self, monitor):
        monitor._rule_counts = {"R-01": 5, "R-02": 3}
        stats = monitor.get_statistics()
        assert stats["rules_monitored"] == 2


class TestGetHourlyStats:
    """Tests for get_hourly_stats()."""

    def test_empty(self, monitor):
        stats = monitor.get_hourly_stats()
        assert stats["total"] == 0
        assert "hour" in stats

    def test_recent_events_counted(self, monitor):
        now = datetime.now()
        monitor._events = [
            MockMonitorEvent("read", now.isoformat()),
            MockMonitorEvent("read", (now - timedelta(minutes=30)).isoformat()),
            MockMonitorEvent("update", (now - timedelta(minutes=45)).isoformat()),
        ]
        stats = monitor.get_hourly_stats()
        assert stats["total"] == 3
        assert stats["by_type"]["read"] == 2
        assert stats["by_type"]["update"] == 1

    def test_old_events_excluded(self, monitor):
        old = datetime.now() - timedelta(hours=2)
        monitor._events = [
            MockMonitorEvent("read", old.isoformat()),
        ]
        stats = monitor.get_hourly_stats()
        assert stats["total"] == 0


class TestGetRuleEvents:
    """Tests for get_rule_events()."""

    def test_empty(self, monitor):
        assert monitor.get_rule_events("R-01") == []

    def test_filters_by_rule_id(self, monitor):
        monitor._events = [
            MockMonitorEvent("read", datetime.now().isoformat(), {"rule_id": "R-01"}),
            MockMonitorEvent("read", datetime.now().isoformat(), {"rule_id": "R-02"}),
            MockMonitorEvent("update", datetime.now().isoformat(), {"rule_id": "R-01"}),
        ]
        result = monitor.get_rule_events("R-01")
        assert len(result) == 2
        assert all(e["details"]["rule_id"] == "R-01" for e in result)

    def test_respects_limit(self, monitor):
        for i in range(10):
            monitor._events.append(
                MockMonitorEvent("read", datetime.now().isoformat(), {"rule_id": "R-01"})
            )
        result = monitor.get_rule_events("R-01", limit=3)
        assert len(result) == 3

    def test_returns_most_recent_first(self, monitor):
        now = datetime.now()
        monitor._events = [
            MockMonitorEvent("e1", (now - timedelta(minutes=2)).isoformat(), {"rule_id": "R-01"}),
            MockMonitorEvent("e2", now.isoformat(), {"rule_id": "R-01"}),
        ]
        result = monitor.get_rule_events("R-01")
        assert result[0]["event_type"] == "e2"


class TestGetTopRules:
    """Tests for get_top_rules()."""

    def test_empty(self, monitor):
        assert monitor.get_top_rules() == []

    def test_sorted_by_count(self, monitor):
        monitor._rule_counts = {"R-01": 5, "R-02": 10, "R-03": 3}
        result = monitor.get_top_rules()
        assert result[0]["rule_id"] == "R-02"
        assert result[0]["event_count"] == 10
        assert result[-1]["rule_id"] == "R-03"

    def test_respects_limit(self, monitor):
        for i in range(20):
            monitor._rule_counts[f"R-{i:02d}"] = i
        result = monitor.get_top_rules(limit=5)
        assert len(result) == 5
