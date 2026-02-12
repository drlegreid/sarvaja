"""
Unit tests for Real-time Monitoring State Transforms.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/monitor.py.
Tests: with_monitor_feed, with_monitor_alerts, with_monitor_stats,
       with_monitor_filter, with_auto_refresh, with_top_rules,
       with_hourly_stats, get_event_type_color, get_event_type_icon,
       get_severity_color, format_event_item, format_alert_item.
"""

from agent.governance_ui.state.monitor import (
    with_monitor_feed, with_monitor_alerts, with_monitor_stats,
    with_monitor_filter, with_auto_refresh, with_top_rules,
    with_hourly_stats,
    get_event_type_color, get_event_type_icon, get_severity_color,
    format_event_item, format_alert_item,
)


# ── State Transforms ─────────────────────────────────────


class TestWithMonitorFeed:
    def test_sets_feed(self):
        feed = [{"event_id": "E-1"}]
        result = with_monitor_feed({}, feed)
        assert result["monitor_feed"] == feed

    def test_preserves_other_keys(self):
        result = with_monitor_feed({"x": 1}, [])
        assert result["x"] == 1


class TestWithMonitorAlerts:
    def test_sets_alerts(self):
        alerts = [{"alert_id": "A-1"}]
        assert with_monitor_alerts({}, alerts)["monitor_alerts"] == alerts


class TestWithMonitorStats:
    def test_sets_stats(self):
        stats = {"total": 42}
        assert with_monitor_stats({}, stats)["monitor_stats"] == stats


class TestWithMonitorFilter:
    def test_sets_filter(self):
        assert with_monitor_filter({}, "violation")["monitor_filter"] == "violation"

    def test_clears_filter(self):
        assert with_monitor_filter({}, None)["monitor_filter"] is None


class TestWithAutoRefresh:
    def test_enable(self):
        assert with_auto_refresh({}, True)["auto_refresh"] is True

    def test_disable(self):
        assert with_auto_refresh({}, False)["auto_refresh"] is False


class TestWithTopRules:
    def test_sets_top_rules(self):
        rules = [{"rule_id": "R-1", "count": 5}]
        assert with_top_rules({}, rules)["top_rules"] == rules


class TestWithHourlyStats:
    def test_sets_hourly(self):
        hourly = {"00": 5, "01": 3}
        assert with_hourly_stats({}, hourly)["hourly_stats"] == hourly


# ── UI Helpers ────────────────────────────────────────────


class TestGetEventTypeColor:
    def test_known_types(self):
        assert get_event_type_color("rule_query") == "info"
        assert get_event_type_color("violation") == "error"
        assert get_event_type_color("compliance_check") == "success"

    def test_unknown_fallback(self):
        assert get_event_type_color("random") == "grey"


class TestGetEventTypeIcon:
    def test_known_types(self):
        assert get_event_type_icon("rule_query") == "mdi-magnify"
        assert get_event_type_icon("violation") == "mdi-alert-circle"

    def test_unknown_fallback(self):
        assert get_event_type_icon("random") == "mdi-information"


class TestGetSeverityColor:
    def test_known_severities(self):
        assert get_severity_color("INFO") == "info"
        assert get_severity_color("WARNING") == "warning"
        assert get_severity_color("CRITICAL") == "error"

    def test_unknown_fallback(self):
        assert get_severity_color("NONE") == "info"


# ── Format Functions ──────────────────────────────────────


class TestFormatEventItem:
    def test_full_event(self):
        event = {
            "event_id": "E-001",
            "event_type": "violation",
            "source": "monitor",
            "timestamp": "2026-01-01T10:00:00",
            "severity": "CRITICAL",
            "details": {"rule_id": "R-1"},
        }
        result = format_event_item(event)
        assert result["event_id"] == "E-001"
        assert result["event_type"] == "violation"
        assert result["source"] == "monitor"
        assert result["severity"] == "CRITICAL"
        assert result["icon"] == "mdi-alert-circle"
        assert result["color"] == "error"
        assert result["rule_id"] == "R-1"

    def test_defaults(self):
        result = format_event_item({})
        assert result["event_id"] == "Unknown"
        assert result["source"] == "Unknown"
        assert result["icon"] == "mdi-information"
        assert result["rule_id"] == ""
        assert result["details"] == {}


class TestFormatAlertItem:
    def test_full_alert(self):
        alert = {
            "alert_id": "A-001",
            "message": "Rule violated",
            "rule_id": "R-1",
            "severity": "WARNING",
            "acknowledged": True,
            "timestamp": "2026-01-01T12:00:00",
        }
        result = format_alert_item(alert)
        assert result["alert_id"] == "A-001"
        assert result["message"] == "Rule violated"
        assert result["severity"] == "WARNING"
        assert result["color"] == "warning"
        assert result["acknowledged"] is True
        assert result["ack_color"] == "grey"

    def test_unacknowledged(self):
        result = format_alert_item({"acknowledged": False})
        assert result["ack_color"] == "error"

    def test_defaults(self):
        result = format_alert_item({})
        assert result["alert_id"] == "Unknown"
        assert result["message"] == ""
        assert result["acknowledged"] is False
        assert result["ack_color"] == "error"
