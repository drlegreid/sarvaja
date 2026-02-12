"""
Unit tests for Session Collector Capture Mixin.

Per DOC-SIZE-01-v1: Tests for session_collector/capture.py module.
Tests: SessionCaptureMixin methods (prompt, response, decision, task, etc.).
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from governance.session_collector.models import (
    SessionEvent, Task, Decision, SessionIntent, SessionOutcome,
)
from governance.session_collector.capture import SessionCaptureMixin


class _TestCollector(SessionCaptureMixin):
    """Concrete class for testing the mixin."""

    def __init__(self, session_id="SESSION-2026-02-11-TEST"):
        self.session_id = session_id
        self.events = []
        self.decisions = []
        self.tasks = []
        self.intent = None
        self.outcome = None

    def _index_decision_to_typedb(self, decision):
        pass

    def _index_task_to_typedb(self, task):
        pass


class TestCapturePrompt:
    """Tests for capture_prompt()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_prompt("hello world")
        assert len(c.events) == 1
        assert c.events[0].event_type == "prompt"
        assert c.events[0].content == "hello world"

    def test_with_metadata(self):
        c = _TestCollector()
        c.capture_prompt("test", metadata={"model": "opus"})
        assert c.events[0].metadata["model"] == "opus"
        assert c.events[0].metadata["session_id"] == "SESSION-2026-02-11-TEST"


class TestCaptureResponse:
    """Tests for capture_response()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_response("answer here")
        assert len(c.events) == 1
        assert c.events[0].event_type == "response"
        assert c.events[0].content == "answer here"

    def test_with_metadata(self):
        c = _TestCollector()
        c.capture_response("resp", metadata={"tokens": 100})
        assert c.events[0].metadata["tokens"] == 100


class TestCaptureDecision:
    """Tests for capture_decision()."""

    def test_basic(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            d = c.capture_decision("D-001", "Use TypeDB", "context", "better schema")
        assert isinstance(d, Decision)
        assert d.id == "D-001"
        assert d.name == "Use TypeDB"
        assert len(c.decisions) == 1
        assert len(c.events) == 1
        assert c.events[0].event_type == "decision"

    def test_custom_status(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            d = c.capture_decision("D-002", "Name", "ctx", "why", status="pending")
        assert d.status == "pending"

    def test_event_metadata(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            c.capture_decision("D-003", "Name", "ctx", "rationale text")
        assert c.events[0].metadata["decision_id"] == "D-003"
        assert c.events[0].metadata["rationale"] == "rationale text"


class TestCaptureTask:
    """Tests for capture_task()."""

    def test_basic(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            t = c.capture_task("T-001", "Fix bug", "Fix the login bug")
        assert isinstance(t, Task)
        assert t.id == "T-001"
        assert t.status == "pending"
        assert t.priority == "MEDIUM"
        assert len(c.tasks) == 1
        assert len(c.events) == 1

    def test_custom_priority(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            t = c.capture_task("T-002", "Critical", "desc", priority="CRITICAL")
        assert t.priority == "CRITICAL"

    def test_event_metadata(self):
        c = _TestCollector()
        with patch("governance.session_collector.capture.TYPEDB_AVAILABLE", False):
            c.capture_task("T-003", "Task", "desc", status="in_progress", priority="HIGH")
        assert c.events[0].metadata["task_id"] == "T-003"
        assert c.events[0].metadata["status"] == "in_progress"
        assert c.events[0].metadata["priority"] == "HIGH"


class TestCaptureError:
    """Tests for capture_error()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_error("Connection timeout")
        assert c.events[0].event_type == "error"
        assert c.events[0].content == "Connection timeout"

    def test_with_context(self):
        c = _TestCollector()
        c.capture_error("Failed", context="TypeDB query")
        assert c.events[0].metadata["context"] == "TypeDB query"


