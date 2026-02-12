"""
Unit tests for Dashboard Action Logging.

Per DOC-SIZE-01-v1: Tests for middleware/dashboard_log.py module.
Tests: log_action() structured logging.
"""

import json
import logging
import pytest

from governance.middleware.dashboard_log import log_action


@pytest.fixture
def captured_logs(caplog):
    """Capture governance.dashboard log messages."""
    with caplog.at_level(logging.INFO, logger="governance.dashboard"):
        yield caplog


class TestLogAction:
    """Tests for log_action()."""

    def test_basic_log(self, captured_logs):
        log_action("sessions", "select")
        assert len(captured_logs.records) == 1
        entry = json.loads(captured_logs.records[0].message)
        assert entry["view"] == "sessions"
        assert entry["action"] == "select"

    def test_has_timestamp(self, captured_logs):
        log_action("tasks", "create")
        entry = json.loads(captured_logs.records[0].message)
        assert "ts" in entry
        # Format: YYYY-MM-DDTHH:MM:SS
        assert len(entry["ts"]) == 19

    def test_with_details(self, captured_logs):
        log_action("rules", "delete", rule_id="RULE-001", reason="deprecated")
        entry = json.loads(captured_logs.records[0].message)
        assert entry["rule_id"] == "RULE-001"
        assert entry["reason"] == "deprecated"

    def test_compact_json(self, captured_logs):
        log_action("agents", "filter")
        msg = captured_logs.records[0].message
        # Uses compact separators (",", ":")
        assert ": " not in msg or msg.count(": ") == 0
        assert ", " not in msg

    def test_multiple_details(self, captured_logs):
        log_action("sessions", "page", page=2, size=50, sort="desc")
        entry = json.loads(captured_logs.records[0].message)
        assert entry["page"] == 2
        assert entry["size"] == 50
        assert entry["sort"] == "desc"

    def test_valid_json_output(self, captured_logs):
        log_action("tasks", "update", task_id="T-123")
        msg = captured_logs.records[0].message
        parsed = json.loads(msg)
        assert isinstance(parsed, dict)

    def test_different_views(self, captured_logs):
        for view in ["sessions", "tasks", "rules", "agents"]:
            log_action(view, "select")
        assert len(captured_logs.records) == 4
        views = {json.loads(r.message)["view"] for r in captured_logs.records}
        assert views == {"sessions", "tasks", "rules", "agents"}
