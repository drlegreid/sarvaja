"""
Unit tests for Session Collector Sync Mixin.

Per DOC-SIZE-01-v1: Tests for session_collector/sync.py module.
Tests: SessionSyncMixin methods (_generate_summary, _index_decision_to_typedb, _index_task_to_typedb).
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.session_collector.models import (
    SessionEvent, Task, Decision,
)
from governance.session_collector.sync import SessionSyncMixin
from governance.session_collector.capture import SessionCaptureMixin


class _TestSyncCollector(SessionSyncMixin, SessionCaptureMixin):
    """Concrete class for testing sync mixin."""

    def __init__(self, session_id="SESSION-2026-02-11-SYNC"):
        self.session_id = session_id
        self.topic = "Sync Test"
        self.session_type = "CHAT"
        self.start_time = datetime(2026, 2, 11, 10, 0, 0)
        self.events = []
        self.decisions = []
        self.tasks = []
        self.typedb_host = "localhost"
        self.typedb_port = 1729
        self.typedb_database = "governance"


class TestGenerateSummary:
    """Tests for _generate_summary()."""

    def test_basic(self):
        c = _TestSyncCollector()
        summary = c._generate_summary()
        assert "SESSION-2026-02-11-SYNC" in summary
        assert "Sync Test" in summary
        assert "CHAT" in summary

    def test_with_decisions(self):
        c = _TestSyncCollector()
        c.decisions = [Decision(id="D-1", name="Use TypeDB", context="c", rationale="r", status="active")]
        summary = c._generate_summary()
        assert "Use TypeDB" in summary

    def test_with_tasks(self):
        c = _TestSyncCollector()
        c.tasks = [Task(id="T-1", name="Fix bug", description="d", status="pending")]
        summary = c._generate_summary()
        assert "Fix bug" in summary

    def test_with_key_events(self):
        c = _TestSyncCollector()
        c.events = [
            SessionEvent(timestamp="t1", event_type="decision", content="Decided X"),
            SessionEvent(timestamp="t2", event_type="task", content="Created T-1"),
            SessionEvent(timestamp="t3", event_type="prompt", content="should not appear"),
        ]
        summary = c._generate_summary()
        assert "Decided X" in summary
        assert "Created T-1" in summary


class TestSyncToChromaDB:
    """Tests for sync_to_chromadb()."""

    def test_sync_returns_bool(self):
        c = _TestSyncCollector()
        result = c.sync_to_chromadb()
        assert isinstance(result, bool)

    @patch("governance.session_collector.sync.os.getenv", return_value="localhost")
    def test_sync_with_agent_id(self, mock_getenv):
        c = _TestSyncCollector()
        c.agent_id = "code-agent"
        result = c.sync_to_chromadb()
        assert isinstance(result, bool)


class TestIndexDecisionToTypeDB:
    """Tests for _index_decision_to_typedb()."""

    @patch("governance.session_collector.sync.TYPEDB_AVAILABLE", False)
    def test_returns_false_when_unavailable(self):
        c = _TestSyncCollector()
        d = Decision(id="D-1", name="n", context="c", rationale="r", status="active")
        assert c._index_decision_to_typedb(d) is False

    @patch("governance.session_collector.sync.TYPEDB_AVAILABLE", True)
    @patch("governance.client.TypeDBClient")
    def test_returns_false_on_connect_failure(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_client_class.return_value = mock_client
        c = _TestSyncCollector()
        d = Decision(id="D-1", name="n", context="c", rationale="r", status="active")
        result = c._index_decision_to_typedb(d)
        assert result is False


class TestIndexTaskToTypeDB:
    """Tests for _index_task_to_typedb()."""

    @patch("governance.session_collector.sync.TYPEDB_AVAILABLE", False)
    def test_returns_false_when_unavailable(self):
        c = _TestSyncCollector()
        t = Task(id="T-1", name="n", description="d", status="pending")
        assert c._index_task_to_typedb(t) is False

    @patch("governance.session_collector.sync.TYPEDB_AVAILABLE", True)
    @patch("governance.client.TypeDBClient")
    def test_returns_false_on_connect_failure(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_client_class.return_value = mock_client
        c = _TestSyncCollector()
        t = Task(id="T-1", name="n", description="d", status="pending")
        result = c._index_task_to_typedb(t)
        assert result is False
