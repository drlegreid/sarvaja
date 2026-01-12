"""
Tests for SessionCollector (P4.2)

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: R&D-BACKLOG.md Phase 4.2, STRATEGIC-SESSION-FLOW.md
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch


class TestSessionCollectorUnit:
    """Unit tests for SessionCollector class."""

    def test_session_collector_class_exists(self):
        """SessionCollector class exists and is importable."""
        from governance.session_collector import SessionCollector
        assert SessionCollector is not None

    def test_session_collector_creates_session_id(self):
        """SessionCollector generates correct session ID format."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST-TOPIC")
        assert "SESSION-" in collector.session_id
        assert "TEST-TOPIC" in collector.session_id

    def test_session_collector_stores_topic(self):
        """SessionCollector stores topic."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("MY-TOPIC", session_type="strategic")
        assert collector.topic == "MY-TOPIC"
        assert collector.session_type == "strategic"

    def test_session_collector_has_empty_collections(self):
        """SessionCollector starts with empty collections."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        assert collector.events == []
        assert collector.decisions == []
        assert collector.tasks == []


class TestSessionEventCapture:
    """Tests for event capture methods."""

    def test_capture_prompt(self):
        """capture_prompt adds event."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        collector.capture_prompt("What is the architecture?")

        assert len(collector.events) == 1
        assert collector.events[0].event_type == "prompt"
        assert "architecture" in collector.events[0].content

    def test_capture_response(self):
        """capture_response adds event."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        collector.capture_response("The architecture is...")

        assert len(collector.events) == 1
        assert collector.events[0].event_type == "response"

    def test_capture_error(self):
        """capture_error adds error event."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        collector.capture_error("Connection failed", context="TypeDB")

        assert len(collector.events) == 1
        assert collector.events[0].event_type == "error"
        assert "Connection failed" in collector.events[0].content


class TestDecisionCapture:
    """Tests for decision capture."""

    def test_capture_decision_creates_decision(self):
        """capture_decision creates Decision object."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")

        decision = collector.capture_decision(
            decision_id="DECISION-007",
            name="Use TypeDB",
            context="Need graph database",
            rationale="TypeDB supports inference"
        )

        assert decision.id == "DECISION-007"
        assert decision.name == "Use TypeDB"
        assert len(collector.decisions) == 1

    def test_capture_decision_adds_event(self):
        """capture_decision also adds event."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")

        collector.capture_decision(
            decision_id="DECISION-008",
            name="Use ChromaDB",
            context="Need vector search",
            rationale="ChromaDB is simple"
        )

        assert len(collector.events) == 1
        assert collector.events[0].event_type == "decision"
        assert "DECISION-008" in collector.events[0].content


class TestTaskCapture:
    """Tests for task capture."""

    def test_capture_task_creates_task(self):
        """capture_task creates Task object."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")

        task = collector.capture_task(
            task_id="P4.2",
            name="Implement SessionCollector",
            description="Create session evidence collector",
            status="in_progress",
            priority="HIGH"
        )

        assert task.id == "P4.2"
        assert task.name == "Implement SessionCollector"
        assert task.status == "in_progress"
        assert task.priority == "HIGH"
        assert len(collector.tasks) == 1

    def test_capture_task_adds_event(self):
        """capture_task also adds event."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")

        collector.capture_task(
            task_id="RD-001",
            name="Research Haskell",
            description="Research Haskell MCP",
            status="pending"
        )

        assert len(collector.events) == 1
        assert collector.events[0].event_type == "task"


class TestSessionLogGeneration:
    """Tests for session log generation."""

    def test_generate_session_log_creates_file(self):
        """generate_session_log creates markdown file."""
        from governance.session_collector import SessionCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SessionCollector("TEST", evidence_dir=tmpdir)
            collector.capture_prompt("Test prompt")

            log_path = collector.generate_session_log(Path(tmpdir))

            assert Path(log_path).exists()
            assert log_path.endswith(".md")

    def test_generate_session_log_contains_header(self):
        """Generated log contains session header."""
        from governance.session_collector import SessionCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SessionCollector("MY-TOPIC", evidence_dir=tmpdir)
            log_path = collector.generate_session_log(Path(tmpdir))

            with open(log_path) as f:
                content = f.read()

            assert "MY-TOPIC" in content
            assert "Session ID:" in content

    def test_generate_session_log_contains_decisions(self):
        """Generated log contains decisions section."""
        from governance.session_collector import SessionCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SessionCollector("TEST", evidence_dir=tmpdir)
            collector.capture_decision(
                decision_id="DECISION-001",
                name="Test Decision",
                context="Testing",
                rationale="For testing"
            )

            log_path = collector.generate_session_log(Path(tmpdir))

            with open(log_path, encoding="utf-8") as f:
                content = f.read()

            assert "## Decisions" in content
            assert "DECISION-001" in content
            assert "Test Decision" in content


class TestSessionSerialization:
    """Tests for session serialization."""

    def test_to_dict_returns_dict(self):
        """to_dict returns dictionary."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        result = collector.to_dict()

        assert isinstance(result, dict)
        assert "session_id" in result
        assert "topic" in result
        assert "events_count" in result

    def test_to_json_returns_valid_json(self):
        """to_json returns valid JSON string."""
        from governance.session_collector import SessionCollector
        collector = SessionCollector("TEST")
        result = collector.to_json()

        parsed = json.loads(result)
        assert parsed["topic"] == "TEST"


