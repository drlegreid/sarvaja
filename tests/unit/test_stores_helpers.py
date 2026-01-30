"""
Tests for governance stores helper functions.

Per RULE-032: Tests for modularized stores module.
Covers trust score calculation, session ID extraction, chat ID generation,
and execution event synthesis.

Created: 2026-01-30
"""

import re
import pytest

from governance.stores.agents import (
    _calculate_trust_score,
    _AGENT_BASE_CONFIG,
)
from governance.stores.helpers import (
    extract_session_id,
    generate_chat_session_id,
    synthesize_execution_events,
)


class TestCalculateTrustScore:
    """Test trust score calculation formula."""

    def test_zero_tasks_returns_base(self):
        """New agent (0 tasks) gets base trust score."""
        assert _calculate_trust_score("agent-1", 0, 0.85) == 0.85

    def test_one_task_slightly_higher(self):
        """One task yields slightly higher than base."""
        score = _calculate_trust_score("agent-1", 1, 0.85)
        assert score > 0.85
        assert score < 0.90

    def test_many_tasks_higher(self):
        """Many tasks yields significantly higher score."""
        score_10 = _calculate_trust_score("agent-1", 10, 0.85)
        score_100 = _calculate_trust_score("agent-1", 100, 0.85)
        assert score_100 > score_10

    def test_logarithmic_growth(self):
        """Growth is logarithmic - diminishing returns."""
        score_100 = _calculate_trust_score("agent-1", 100, 0.85)
        score_1000 = _calculate_trust_score("agent-1", 1000, 0.85)
        # Gap between 100->1000 should be smaller than 0->100
        gap_100_1000 = score_1000 - score_100
        gap_0_100 = score_100 - 0.85
        assert gap_100_1000 < gap_0_100

    def test_never_exceeds_one(self):
        """Trust score never exceeds 1.0."""
        score = _calculate_trust_score("agent-1", 1_000_000, 0.99)
        assert score <= 1.0

    def test_different_base_trust(self):
        """Different base trust values produce different results."""
        low = _calculate_trust_score("agent-1", 10, 0.50)
        high = _calculate_trust_score("agent-1", 10, 0.95)
        assert high > low

    def test_all_base_agents_have_config(self):
        """All base agents have name, type, base_trust, capabilities."""
        for agent_id, config in _AGENT_BASE_CONFIG.items():
            assert "name" in config
            assert "agent_type" in config
            assert "base_trust" in config
            assert 0.0 < config["base_trust"] <= 1.0
            assert "capabilities" in config
            assert isinstance(config["capabilities"], list)


class TestExtractSessionId:
    """Test session ID extraction from filenames."""

    def test_valid_session_filename(self):
        """Extract ID from standard session filename."""
        assert extract_session_id("SESSION-2026-01-30-001.md") == "SESSION-2026-01-30-001"

    def test_session_without_extension(self):
        """Extract ID even without .md extension."""
        assert extract_session_id("SESSION-2026-01-30-042") == "SESSION-2026-01-30-042"

    def test_no_match(self):
        """Return None for non-session filenames."""
        assert extract_session_id("README.md") is None

    def test_dsm_file_no_match(self):
        """DSM files don't match session pattern."""
        assert extract_session_id("DSM-2026-01-25-015206.md") is None

    def test_partial_match(self):
        """Don't match partial session patterns."""
        assert extract_session_id("SESSION-2026-01.md") is None


class TestGenerateChatSessionId:
    """Test chat session ID generation."""

    def test_format(self):
        """Chat ID follows CHAT-XXXXXXXX format."""
        chat_id = generate_chat_session_id()
        assert chat_id.startswith("CHAT-")
        assert len(chat_id) == 13  # CHAT- + 8 hex chars

    def test_uppercase_hex(self):
        """Chat ID hex portion is uppercase."""
        chat_id = generate_chat_session_id()
        hex_part = chat_id[5:]
        assert hex_part == hex_part.upper()

    def test_uniqueness(self):
        """Generated IDs are unique."""
        ids = {generate_chat_session_id() for _ in range(100)}
        assert len(ids) == 100


class TestSynthesizeExecutionEvents:
    """Test execution event synthesis from task data."""

    def test_empty_task_no_events(self):
        """Task with no timestamps produces no events."""
        events = synthesize_execution_events("T-001", {
            "status": "pending",
        })
        assert len(events) == 0

    def test_created_event(self):
        """Task with created_at produces started event."""
        events = synthesize_execution_events("T-001", {
            "created_at": "2026-01-30T10:00:00",
            "status": "pending",
        })
        assert len(events) == 1
        assert events[0]["event_type"] == "started"
        assert events[0]["task_id"] == "T-001"

    def test_claimed_event(self):
        """Task with claimed_at and agent_id produces claimed event."""
        events = synthesize_execution_events("T-001", {
            "claimed_at": "2026-01-30T10:05:00",
            "agent_id": "rules-curator",
            "status": "IN_PROGRESS",
        })
        assert any(e["event_type"] == "claimed" for e in events)
        claimed = [e for e in events if e["event_type"] == "claimed"][0]
        assert claimed["agent_id"] == "rules-curator"

    def test_completed_event(self):
        """Task with completed_at produces completed event."""
        events = synthesize_execution_events("T-001", {
            "completed_at": "2026-01-30T12:00:00",
            "status": "DONE",
        })
        assert any(e["event_type"] == "completed" for e in events)

    def test_done_status_triggers_completed(self):
        """Status DONE triggers completed event even without completed_at."""
        events = synthesize_execution_events("T-001", {
            "status": "DONE",
        })
        assert any(e["event_type"] == "completed" for e in events)

    def test_evidence_event(self):
        """Task with evidence produces evidence event."""
        events = synthesize_execution_events("T-001", {
            "evidence": "[Verification: L2] Tests pass with 95% coverage",
            "status": "completed",
        })
        assert any(e["event_type"] == "evidence" for e in events)
        ev = [e for e in events if e["event_type"] == "evidence"][0]
        assert "full_evidence" in ev["details"]

    def test_evidence_truncated(self):
        """Long evidence is truncated in message."""
        long_evidence = "A" * 200
        events = synthesize_execution_events("T-001", {
            "evidence": long_evidence,
            "status": "completed",
        })
        ev = [e for e in events if e["event_type"] == "evidence"][0]
        assert ev["message"].endswith("...")
        assert len(ev["message"]) <= 103  # 100 chars + "..."

    def test_full_lifecycle(self):
        """Full task lifecycle produces all events."""
        events = synthesize_execution_events("T-001", {
            "created_at": "2026-01-30T10:00:00",
            "claimed_at": "2026-01-30T10:05:00",
            "completed_at": "2026-01-30T12:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": "All tests pass",
        })
        types = [e["event_type"] for e in events]
        assert "started" in types
        assert "claimed" in types
        assert "completed" in types
        assert "evidence" in types

    def test_event_ids_unique(self):
        """Each event has a unique EVT-XXXXXXXX ID."""
        events = synthesize_execution_events("T-001", {
            "created_at": "2026-01-30T10:00:00",
            "claimed_at": "2026-01-30T10:05:00",
            "completed_at": "2026-01-30T12:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
        })
        ids = [e["event_id"] for e in events]
        assert len(ids) == len(set(ids))
        for eid in ids:
            assert eid.startswith("EVT-")
