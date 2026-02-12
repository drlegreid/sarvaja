"""
Unit tests for Event Log Middleware.

Per DOC-SIZE-01-v1: Tests for governance/middleware/event_log.py.
Tests: log_event — structured output, entity/action, details.
"""

import json
from unittest.mock import patch

from governance.middleware.event_log import log_event


class TestLogEvent:
    @patch("governance.middleware.event_log.logger")
    def test_basic_event(self, mock_logger):
        log_event("session", "create")

        mock_logger.info.assert_called_once()
        logged = json.loads(mock_logger.info.call_args[0][0])
        assert logged["entity"] == "session"
        assert logged["action"] == "create"
        assert "ts" in logged

    @patch("governance.middleware.event_log.logger")
    def test_with_details(self, mock_logger):
        log_event("task", "update", task_id="T-1", status="IN_PROGRESS")

        logged = json.loads(mock_logger.info.call_args[0][0])
        assert logged["entity"] == "task"
        assert logged["action"] == "update"
        assert logged["task_id"] == "T-1"
        assert logged["status"] == "IN_PROGRESS"

    @patch("governance.middleware.event_log.logger")
    def test_multiple_details(self, mock_logger):
        log_event("agent", "trust_update", agent_id="A-1",
                  trust_score=0.85, reason="passed checks")

        logged = json.loads(mock_logger.info.call_args[0][0])
        assert logged["agent_id"] == "A-1"
        assert logged["trust_score"] == 0.85
        assert logged["reason"] == "passed checks"

    @patch("governance.middleware.event_log.logger")
    def test_timestamp_format(self, mock_logger):
        log_event("rule", "delete")

        logged = json.loads(mock_logger.info.call_args[0][0])
        # Format: YYYY-MM-DDTHH:MM:SS
        assert len(logged["ts"]) == 19
        assert "T" in logged["ts"]