class TestCaptureToolCall:
    """Tests for capture_tool_call()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_tool_call("health_check")
        assert c.events[0].event_type == "tool_call"
        assert "health_check" in c.events[0].content

    def test_with_all_params(self):
        c = _TestCollector()
        c.capture_tool_call(
            "task_create",
            arguments={"name": "test"},
            result="created T-001",
            duration_ms=42,
            success=True,
            correlation_id="corr-1",
            applied_rules=["RULE-001"],
        )
        meta = c.events[0].metadata
        assert meta["tool_name"] == "task_create"
        assert meta["arguments"] == {"name": "test"}
        assert meta["duration_ms"] == 42
        assert meta["success"] is True
        assert meta["correlation_id"] == "corr-1"
        assert meta["applied_rules"] == ["RULE-001"]

    def test_truncates_long_result(self):
        c = _TestCollector()
        long_result = "x" * 1000
        c.capture_tool_call("tool", result=long_result)
        summary = c.events[0].metadata["result_summary"]
        assert len(summary) <= 504  # 500 + "..."


class TestCaptureThought:
    """Tests for capture_thought()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_thought("I think we should use approach A")
        assert c.events[0].event_type == "thought"
        assert c.events[0].content == "I think we should use approach A"
        assert c.events[0].metadata["thought_type"] == "reasoning"

    def test_with_confidence(self):
        c = _TestCollector()
        c.capture_thought("Likely correct", confidence=0.9, related_tools=["grep"])
        assert c.events[0].metadata["confidence"] == 0.9
        assert c.events[0].metadata["related_tools"] == ["grep"]


class TestCaptureIntent:
    """Tests for capture_intent()."""

    def test_basic(self):
        c = _TestCollector()
        intent = c.capture_intent("Fix bugs", "TODO.md")
        assert isinstance(intent, SessionIntent)
        assert intent.goal == "Fix bugs"
        assert intent.source == "TODO.md"
        assert c.intent is intent
        assert c.events[0].event_type == "intent"

    def test_with_all_fields(self):
        c = _TestCollector()
        intent = c.capture_intent(
            "Implement feature",
            "User request",
            planned_tasks=["T-1"],
            previous_session_id="SESSION-PREV",
            initial_prompt="Please add dark mode",
        )
        assert intent.planned_tasks == ["T-1"]
        assert intent.previous_session_id == "SESSION-PREV"
        assert intent.initial_prompt == "Please add dark mode"


class TestCaptureOutcome:
    """Tests for capture_outcome()."""

    def test_basic(self):
        c = _TestCollector()
        outcome = c.capture_outcome("COMPLETE")
        assert isinstance(outcome, SessionOutcome)
        assert outcome.status == "COMPLETE"
        assert c.outcome is outcome
        assert c.events[0].event_type == "outcome"

    def test_with_all_fields(self):
        c = _TestCollector()
        outcome = c.capture_outcome(
            "PARTIAL",
            achieved_tasks=["T-1"],
            deferred_tasks=["T-2"],
            handoff_items=["Continue T-2"],
            discoveries=["GAP-NEW-001"],
        )
        assert outcome.achieved_tasks == ["T-1"]
        assert outcome.deferred_tasks == ["T-2"]
        assert outcome.discoveries == ["GAP-NEW-001"]


class TestCaptureTestResult:
    """Tests for capture_test_result()."""

    def test_basic(self):
        c = _TestCollector()
        c.capture_test_result(
            test_id="test_foo", name="test_foo", category="unit", status="passed",
        )
        assert c.events[0].event_type == "test_result"
        assert "PASSED" in c.events[0].content

    def test_with_all_params(self):
        c = _TestCollector()
        c.capture_test_result(
            test_id="test_bar", name="test_bar", category="integration",
            status="failed", duration_ms=150.0, intent="Validate login",
            linked_rules=["RULE-001"], linked_gaps=["GAP-001"],
            error_message="AssertionError",
        )
        meta = c.events[0].metadata
        assert meta["category"] == "integration"
        assert meta["status"] == "failed"
        assert meta["duration_ms"] == 150.0
        assert meta["linked_rules"] == ["RULE-001"]
        assert meta["error_message"] == "AssertionError"

    def test_truncates_long_error(self):
        c = _TestCollector()
        long_error = "e" * 1000
        c.capture_test_result(
            test_id="t", name="t", category="unit", status="failed",
            error_message=long_error,
        )
        assert len(c.events[0].metadata["error_message"]) <= 500
