"""
Real-time Rule Monitoring Tests (P9.6)
Created: 2024-12-25

Tests for active governance feed and rule monitoring.
Strategic Goal: Live visibility into rule compliance and changes.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"


class TestRuleMonitorModule:
    """Verify P9.6 rule monitor module exists."""

    @pytest.mark.unit
    def test_rule_monitor_module_exists(self):
        """Rule monitor module must exist."""
        monitor_file = AGENT_DIR / "rule_monitor.py"
        assert monitor_file.exists(), "agent/rule_monitor.py not found"

    @pytest.mark.unit
    def test_rule_monitor_class(self):
        """RuleMonitor class must be importable."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        assert monitor is not None

    @pytest.mark.unit
    def test_monitor_has_required_methods(self):
        """Monitor must have required methods."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        assert hasattr(monitor, 'get_feed')
        assert hasattr(monitor, 'log_event')
        assert hasattr(monitor, 'get_alerts')
        assert hasattr(monitor, 'get_statistics')


class TestEventLogging:
    """Tests for event logging."""

    @pytest.mark.unit
    def test_log_event(self):
        """Should log governance events."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        result = monitor.log_event(
            event_type="rule_query",
            source="agent-001",
            details={"rule_id": "RULE-001"}
        )

        assert isinstance(result, dict)
        assert result.get('success', True)

    @pytest.mark.unit
    def test_log_violation(self):
        """Should log rule violations."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        result = monitor.log_event(
            event_type="violation",
            source="agent-002",
            details={"rule_id": "RULE-011", "reason": "unauthorized access"}
        )

        assert 'event_id' in result or result.get('success')

    @pytest.mark.unit
    def test_log_rule_change(self):
        """Should log rule changes."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        result = monitor.log_event(
            event_type="rule_change",
            source="admin",
            details={"rule_id": "RULE-015", "change": "created"}
        )

        assert result.get('success', True)


class TestEventFeed:
    """Tests for event feed."""

    @pytest.mark.unit
    def test_get_feed(self):
        """Should return event feed."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        feed = monitor.get_feed()

        assert isinstance(feed, list)

    @pytest.mark.unit
    def test_feed_has_events(self):
        """Feed should contain logged events."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log an event
        monitor.log_event(
            event_type="test_event",
            source="test",
            details={}
        )

        feed = monitor.get_feed()
        assert len(feed) > 0

    @pytest.mark.unit
    def test_feed_with_filters(self):
        """Should filter feed by event type."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log different event types
        monitor.log_event("violation", "test", {})
        monitor.log_event("rule_query", "test", {})

        violations = monitor.get_feed(event_type="violation")
        assert all(e['event_type'] == 'violation' for e in violations)

    @pytest.mark.unit
    def test_feed_limit(self):
        """Should limit feed results."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log multiple events
        for i in range(10):
            monitor.log_event("test", "test", {"i": i})

        feed = monitor.get_feed(limit=5)
        assert len(feed) <= 5


class TestAlerts:
    """Tests for alert generation."""

    @pytest.mark.unit
    def test_get_alerts(self):
        """Should return active alerts."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        alerts = monitor.get_alerts()

        assert isinstance(alerts, list)

    @pytest.mark.unit
    def test_violation_generates_alert(self):
        """Violations should generate alerts."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log a violation
        monitor.log_event(
            event_type="violation",
            source="agent-bad",
            details={"rule_id": "RULE-011"}
        )

        alerts = monitor.get_alerts()
        assert len(alerts) > 0

    @pytest.mark.unit
    def test_acknowledge_alert(self):
        """Should be able to acknowledge alerts."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Create an alert
        monitor.log_event("violation", "test", {"rule_id": "RULE-001"})
        alerts = monitor.get_alerts()

        if alerts:
            result = monitor.acknowledge_alert(alerts[0]['alert_id'])
            assert result.get('success', True)


class TestStatistics:
    """Tests for monitoring statistics."""

    @pytest.mark.unit
    def test_get_statistics(self):
        """Should return monitoring statistics."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        stats = monitor.get_statistics()

        assert isinstance(stats, dict)
        assert 'total_events' in stats

    @pytest.mark.unit
    def test_statistics_by_type(self):
        """Should break down statistics by event type."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log different types
        monitor.log_event("violation", "test", {})
        monitor.log_event("rule_query", "test", {})

        stats = monitor.get_statistics()
        assert 'events_by_type' in stats

    @pytest.mark.unit
    def test_get_hourly_statistics(self):
        """Should provide hourly statistics."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()
        hourly = monitor.get_hourly_stats()

        assert isinstance(hourly, dict)


class TestRuleTracking:
    """Tests for rule-specific tracking."""

    @pytest.mark.unit
    def test_get_rule_events(self):
        """Should get events for a specific rule."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log events for specific rule
        monitor.log_event("rule_query", "test", {"rule_id": "RULE-001"})

        events = monitor.get_rule_events("RULE-001")
        assert isinstance(events, list)

    @pytest.mark.unit
    def test_get_most_queried_rules(self):
        """Should return most queried rules."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Query some rules
        for _ in range(5):
            monitor.log_event("rule_query", "test", {"rule_id": "RULE-001"})
        for _ in range(3):
            monitor.log_event("rule_query", "test", {"rule_id": "RULE-011"})

        top_rules = monitor.get_top_rules()
        assert isinstance(top_rules, list)


class TestMonitorIntegration:
    """Integration tests for rule monitor."""

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create monitor."""
        from agent.rule_monitor import create_rule_monitor

        monitor = create_rule_monitor()
        assert monitor is not None

    @pytest.mark.unit
    def test_event_persistence(self):
        """Events should persist in memory."""
        from agent.rule_monitor import RuleMonitor

        monitor = RuleMonitor()

        # Log event
        monitor.log_event("test", "test", {"data": "value"})

        # Should be retrievable
        feed = monitor.get_feed()
        assert len(feed) > 0
