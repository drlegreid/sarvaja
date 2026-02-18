"""
Tests for governance store helper functions.

Per RULE-032: Store conversion helpers for tasks, sessions, chat.
Covers synthesize_execution_events, extract_session_id, generate_chat_session_id.

Created: 2026-01-30
"""

import re
import pytest
from datetime import datetime

from governance.stores.helpers import (
    synthesize_execution_events,
    extract_session_id,
    generate_chat_session_id,
)


class TestSynthesizeExecutionEvents:
    """Test execution event synthesis from task data."""

    def test_dict_with_all_timestamps(self):
        data = {
            "created_at": "2026-01-30T10:00:00",
            "claimed_at": "2026-01-30T10:05:00",
            "completed_at": "2026-01-30T12:00:00",
            "agent_id": "A1",
            "status": "DONE",
            "evidence": "Tests pass"
        }
        events = synthesize_execution_events("T1", data)
        types = [e["event_type"] for e in events]
        assert "started" in types
        assert "claimed" in types
        assert "completed" in types
        assert "evidence" in types
        assert all(e["task_id"] == "T1" for e in events)

    def test_dict_minimal(self):
        data = {"status": "pending"}
        events = synthesize_execution_events("T1", data)
        assert events == []

    def test_dict_created_only(self):
        data = {"created_at": "2026-01-30T10:00:00", "status": "OPEN"}
        events = synthesize_execution_events("T1", data)
        assert len(events) == 1
        assert events[0]["event_type"] == "started"

    def test_dict_completed_status_triggers_event(self):
        data = {"status": "DONE"}
        events = synthesize_execution_events("T1", data)
        assert len(events) == 1
        assert events[0]["event_type"] == "completed"

    def test_dict_completed_alt_status(self):
        # BUG-227-HELPER-003: Only uppercase "DONE" triggers completed event
        data = {"status": "DONE"}
        events = synthesize_execution_events("T1", data)
        assert len(events) == 1
        assert events[0]["event_type"] == "completed"

    def test_dict_claimed_without_agent_skipped(self):
        data = {"claimed_at": "2026-01-30T10:00:00", "agent_id": None}
        events = synthesize_execution_events("T1", data)
        assert len(events) == 0

    def test_evidence_truncation(self):
        long_evidence = "x" * 200
        data = {"evidence": long_evidence, "status": "pending"}
        events = synthesize_execution_events("T1", data)
        assert len(events) == 1
        assert events[0]["event_type"] == "evidence"
        assert events[0]["message"].endswith("...")
        assert len(events[0]["message"]) == 103  # 100 chars + "..."

    def test_short_evidence_no_truncation(self):
        data = {"evidence": "Tests pass", "status": "pending"}
        events = synthesize_execution_events("T1", data)
        assert events[0]["message"] == "Tests pass"

    def test_event_ids_unique(self):
        data = {
            "created_at": "2026-01-30T10:00:00",
            "claimed_at": "2026-01-30T10:05:00",
            "agent_id": "A1",
            "status": "pending",
        }
        events = synthesize_execution_events("T1", data)
        ids = [e["event_id"] for e in events]
        assert len(ids) == len(set(ids))  # All unique

    def test_event_id_format(self):
        data = {"created_at": "2026-01-30T10:00:00"}
        events = synthesize_execution_events("T1", data)
        assert events[0]["event_id"].startswith("EVT-")

    def test_object_with_attributes(self):
        """Test with object-like data that has attributes."""
        class MockTask:
            created_at = datetime(2026, 1, 30, 10, 0)
            claimed_at = datetime(2026, 1, 30, 10, 5)
            completed_at = None
            agent_id = "A1"
            status = "IN_PROGRESS"
            evidence = None

        events = synthesize_execution_events("T1", MockTask())
        assert len(events) == 2  # started + claimed
        assert events[0]["event_type"] == "started"
        assert events[1]["event_type"] == "claimed"


class TestExtractSessionId:
    """Test session ID extraction from filenames."""

    def test_valid_session_id(self):
        assert extract_session_id("SESSION-2026-01-30-001.md") == "SESSION-2026-01-30-001"

    def test_valid_with_suffix(self):
        assert extract_session_id("SESSION-2026-01-30-042.md") == "SESSION-2026-01-30-042"

    def test_no_match(self):
        assert extract_session_id("random-file.md") is None

    def test_partial_match(self):
        assert extract_session_id("SESSION-2026-01.md") is None

    def test_just_session_prefix(self):
        assert extract_session_id("SESSION-abc") is None


class TestGenerateChatSessionId:
    """Test chat session ID generation."""

    def test_format(self):
        sid = generate_chat_session_id()
        assert sid.startswith("CHAT-")
        assert len(sid) == 13  # CHAT- + 8 hex chars

    def test_uniqueness(self):
        ids = {generate_chat_session_id() for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_uppercase(self):
        sid = generate_chat_session_id()
        assert sid == sid.upper()
