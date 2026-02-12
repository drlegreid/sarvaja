"""
Unit tests for Session Collector Data Models.

Per DOC-SIZE-01-v1: Tests for session_collector/models.py module.
Tests: SessionEvent, Task, Decision, SessionIntent, SessionOutcome, get_decision_class.
"""

import pytest
from datetime import datetime
from dataclasses import asdict

from governance.session_collector.models import (
    SessionEvent,
    Task,
    Decision,
    SessionIntent,
    SessionOutcome,
    get_decision_class,
)


class TestSessionEvent:
    """Tests for SessionEvent dataclass."""

    def test_basic(self):
        e = SessionEvent(timestamp="2026-02-11T10:00:00", event_type="prompt", content="hello")
        assert e.timestamp == "2026-02-11T10:00:00"
        assert e.event_type == "prompt"
        assert e.content == "hello"
        assert e.metadata == {}

    def test_with_metadata(self):
        e = SessionEvent(
            timestamp="t1", event_type="tool_call", content="test",
            metadata={"tool_name": "health_check", "success": True},
        )
        assert e.metadata["tool_name"] == "health_check"
        assert e.metadata["success"] is True

    def test_asdict(self):
        e = SessionEvent(timestamp="t1", event_type="response", content="hi")
        d = asdict(e)
        assert isinstance(d, dict)
        assert d["event_type"] == "response"


class TestTask:
    """Tests for Task dataclass."""

    def test_required_fields(self):
        t = Task(id="T-1", name="Test task", description="desc", status="pending")
        assert t.id == "T-1"
        assert t.name == "Test task"
        assert t.status == "pending"

    def test_defaults(self):
        t = Task(id="T-1", name="n", description="d", status="pending")
        assert t.priority == "MEDIUM"
        assert t.created_date is None

    def test_custom_priority(self):
        t = Task(id="T-1", name="n", description="d", status="in_progress", priority="HIGH")
        assert t.priority == "HIGH"

    def test_asdict(self):
        t = Task(id="T-1", name="n", description="d", status="completed")
        d = asdict(t)
        assert d["id"] == "T-1"
        assert d["status"] == "completed"


class TestDecision:
    """Tests for Decision dataclass."""

    def test_required_fields(self):
        d = Decision(id="D-1", name="Choice A", context="ctx", rationale="why", status="active")
        assert d.id == "D-1"
        assert d.name == "Choice A"
        assert d.context == "ctx"
        assert d.rationale == "why"

    def test_defaults(self):
        d = Decision(id="D-1", name="n", context="c", rationale="r", status="active")
        assert d.decision_date is None

    def test_with_date(self):
        now = datetime.now()
        d = Decision(id="D-1", name="n", context="c", rationale="r", status="active", decision_date=now)
        assert d.decision_date == now

    def test_asdict(self):
        d = Decision(id="D-1", name="n", context="c", rationale="r", status="pending")
        data = asdict(d)
        assert data["status"] == "pending"
        assert isinstance(data, dict)


class TestSessionIntent:
    """Tests for SessionIntent dataclass."""

    def test_basic(self):
        intent = SessionIntent(goal="Fix bug", source="TODO.md")
        assert intent.goal == "Fix bug"
        assert intent.source == "TODO.md"
        assert intent.planned_tasks == []
        assert intent.previous_session_id is None
        assert intent.initial_prompt is None
        assert intent.captured_at  # auto-populated

    def test_with_all_fields(self):
        intent = SessionIntent(
            goal="Implement feature",
            source="User request",
            planned_tasks=["T-1", "T-2"],
            previous_session_id="SESSION-2026-02-10-PREV",
            initial_prompt="Please add dark mode",
        )
        assert len(intent.planned_tasks) == 2
        assert intent.previous_session_id == "SESSION-2026-02-10-PREV"
        assert intent.initial_prompt == "Please add dark mode"

    def test_independent_instances(self):
        i1 = SessionIntent(goal="A", source="X")
        i2 = SessionIntent(goal="B", source="Y")
        i1.planned_tasks.append("T-1")
        assert i2.planned_tasks == []


class TestSessionOutcome:
    """Tests for SessionOutcome dataclass."""

    def test_basic(self):
        outcome = SessionOutcome(status="COMPLETE")
        assert outcome.status == "COMPLETE"
        assert outcome.achieved_tasks == []
        assert outcome.deferred_tasks == []
        assert outcome.handoff_items == []
        assert outcome.discoveries == []
        assert outcome.captured_at

    def test_with_all_fields(self):
        outcome = SessionOutcome(
            status="PARTIAL",
            achieved_tasks=["T-1"],
            deferred_tasks=["T-2"],
            handoff_items=["Continue T-2"],
            discoveries=["GAP-NEW-001"],
        )
        assert outcome.status == "PARTIAL"
        assert len(outcome.achieved_tasks) == 1
        assert len(outcome.discoveries) == 1

    def test_independent_instances(self):
        o1 = SessionOutcome(status="COMPLETE")
        o2 = SessionOutcome(status="PARTIAL")
        o1.achieved_tasks.append("T-1")
        assert o2.achieved_tasks == []


class TestGetDecisionClass:
    """Tests for get_decision_class()."""

    def test_returns_class(self):
        cls = get_decision_class()
        assert callable(cls)

    def test_decision_class_has_id(self):
        cls = get_decision_class()
        if cls is Decision:
            d = cls(id="D-1", name="n", context="c", rationale="r", status="s")
            assert d.id == "D-1"