class TestSessionRegistry:
    """Tests for session registry functions."""

    def test_get_or_create_session_creates_new(self):
        """get_or_create_session creates new session."""
        from governance.session_collector import get_or_create_session, _active_sessions

        # Clear existing sessions
        _active_sessions.clear()

        collector = get_or_create_session("NEW-TOPIC")
        assert collector is not None
        assert "NEW-TOPIC" in collector.session_id

    def test_get_or_create_session_returns_existing(self):
        """get_or_create_session returns existing session."""
        from governance.session_collector import get_or_create_session, _active_sessions

        _active_sessions.clear()

        collector1 = get_or_create_session("SAME-TOPIC")
        collector2 = get_or_create_session("SAME-TOPIC")

        assert collector1 is collector2

    def test_list_active_sessions(self):
        """list_active_sessions returns session IDs."""
        from governance.session_collector import (
            get_or_create_session,
            list_active_sessions,
            _active_sessions
        )

        _active_sessions.clear()

        get_or_create_session("TOPIC-A")
        get_or_create_session("TOPIC-B")

        sessions = list_active_sessions()
        assert len(sessions) == 2

    def test_end_session_removes_and_generates_log(self):
        """end_session removes session and generates log."""
        from governance.session_collector import (
            get_or_create_session,
            end_session,
            list_active_sessions,
            _active_sessions
        )

        _active_sessions.clear()

        collector = get_or_create_session("END-TEST")
        collector.capture_prompt("Test")

        # Override evidence dir to temp
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            collector.evidence_dir = Path(tmpdir)
            log_path = end_session("END-TEST")

            assert log_path is not None
            assert "END-TEST" not in [s for s in list_active_sessions()]


class TestMCPSessionTools:
    """Tests for MCP session tools."""

    def test_session_start_tool_exists(self):
        """session_start MCP tool exists."""
        from governance.compat import session_start
        assert session_start is not None
        assert callable(session_start)

    def test_session_start_returns_json(self):
        """session_start returns valid JSON."""
        from governance.compat import session_start
        from governance.session_collector import _active_sessions

        _active_sessions.clear()
        result = session_start("MCP-TEST", "research")

        parsed = json.loads(result)
        assert "session_id" in parsed
        assert parsed["topic"] == "MCP-TEST"

    def test_session_decision_tool_exists(self):
        """session_decision MCP tool exists."""
        from governance.compat import session_decision
        assert session_decision is not None
        assert callable(session_decision)

    def test_session_task_tool_exists(self):
        """session_task MCP tool exists."""
        from governance.compat import session_task
        assert session_task is not None
        assert callable(session_task)

    def test_session_end_tool_exists(self):
        """session_end MCP tool exists."""
        from governance.compat import session_end
        assert session_end is not None
        assert callable(session_end)

    def test_session_list_tool_exists(self):
        """session_list MCP tool exists."""
        from governance.compat import session_list
        assert session_list is not None
        assert callable(session_list)


class TestSessionDataclasses:
    """Tests for session dataclasses."""

    def test_session_event_dataclass(self):
        """SessionEvent dataclass works."""
        from governance.session_collector import SessionEvent

        event = SessionEvent(
            timestamp="2024-12-24T12:00:00",
            event_type="prompt",
            content="Test content",
            metadata={"key": "value"}
        )

        assert event.timestamp == "2024-12-24T12:00:00"
        assert event.event_type == "prompt"
        assert event.metadata["key"] == "value"

    def test_task_dataclass(self):
        """Task dataclass works."""
        from governance.session_collector import Task

        task = Task(
            id="P4.2",
            name="Test Task",
            description="A test task",
            status="pending",
            priority="HIGH"
        )

        assert task.id == "P4.2"
        assert task.status == "pending"
        assert task.priority == "HIGH"
