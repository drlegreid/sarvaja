"""
Unit tests for Governance Stores Helpers.

Per DOC-SIZE-01-v1: Tests for stores/helpers.py module.
Tests: synthesize_execution_events, extract_session_id, generate_chat_session_id.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from governance.stores.helpers import (
    synthesize_execution_events,
    extract_session_id,
    generate_chat_session_id,
)


class TestSynthesizeExecutionEvents:
    """Tests for synthesize_execution_events()."""

    def test_empty_dict(self):
        events = synthesize_execution_events("T-1", {})
        assert events == []

    def test_created_at(self):
        data = {"created_at": "2026-02-11T10:00:00"}
        events = synthesize_execution_events("T-1", data)
        assert len(events) == 1
        assert events[0]["event_type"] == "started"
        assert events[0]["task_id"] == "T-1"

    def test_claimed_at(self):
        data = {"claimed_at": "2026-02-11T10:05:00", "agent_id": "code-agent"}
        events = synthesize_execution_events("T-1", data)
        assert any(e["event_type"] == "claimed" for e in events)
        claimed = [e for e in events if e["event_type"] == "claimed"][0]
        assert claimed["agent_id"] == "code-agent"

    def test_claimed_without_agent_skipped(self):
        data = {"claimed_at": "2026-02-11T10:05:00"}
        events = synthesize_execution_events("T-1", data)
        assert not any(e["event_type"] == "claimed" for e in events)

    def test_completed_at(self):
        data = {"completed_at": "2026-02-11T11:00:00"}
        events = synthesize_execution_events("T-1", data)
        assert any(e["event_type"] == "completed" for e in events)

    def test_done_status_creates_completed(self):
        data = {"status": "DONE"}
        events = synthesize_execution_events("T-1", data)
        assert any(e["event_type"] == "completed" for e in events)

    def test_evidence_creates_event(self):
        data = {"evidence": "Tests pass with 100% coverage", "completed_at": "2026-02-11T11:00:00"}
        events = synthesize_execution_events("T-1", data)
        assert any(e["event_type"] == "evidence" for e in events)

    def test_evidence_truncated(self):
        long_evidence = "x" * 200
        data = {"evidence": long_evidence}
        events = synthesize_execution_events("T-1", data)
        evidence_events = [e for e in events if e["event_type"] == "evidence"]
        if evidence_events:
            assert len(evidence_events[0]["message"]) <= 103  # 100 + "..."

    def test_full_lifecycle(self):
        data = {
            "created_at": "2026-02-11T10:00:00",
            "claimed_at": "2026-02-11T10:05:00",
            "completed_at": "2026-02-11T11:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": "All tests pass",
        }
        events = synthesize_execution_events("T-1", data)
        types = [e["event_type"] for e in events]
        assert "started" in types
        assert "claimed" in types
        assert "completed" in types
        assert "evidence" in types

    def test_with_typedb_task_object(self):
        mock_task = MagicMock()
        mock_task.created_at = datetime(2026, 2, 11, 10, 0, 0)
        mock_task.claimed_at = datetime(2026, 2, 11, 10, 5, 0)
        mock_task.completed_at = None
        mock_task.agent_id = "code-agent"
        mock_task.status = "IN_PROGRESS"
        mock_task.evidence = None
        events = synthesize_execution_events("T-1", mock_task)
        assert any(e["event_type"] == "started" for e in events)
        assert any(e["event_type"] == "claimed" for e in events)

    def test_event_ids_unique(self):
        data = {"created_at": "t1", "claimed_at": "t2", "agent_id": "a"}
        events = synthesize_execution_events("T-1", data)
        ids = [e["event_id"] for e in events]
        assert len(ids) == len(set(ids))


class TestExtractSessionId:
    """Tests for extract_session_id()."""

    def test_valid_pattern(self):
        assert extract_session_id("SESSION-2026-02-11-001.md") == "SESSION-2026-02-11-001"

    def test_invalid_pattern(self):
        assert extract_session_id("random-file.md") is None

    def test_no_extension(self):
        result = extract_session_id("SESSION-2026-02-11-001")
        assert result == "SESSION-2026-02-11-001"


class TestGenerateChatSessionId:
    """Tests for generate_chat_session_id()."""

    def test_format(self):
        sid = generate_chat_session_id()
        assert sid.startswith("CHAT-")
        assert len(sid) == 13  # CHAT- + 8 hex chars

    def test_unique(self):
        ids = {generate_chat_session_id() for _ in range(10)}
        assert len(ids) == 10
