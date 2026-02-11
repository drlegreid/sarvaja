"""
Unit tests for Session Rendering and Serialization.

Per SESSION-EVID-01-v1: Tests for SessionRenderMixin markdown generation,
to_dict, and to_json methods.
"""

import json
import pytest
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from governance.session_collector.models import (
    SessionEvent, Task, Decision, SessionIntent, SessionOutcome,
)
from governance.session_collector.render import SessionRenderMixin


class _FakeCollector(SessionRenderMixin):
    """Fake collector with required attributes for the mixin."""

    def __init__(self, **kwargs):
        self.session_id = kwargs.get("session_id", "SESSION-2026-02-11-TEST")
        self.topic = kwargs.get("topic", "Test Session")
        self.session_type = kwargs.get("session_type", "DEVELOPMENT")
        self.start_time = kwargs.get("start_time", datetime(2026, 2, 11, 9, 0, 0))
        self.end_time = kwargs.get("end_time", datetime(2026, 2, 11, 13, 0, 0))
        self.events: List[SessionEvent] = kwargs.get("events", [])
        self.decisions: List[Decision] = kwargs.get("decisions", [])
        self.tasks: List[Task] = kwargs.get("tasks", [])
        self.intent: Optional[SessionIntent] = kwargs.get("intent", None)
        self.outcome: Optional[SessionOutcome] = kwargs.get("outcome", None)
        self.evidence_dir = kwargs.get("evidence_dir", Path("/tmp/test-evidence"))


# ---------------------------------------------------------------------------
# _render_session_markdown
# ---------------------------------------------------------------------------
class TestRenderSessionMarkdown:
    """Tests for _render_session_markdown method."""

    def test_minimal(self):
        c = _FakeCollector()
        md = c._render_session_markdown()
        assert "# Session Evidence Log: Test Session" in md
        assert "SESSION-2026-02-11-TEST" in md
        assert "DEVELOPMENT" in md
        assert "SESSION-EVID-01-v1" in md

    def test_with_intent(self):
        intent = SessionIntent(
            goal="Fix auth", source="TODO.md",
            planned_tasks=["T-1", "T-2"],
            previous_session_id="SESSION-2026-02-10-PREV",
            initial_prompt="Please fix the auth bug",
        )
        c = _FakeCollector(intent=intent)
        md = c._render_session_markdown()
        assert "## Session Intent" in md
        assert "Fix auth" in md
        assert "TODO.md" in md
        assert "T-1" in md
        assert "SESSION-2026-02-10-PREV" in md
        assert "Please fix the auth bug" in md

    def test_with_outcome(self):
        outcome = SessionOutcome(
            status="COMPLETE",
            achieved_tasks=["T-1"],
            deferred_tasks=["T-2"],
            handoff_items=["Review PR"],
            discoveries=["GAP-NEW-001"],
        )
        c = _FakeCollector(outcome=outcome)
        md = c._render_session_markdown()
        assert "## Session Outcome" in md
        assert "COMPLETE" in md
        assert "[x] T-1" in md
        assert "[ ] T-2" in md
        assert "Review PR" in md
        assert "GAP-NEW-001" in md

    def test_with_decisions(self):
        decisions = [
            Decision(id="D-1", name="Use TypeDB", context="DB choice",
                     rationale="Better for inference", status="APPROVED"),
        ]
        c = _FakeCollector(decisions=decisions)
        md = c._render_session_markdown()
        assert "## Decisions" in md
        assert "D-1" in md
        assert "Use TypeDB" in md
        assert "APPROVED" in md
        assert "Better for inference" in md

    def test_with_tasks(self):
        tasks = [
            Task(id="T-1", name="Fix bug", description="Fix it",
                 status="completed", priority="HIGH"),
        ]
        c = _FakeCollector(tasks=tasks)
        md = c._render_session_markdown()
        assert "## Tasks" in md
        assert "T-1" in md
        assert "Fix bug" in md
        assert "completed" in md
        assert "HIGH" in md

    def test_with_thought_events(self):
        events = [
            SessionEvent(
                timestamp="2026-02-11T10:00:00",
                event_type="thought",
                content="I should check the auth module first",
                metadata={"thought_type": "analysis", "confidence": 0.9,
                          "related_tools": ["read_file", "grep"]},
            ),
        ]
        c = _FakeCollector(events=events)
        md = c._render_session_markdown()
        assert "## Key Thoughts" in md
        assert "Analysis" in md  # title-cased
        assert "auth module" in md
        assert "90.0%" in md
        assert "read_file" in md

    def test_with_tool_events(self):
        events = [
            SessionEvent(
                timestamp="2026-02-11T10:00:00",
                event_type="tool_call",
                content="health_check",
                metadata={"tool_name": "health_check", "success": True, "duration_ms": 50},
            ),
        ]
        c = _FakeCollector(events=events)
        md = c._render_session_markdown()
        assert "## Tool Calls" in md
        assert "health_check" in md
        assert "50ms" in md

    def test_event_timeline(self):
        events = [
            SessionEvent("2026-02-11T10:00:00", "prompt", "User input here"),
            SessionEvent("2026-02-11T10:01:00", "response", "Bot response"),
        ]
        c = _FakeCollector(events=events)
        md = c._render_session_markdown()
        assert "## Event Timeline" in md
        assert "PROMPT" in md
        assert "RESPONSE" in md


