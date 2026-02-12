"""
Unit tests for Rule Monitor.

Batch 122: Tests for agent/rule_monitor.py
- RuleMonitor: log_event, get_feed, get_alerts, acknowledge_alert
- Alert generation for violation/rule_change/trust_decrease
- Event trimming at max_events
- Factory function create_rule_monitor
- RuleMonitorStatsMixin: get_statistics, get_hourly_stats, get_rule_events, get_top_rules
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ── RuleMonitor Core ────────────────────────────────────────


class TestRuleMonitorInit:
    """Test RuleMonitor initialization."""

    def test_default_max_events(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        assert m.max_events == 1000

    def test_custom_max_events(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor(max_events=50)
        assert m.max_events == 50

    def test_starts_empty(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        assert len(m._events) == 0
        assert len(m._alerts) == 0


class TestLogEvent:
    """Test log_event method."""

    def test_returns_success(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        result = m.log_event("rule_query", "test-agent", {"rule_id": "R-1"})
        assert result["success"] is True
        assert result["event_type"] == "rule_query"
        assert "event_id" in result

    def test_event_stored(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "agent-1", {"rule_id": "R-1"})
        assert len(m._events) == 1
        assert m._events[0].event_type == "rule_query"
        assert m._events[0].source == "agent-1"

    def test_event_count_tracked(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {})
        m.log_event("rule_query", "b", {})
        m.log_event("violation", "c", {})
        assert m._event_counts["rule_query"] == 2
        assert m._event_counts["violation"] == 1

    def test_rule_count_tracked(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {"rule_id": "R-1"})
        m.log_event("rule_query", "a", {"rule_id": "R-1"})
        m.log_event("rule_query", "a", {"rule_id": "R-2"})
        assert m._rule_counts["R-1"] == 2
        assert m._rule_counts["R-2"] == 1

    def test_no_rule_id_skips_rule_count(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {})
        assert len(m._rule_counts) == 0

    def test_violation_forced_critical(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "agent", {}, severity="INFO")
        assert m._events[0].severity == "CRITICAL"

    def test_non_violation_preserves_severity(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "agent", {}, severity="WARNING")
        assert m._events[0].severity == "WARNING"

    def test_event_trimming(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor(max_events=5)
        for i in range(10):
            m.log_event("rule_query", f"agent-{i}", {})
        assert len(m._events) == 5
        # Should keep the most recent 5
        assert m._events[0].source == "agent-5"
        assert m._events[-1].source == "agent-9"


class TestAlertGeneration:
    """Test alert creation for specific event types."""

    def test_violation_creates_alert(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "bad-agent", {"rule_id": "R-1"})
        assert len(m._alerts) == 1

    def test_rule_change_creates_alert(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_change", "admin", {"rule_id": "R-2"})
        assert len(m._alerts) == 1

    def test_trust_decrease_creates_alert(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("trust_decrease", "system", {"agent_id": "a-1"})
        assert len(m._alerts) == 1

    def test_rule_query_no_alert(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "agent", {})
        assert len(m._alerts) == 0

    def test_compliance_check_no_alert(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("compliance_check", "agent", {})
        assert len(m._alerts) == 0

    def test_violation_alert_message_includes_source(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "bad-agent", {"rule_id": "R-1"})
        alert = list(m._alerts.values())[0]
        assert "bad-agent" in alert.message
        assert "R-1" in alert.message

    def test_alert_not_acknowledged_by_default(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "agent", {})
        alert = list(m._alerts.values())[0]
        assert alert.acknowledged is False


class TestGetFeed:
    """Test get_feed method."""

    def test_empty_feed(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        assert m.get_feed() == []

    def test_newest_first(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "first", {})
        m.log_event("rule_query", "second", {})
        feed = m.get_feed()
        assert feed[0]["source"] == "second"
        assert feed[1]["source"] == "first"

    def test_limit(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        for i in range(10):
            m.log_event("rule_query", f"agent-{i}", {})
        feed = m.get_feed(limit=3)
        assert len(feed) == 3

    def test_filter_by_event_type(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {})
        m.log_event("violation", "b", {})
        m.log_event("rule_query", "c", {})
        feed = m.get_feed(event_type="violation")
        assert len(feed) == 1
        assert feed[0]["source"] == "b"

    def test_filter_by_source(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "agent-A", {})
        m.log_event("rule_query", "agent-B", {})
        m.log_event("rule_query", "agent-A", {})
        feed = m.get_feed(source="agent-A")
        assert len(feed) == 2

    def test_returns_dicts(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {"x": 1})
        feed = m.get_feed()
        assert isinstance(feed[0], dict)
        assert feed[0]["details"]["x"] == 1


class TestGetAlerts:
    """Test get_alerts method."""

    def test_empty_alerts(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        assert m.get_alerts() == []

    def test_filter_unacknowledged(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "a", {})
        m.log_event("violation", "b", {})
        alert_id = list(m._alerts.keys())[0]
        m.acknowledge_alert(alert_id)
        unack = m.get_alerts(acknowledged=False)
        assert len(unack) == 1

    def test_filter_acknowledged(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "a", {})
        alert_id = list(m._alerts.keys())[0]
        m.acknowledge_alert(alert_id)
        ack = m.get_alerts(acknowledged=True)
        assert len(ack) == 1

    def test_sorted_by_timestamp_desc(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "first", {})
        m.log_event("rule_change", "second", {"rule_id": "R-1"})
        alerts = m.get_alerts()
        assert alerts[0]["timestamp"] >= alerts[-1]["timestamp"]


class TestAcknowledgeAlert:
    """Test acknowledge_alert method."""

    def test_acknowledge_existing(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("violation", "a", {})
        alert_id = list(m._alerts.keys())[0]
        result = m.acknowledge_alert(alert_id)
        assert result["success"] is True
        assert m._alerts[alert_id].acknowledged is True

    def test_acknowledge_nonexistent(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        result = m.acknowledge_alert("nonexistent-id")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ── Factory Function ────────────────────────────────────────


class TestCreateRuleMonitor:
    """Test create_rule_monitor factory."""

    def test_default_with_demo_data(self):
        from agent.rule_monitor import create_rule_monitor
        m = create_rule_monitor()
        assert len(m._events) > 0  # Demo events seeded

    def test_no_demo_data(self):
        from agent.rule_monitor import create_rule_monitor
        m = create_rule_monitor(seed_demo_data=False)
        assert len(m._events) == 0

    def test_custom_max_events(self):
        from agent.rule_monitor import create_rule_monitor
        m = create_rule_monitor(max_events=50, seed_demo_data=False)
        assert m.max_events == 50

    def test_demo_creates_alerts(self):
        from agent.rule_monitor import create_rule_monitor
        m = create_rule_monitor()
        # DEMO_EVENTS has violation + rule_change + trust_decrease → alerts
        assert len(m._alerts) >= 2


# ── RuleMonitorStatsMixin ───────────────────────────────────


class TestStatsMixin:
    """Test statistics mixin methods."""

    def test_get_statistics_structure(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {"rule_id": "R-1"})
        m.log_event("violation", "b", {"rule_id": "R-2"})
        stats = m.get_statistics()
        assert stats["total_events"] == 2
        assert stats["events_by_type"]["rule_query"] == 1
        assert stats["active_alerts"] == 1  # violation
        assert stats["rules_monitored"] == 2
        assert "timestamp" in stats

    def test_get_hourly_stats(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {})
        stats = m.get_hourly_stats()
        assert stats["total"] >= 1
        assert "hour" in stats

    def test_get_rule_events(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        m.log_event("rule_query", "a", {"rule_id": "R-1"})
        m.log_event("rule_query", "b", {"rule_id": "R-2"})
        m.log_event("violation", "c", {"rule_id": "R-1"})
        events = m.get_rule_events("R-1")
        assert len(events) == 2
        # Most recent first
        assert events[0]["event_type"] == "violation"

    def test_get_rule_events_limit(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        for i in range(10):
            m.log_event("rule_query", f"a-{i}", {"rule_id": "R-1"})
        events = m.get_rule_events("R-1", limit=3)
        assert len(events) == 3

    def test_get_top_rules(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        for _ in range(5):
            m.log_event("rule_query", "a", {"rule_id": "R-1"})
        for _ in range(3):
            m.log_event("rule_query", "a", {"rule_id": "R-2"})
        top = m.get_top_rules(limit=2)
        assert len(top) == 2
        assert top[0]["rule_id"] == "R-1"
        assert top[0]["event_count"] == 5
        assert top[1]["rule_id"] == "R-2"

    def test_get_top_rules_empty(self):
        from agent.rule_monitor import RuleMonitor
        m = RuleMonitor()
        assert m.get_top_rules() == []


# ── Models and Demo Data ────────────────────────────────────


class TestMonitorModels:
    """Test MonitorEvent and Alert dataclasses."""

    def test_monitor_event_fields(self):
        from agent.rule_monitor_models import MonitorEvent
        e = MonitorEvent(
            event_id="e1", event_type="rule_query",
            source="test", details={}, timestamp="2026-01-01",
            severity="INFO",
        )
        assert e.event_id == "e1"
        assert e.severity == "INFO"

    def test_alert_fields(self):
        from agent.rule_monitor_models import Alert
        a = Alert(
            alert_id="a1", event_id="e1", rule_id="R-1",
            message="test", severity="WARNING",
            acknowledged=False, timestamp="2026-01-01",
        )
        assert a.alert_id == "a1"
        assert a.acknowledged is False

    def test_demo_events_is_list(self):
        from agent.rule_monitor_models import DEMO_EVENTS
        assert isinstance(DEMO_EVENTS, list)
        assert len(DEMO_EVENTS) == 8

    def test_seed_demo_events(self):
        from agent.rule_monitor import RuleMonitor
        from agent.rule_monitor_models import seed_demo_events
        m = RuleMonitor()
        seed_demo_events(m)
        assert len(m._events) == 8
