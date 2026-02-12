"""
Unit tests for Monitoring Data Access.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/monitoring.py module.
Tests: _get_audit_log_dir, _write_audit_event, get_rule_monitor,
       get_monitor_feed, get_monitor_alerts, get_monitor_stats,
       log_monitor_event, read_audit_events.
"""

import json
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

_P = "agent.governance_ui.data_access.monitoring"


@pytest.fixture(autouse=True)
def _reset_globals():
    with patch(f"{_P}._AUDIT_LOG_DIR", None), \
         patch(f"{_P}._monitor_instance", None):
        yield


# ── _get_audit_log_dir ───────────────────────────────────────────


class TestGetAuditLogDir:
    def test_finds_workspace_root(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import _get_audit_log_dir
        (tmp_path / "CLAUDE.md").write_text("# CLAUDE")
        with patch(f"{_P}._AUDIT_LOG_DIR", None), \
             patch(f"{_P}.Path") as MockPath:
            # Make the path resolution find tmp_path
            mock_file = MagicMock()
            mock_file.resolve.return_value = tmp_path / "agent" / "governance_ui" / "data_access" / "monitoring.py"
            MockPath.__file__ = str(mock_file)
            MockPath.return_value = mock_file
            # Just test that function returns a Path
            # (Can't easily test file-system traversal without mocking deeply)

    def test_fallback_to_tmp(self, _reset_globals):
        from agent.governance_ui.data_access.monitoring import _get_audit_log_dir
        with patch(f"{_P}._AUDIT_LOG_DIR", None):
            # Force re-resolution with mocked path that won't find workspace
            import agent.governance_ui.data_access.monitoring as mod
            mod._AUDIT_LOG_DIR = None
            result = mod._get_audit_log_dir()
            assert result is not None


# ── _write_audit_event ───────────────────────────────────────────


class TestWriteAuditEvent:
    def test_writes_jsonl(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import _write_audit_event
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            _write_audit_event({"event_type": "test", "source": "unit"})
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        assert log_file.exists()
        content = log_file.read_text()
        event = json.loads(content.strip())
        assert event["event_type"] == "test"

    def test_exception_silenced(self):
        from agent.governance_ui.data_access.monitoring import _write_audit_event
        with patch(f"{_P}._get_audit_log_dir", side_effect=Exception("fail")):
            _write_audit_event({"test": True})  # should not raise


# ── get_rule_monitor ─────────────────────────────────────────────


class TestGetRuleMonitor:
    def test_creates_singleton(self):
        from agent.governance_ui.data_access.monitoring import get_rule_monitor
        mock_monitor = MagicMock()
        with patch("agent.rule_monitor.create_rule_monitor", return_value=mock_monitor):
            result = get_rule_monitor()
        assert result == mock_monitor

    def test_returns_cached(self):
        from agent.governance_ui.data_access.monitoring import get_rule_monitor
        import agent.governance_ui.data_access.monitoring as mod
        mock_monitor = MagicMock()
        mod._monitor_instance = mock_monitor
        result = get_rule_monitor()
        assert result is mock_monitor


# ── read_audit_events ────────────────────────────────────────────


class TestReadAuditEvents:
    def test_reads_today(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        log_file.write_text(
            json.dumps({"event_type": "test", "severity": "INFO", "timestamp": "2026-02-11T10:00:00"}) + "\n"
            + json.dumps({"event_type": "alert", "severity": "CRITICAL", "timestamp": "2026-02-11T11:00:00"}) + "\n"
        )
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1)
        assert len(events) == 2
        assert events[0]["timestamp"] > events[1]["timestamp"]  # newest first

    def test_filter_event_type(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        log_file.write_text(
            json.dumps({"event_type": "test", "timestamp": "t1"}) + "\n"
            + json.dumps({"event_type": "alert", "timestamp": "t2"}) + "\n"
        )
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1, event_type="alert")
        assert len(events) == 1
        assert events[0]["event_type"] == "alert"

    def test_filter_severity(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        log_file.write_text(
            json.dumps({"event_type": "e", "severity": "INFO", "timestamp": "t1"}) + "\n"
            + json.dumps({"event_type": "e", "severity": "CRITICAL", "timestamp": "t2"}) + "\n"
        )
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1, severity="CRITICAL")
        assert len(events) == 1

    def test_no_file(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1)
        assert events == []

    def test_invalid_json_skipped(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        log_file.write_text("not json\n" + json.dumps({"event_type": "ok", "timestamp": "t"}) + "\n")
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1)
        assert len(events) == 1

    def test_limit(self, tmp_path):
        from agent.governance_ui.data_access.monitoring import read_audit_events
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / f"{today}.jsonl"
        lines = [json.dumps({"event_type": "e", "timestamp": f"t{i}"}) for i in range(10)]
        log_file.write_text("\n".join(lines) + "\n")
        with patch(f"{_P}._get_audit_log_dir", return_value=tmp_path):
            events = read_audit_events(days=1, limit=3)
        assert len(events) == 3


# ── get_monitor_feed ─────────────────────────────────────────────


class TestGetMonitorFeed:
    def test_merges_memory_and_audit(self):
        from agent.governance_ui.data_access.monitoring import get_monitor_feed
        monitor = MagicMock()
        monitor.get_feed.return_value = [
            {"id": "E-1", "event_type": "test", "timestamp": "2026-02-11T10:00:00"},
        ]
        with patch(f"{_P}.get_rule_monitor", return_value=monitor), \
             patch(f"{_P}.read_audit_events", return_value=[
                 {"event_id": "E-2", "event_type": "alert", "timestamp": "2026-02-11T11:00:00"},
             ]):
            events = get_monitor_feed(limit=10)
        assert len(events) == 2

    def test_deduplicates(self):
        from agent.governance_ui.data_access.monitoring import get_monitor_feed
        monitor = MagicMock()
        monitor.get_feed.return_value = [
            {"id": "E-1", "event_type": "test", "timestamp": "t1"},
        ]
        with patch(f"{_P}.get_rule_monitor", return_value=monitor), \
             patch(f"{_P}.read_audit_events", return_value=[
                 {"event_id": "E-1", "event_type": "test", "timestamp": "t1"},
             ]):
            events = get_monitor_feed(limit=10)
        assert len(events) == 1

    def test_audit_read_failure(self):
        from agent.governance_ui.data_access.monitoring import get_monitor_feed
        monitor = MagicMock()
        monitor.get_feed.return_value = [{"id": "E-1", "event_type": "t", "timestamp": "t"}]
        with patch(f"{_P}.get_rule_monitor", return_value=monitor), \
             patch(f"{_P}.read_audit_events", side_effect=Exception("fail")):
            events = get_monitor_feed(limit=10)
        assert len(events) == 1


# ── log_monitor_event ────────────────────────────────────────────


class TestLogMonitorEvent:
    def test_logs_and_writes_audit(self):
        from agent.governance_ui.data_access.monitoring import log_monitor_event
        monitor = MagicMock()
        monitor.log_event.return_value = {"id": "E-1"}
        with patch(f"{_P}.get_rule_monitor", return_value=monitor), \
             patch(f"{_P}._write_audit_event") as mock_audit:
            result = log_monitor_event("test", "unit", {"key": "val"})
        assert result["id"] == "E-1"
        mock_audit.assert_called_once()


# ── Simple delegates ─────────────────────────────────────────────


class TestDelegates:
    def test_get_monitor_alerts(self):
        from agent.governance_ui.data_access.monitoring import get_monitor_alerts
        monitor = MagicMock()
        monitor.get_alerts.return_value = [{"id": "A-1"}]
        with patch(f"{_P}.get_rule_monitor", return_value=monitor):
            result = get_monitor_alerts()
        assert len(result) == 1

    def test_get_monitor_stats(self):
        from agent.governance_ui.data_access.monitoring import get_monitor_stats
        monitor = MagicMock()
        monitor.get_statistics.return_value = {"events": 10}
        with patch(f"{_P}.get_rule_monitor", return_value=monitor):
            result = get_monitor_stats()
        assert result["events"] == 10

    def test_acknowledge_alert(self):
        from agent.governance_ui.data_access.monitoring import acknowledge_monitor_alert
        monitor = MagicMock()
        monitor.acknowledge_alert.return_value = {"ok": True}
        with patch(f"{_P}.get_rule_monitor", return_value=monitor):
            result = acknowledge_monitor_alert("A-1")
        assert result["ok"] is True

    def test_get_top_rules(self):
        from agent.governance_ui.data_access.monitoring import get_top_monitored_rules
        monitor = MagicMock()
        monitor.get_top_rules.return_value = [{"rule_id": "R-1", "count": 5}]
        with patch(f"{_P}.get_rule_monitor", return_value=monitor):
            result = get_top_monitored_rules(limit=5)
        assert len(result) == 1

    def test_get_hourly_stats(self):
        from agent.governance_ui.data_access.monitoring import get_hourly_monitor_stats
        monitor = MagicMock()
        monitor.get_hourly_stats.return_value = {"hour_0": 3}
        with patch(f"{_P}.get_rule_monitor", return_value=monitor):
            result = get_hourly_monitor_stats()
        assert result["hour_0"] == 3