# ---------------------------------------------------------------------------
# to_dict / to_json
# ---------------------------------------------------------------------------
class TestToDict:
    """Tests for to_dict method."""

    def test_basic(self):
        c = _FakeCollector()
        d = c.to_dict()
        assert d["session_id"] == "SESSION-2026-02-11-TEST"
        assert d["topic"] == "Test Session"
        assert d["session_type"] == "DEVELOPMENT"
        assert d["events_count"] == 0
        assert d["decisions_count"] == 0
        assert d["tasks_count"] == 0

    def test_with_intent(self):
        intent = SessionIntent(goal="Fix auth", source="test")
        c = _FakeCollector(intent=intent)
        d = c.to_dict()
        assert "intent" in d
        assert d["intent"]["goal"] == "Fix auth"

    def test_with_outcome(self):
        outcome = SessionOutcome(status="COMPLETE")
        c = _FakeCollector(outcome=outcome)
        d = c.to_dict()
        assert "outcome" in d
        assert d["outcome"]["status"] == "COMPLETE"

    def test_without_intent_outcome(self):
        c = _FakeCollector()
        d = c.to_dict()
        assert "intent" not in d
        assert "outcome" not in d

    def test_end_time_none(self):
        c = _FakeCollector(end_time=None)
        d = c.to_dict()
        assert d["end_time"] is None


class TestToJson:
    """Tests for to_json method."""

    def test_valid_json(self):
        c = _FakeCollector()
        j = c.to_json()
        parsed = json.loads(j)
        assert parsed["session_id"] == "SESSION-2026-02-11-TEST"

    def test_with_decisions(self):
        decisions = [
            Decision(id="D-1", name="Test", context="ctx",
                     rationale="why", status="APPROVED"),
        ]
        c = _FakeCollector(decisions=decisions)
        j = c.to_json()
        parsed = json.loads(j)
        assert len(parsed["decisions"]) == 1
        assert parsed["decisions"][0]["id"] == "D-1"


# ---------------------------------------------------------------------------
# generate_session_log
# ---------------------------------------------------------------------------
class TestGenerateSessionLog:
    """Tests for generate_session_log method."""

    def test_generates_file(self, tmp_path):
        c = _FakeCollector(evidence_dir=tmp_path)
        path = c.generate_session_log()
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "# Session Evidence Log" in content

    def test_custom_output_dir(self, tmp_path):
        custom_dir = tmp_path / "custom"
        c = _FakeCollector()
        path = c.generate_session_log(output_dir=custom_dir)
        assert custom_dir.exists()
        assert Path(path).exists()

    def test_filename_matches_session_id(self, tmp_path):
        c = _FakeCollector(
            session_id="SESSION-2026-02-11-MYTEST",
            evidence_dir=tmp_path,
        )
        path = c.generate_session_log()
        assert "SESSION-2026-02-11-MYTEST.md" in path
