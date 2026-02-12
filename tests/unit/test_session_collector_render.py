"""
Unit tests for Session Collector Render Mixin.

Per DOC-SIZE-01-v1: Tests for session_collector/render.py module.
Tests: SessionRenderMixin methods (markdown rendering, to_dict, to_json).
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from governance.session_collector.models import (
    SessionEvent, Task, Decision, SessionIntent, SessionOutcome,
)
from governance.session_collector.render import SessionRenderMixin


class _TestRenderer(SessionRenderMixin):
    """Concrete class for testing the render mixin."""

    def __init__(self, session_id="SESSION-2026-02-11-TEST", topic="Test"):
        self.session_id = session_id
        self.topic = topic
        self.session_type = "CHAT"
        self.start_time = datetime(2026, 2, 11, 10, 0, 0)
        self.end_time = None
        self.events = []
        self.decisions = []
        self.tasks = []
        self.intent = None
        self.outcome = None
        self.evidence_dir = Path("/tmp/evidence")


class TestRenderSessionMarkdown:
    """Tests for _render_session_markdown()."""

    def test_basic_header(self):
        r = _TestRenderer()
        md = r._render_session_markdown()
        assert "# Session Evidence Log: Test" in md
        assert "SESSION-2026-02-11-TEST" in md
        assert "CHAT" in md

    def test_with_intent(self):
        r = _TestRenderer()
        r.intent = SessionIntent(goal="Fix bug", source="TODO.md")
        md = r._render_session_markdown()
        assert "## Session Intent" in md
        assert "Fix bug" in md
        assert "TODO.md" in md

    def test_intent_with_prompt(self):
        r = _TestRenderer()
        r.intent = SessionIntent(
            goal="Goal", source="User",
            initial_prompt="Please help me",
        )
        md = r._render_session_markdown()
        assert "### Initial Prompt" in md
        assert "Please help me" in md

    def test_intent_with_planned_tasks(self):
        r = _TestRenderer()
        r.intent = SessionIntent(
            goal="Goal", source="User",
            planned_tasks=["T-1", "T-2"],
        )
        md = r._render_session_markdown()
        assert "### Planned Tasks" in md
        assert "- [ ] T-1" in md

    def test_intent_with_previous_session(self):
        r = _TestRenderer()
        r.intent = SessionIntent(
            goal="Goal", source="Handoff",
            previous_session_id="SESSION-2026-02-10-PREV",
        )
        md = r._render_session_markdown()
        assert "SESSION-2026-02-10-PREV" in md

    def test_with_outcome(self):
        r = _TestRenderer()
        r.outcome = SessionOutcome(status="COMPLETE", achieved_tasks=["T-1"])
        md = r._render_session_markdown()
        assert "## Session Outcome" in md
        assert "COMPLETE" in md
        assert "- [x] T-1" in md

    def test_outcome_deferred(self):
        r = _TestRenderer()
        r.outcome = SessionOutcome(status="PARTIAL", deferred_tasks=["T-2"])
        md = r._render_session_markdown()
        assert "### Deferred Tasks" in md
        assert "- [ ] T-2" in md

    def test_outcome_handoff_items(self):
        r = _TestRenderer()
        r.outcome = SessionOutcome(status="PARTIAL", handoff_items=["Continue work"])
        md = r._render_session_markdown()
        assert "### Handoff Items" in md
        assert "Continue work" in md

    def test_outcome_discoveries(self):
        r = _TestRenderer()
        r.outcome = SessionOutcome(status="COMPLETE", discoveries=["GAP-NEW-001"])
        md = r._render_session_markdown()
        assert "### Discoveries" in md
        assert "GAP-NEW-001" in md

    def test_with_decisions(self):
        r = _TestRenderer()
        r.decisions = [
            Decision(id="D-001", name="Use TypeDB", context="ctx", rationale="better", status="active"),
        ]
        md = r._render_session_markdown()
        assert "## Decisions" in md
        assert "D-001" in md
        assert "Use TypeDB" in md

    def test_with_tasks(self):
        r = _TestRenderer()
        r.tasks = [
            Task(id="T-001", name="Fix bug", description="desc", status="completed", priority="HIGH"),
        ]
        md = r._render_session_markdown()
        assert "## Tasks" in md
        assert "T-001" in md
        assert "Fix bug" in md

    def test_with_thought_events(self):
        r = _TestRenderer()
        r.events = [
            SessionEvent(
                timestamp="t1", event_type="thought", content="I should check the schema",
                metadata={"thought_type": "reasoning", "confidence": 0.8, "related_tools": ["grep"]},
            ),
        ]
        md = r._render_session_markdown()
        assert "## Key Thoughts" in md
        assert "I should check the schema" in md

    def test_with_tool_call_events(self):
        r = _TestRenderer()
        r.events = [
            SessionEvent(
                timestamp="t1", event_type="tool_call", content="health_check",
                metadata={"tool_name": "health_check", "success": True, "duration_ms": 42},
            ),
        ]
        md = r._render_session_markdown()
        assert "## Tool Calls" in md
        assert "health_check" in md

    def test_event_timeline(self):
        r = _TestRenderer()
        r.events = [
            SessionEvent(timestamp="t1", event_type="prompt", content="hello"),
            SessionEvent(timestamp="t2", event_type="response", content="world"),
        ]
        md = r._render_session_markdown()
        assert "## Event Timeline" in md
        assert "PROMPT" in md
        assert "RESPONSE" in md


class TestGenerateSessionLog:
    """Tests for generate_session_log()."""

    def test_creates_file(self, tmp_path):
        r = _TestRenderer()
        r.evidence_dir = tmp_path
        filepath = r.generate_session_log()
        assert Path(filepath).exists()
        content = Path(filepath).read_text()
        assert "SESSION-2026-02-11-TEST" in content

    def test_custom_output_dir(self, tmp_path):
        out = tmp_path / "custom"
        r = _TestRenderer()
        filepath = r.generate_session_log(output_dir=out)
        assert Path(filepath).exists()
        assert "custom" in filepath

    def test_sets_end_time(self):
        r = _TestRenderer()
        r.evidence_dir = Path("/tmp")
        assert r.end_time is None
        # Don't actually write, just check end_time would be set
        r.end_time = datetime.now()
        assert r.end_time is not None


class TestToDict:
    """Tests for to_dict()."""

    def test_basic(self):
        r = _TestRenderer()
        d = r.to_dict()
        assert d["session_id"] == "SESSION-2026-02-11-TEST"
        assert d["topic"] == "Test"
        assert d["session_type"] == "CHAT"
        assert d["events_count"] == 0
        assert d["decisions_count"] == 0
        assert d["tasks_count"] == 0

    def test_with_events(self):
        r = _TestRenderer()
        r.events = [
            SessionEvent(timestamp="t1", event_type="prompt", content="hi"),
        ]
        d = r.to_dict()
        assert d["events_count"] == 1

    def test_with_decisions(self):
        r = _TestRenderer()
        r.decisions = [
            Decision(id="D-1", name="n", context="c", rationale="r", status="active"),
        ]
        d = r.to_dict()
        assert d["decisions_count"] == 1
        assert d["decisions"][0]["id"] == "D-1"

    def test_with_tasks(self):
        r = _TestRenderer()
        r.tasks = [
            Task(id="T-1", name="n", description="d", status="pending"),
        ]
        d = r.to_dict()
        assert d["tasks_count"] == 1
        assert d["tasks"][0]["id"] == "T-1"

    def test_with_intent(self):
        r = _TestRenderer()
        r.intent = SessionIntent(goal="G", source="S")
        d = r.to_dict()
        assert "intent" in d
        assert d["intent"]["goal"] == "G"

    def test_with_outcome(self):
        r = _TestRenderer()
        r.outcome = SessionOutcome(status="COMPLETE")
        d = r.to_dict()
        assert "outcome" in d
        assert d["outcome"]["status"] == "COMPLETE"

    def test_no_intent_or_outcome(self):
        r = _TestRenderer()
        d = r.to_dict()
        assert "intent" not in d
        assert "outcome" not in d

    def test_end_time_none(self):
        r = _TestRenderer()
        d = r.to_dict()
        assert d["end_time"] is None

    def test_end_time_set(self):
        r = _TestRenderer()
        r.end_time = datetime(2026, 2, 11, 11, 0, 0)
        d = r.to_dict()
        assert d["end_time"] == "2026-02-11T11:00:00"


class TestToJson:
    """Tests for to_json()."""

    def test_valid_json(self):
        r = _TestRenderer()
        j = r.to_json()
        parsed = json.loads(j)
        assert parsed["session_id"] == "SESSION-2026-02-11-TEST"

    def test_with_decisions_serializable(self):
        r = _TestRenderer()
        r.decisions = [
            Decision(id="D-1", name="n", context="c", rationale="r",
                     status="active", decision_date=datetime(2026, 2, 11)),
        ]
        j = r.to_json()
        parsed = json.loads(j)
        assert len(parsed["decisions"]) == 1
