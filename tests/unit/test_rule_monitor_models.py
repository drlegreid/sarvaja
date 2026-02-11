"""
Unit tests for Rule Monitor Models & Demo Seed Data.

Per DOC-SIZE-01-v1: Tests for extracted rule_monitor_models.py.
Tests: MonitorEvent, Alert, DEMO_EVENTS, seed_demo_events.
"""

import pytest
from unittest.mock import MagicMock

from agent.rule_monitor_models import (
    MonitorEvent,
    Alert,
    DEMO_EVENTS,
    seed_demo_events,
)


class TestMonitorEvent:
    """Tests for MonitorEvent dataclass."""

    def test_creation(self):
        event = MonitorEvent(
            event_id="EV-001",
            event_type="rule_query",
            source="claude-code",
            details={"rule_id": "R-1"},
            timestamp="2026-02-11T10:00:00",
            severity="INFO",
        )
        assert event.event_id == "EV-001"
        assert event.severity == "INFO"


class TestAlert:
    """Tests for Alert dataclass."""

    def test_creation(self):
        alert = Alert(
            alert_id="AL-001",
            event_id="EV-001",
            rule_id="R-1",
            message="Test alert",
            severity="WARNING",
            acknowledged=False,
            timestamp="2026-02-11T10:00:00",
        )
        assert alert.alert_id == "AL-001"
        assert alert.acknowledged is False


class TestDemoEvents:
    """Tests for DEMO_EVENTS constant."""

    def test_has_events(self):
        assert len(DEMO_EVENTS) == 8

    def test_event_structure(self):
        for event in DEMO_EVENTS:
            assert "event_type" in event
            assert "source" in event
            assert "details" in event
            assert "severity" in event

    def test_severities_valid(self):
        valid = {"INFO", "WARNING", "CRITICAL"}
        for event in DEMO_EVENTS:
            assert event["severity"] in valid


class TestSeedDemoEvents:
    """Tests for seed_demo_events()."""

    def test_seeds_all_events(self):
        mock_monitor = MagicMock()
        seed_demo_events(mock_monitor)
        assert mock_monitor.log_event.call_count == 8

    def test_passes_correct_params(self):
        mock_monitor = MagicMock()
        seed_demo_events(mock_monitor)
        first_call = mock_monitor.log_event.call_args_list[0]
        assert first_call.kwargs["event_type"] == "rule_query"
        assert first_call.kwargs["source"] == "claude-code"
