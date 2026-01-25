"""
Robot Framework Library for SessionCollector Tests.

Per P4.2: Session Collector.
Migrated from tests/test_session_collector.py
"""
import json
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class SessionCollectorLibrary:
    """Library for testing SessionCollector class."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # SessionCollector Unit Tests
    # =============================================================================

    @keyword("Session Collector Class Exists")
    def session_collector_class_exists(self):
        """SessionCollector class exists and is importable."""
        try:
            from governance.session_collector import SessionCollector
            return {"exists": SessionCollector is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Collector Creates Session ID")
    def session_collector_creates_session_id(self):
        """SessionCollector generates correct session ID format."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST-TOPIC")
            return {
                "has_session_prefix": "SESSION-" in collector.session_id,
                "has_topic": "TEST-TOPIC" in collector.session_id
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Collector Stores Topic")
    def session_collector_stores_topic(self):
        """SessionCollector stores topic and session type."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("MY-TOPIC", session_type="strategic")
            return {
                "topic_correct": collector.topic == "MY-TOPIC",
                "type_correct": collector.session_type == "strategic"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Collector Has Empty Collections")
    def session_collector_has_empty_collections(self):
        """SessionCollector starts with empty collections."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            return {
                "events_empty": collector.events == [],
                "decisions_empty": collector.decisions == [],
                "tasks_empty": collector.tasks == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Event Capture Tests
    # =============================================================================

    @keyword("Capture Prompt Adds Event")
    def capture_prompt_adds_event(self):
        """capture_prompt adds event."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            collector.capture_prompt("What is the architecture?")
            return {
                "event_added": len(collector.events) == 1,
                "type_correct": collector.events[0].event_type == "prompt",
                "content_correct": "architecture" in collector.events[0].content
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Capture Response Adds Event")
    def capture_response_adds_event(self):
        """capture_response adds event."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            collector.capture_response("The architecture is...")
            return {
                "event_added": len(collector.events) == 1,
                "type_correct": collector.events[0].event_type == "response"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Capture Error Adds Event")
    def capture_error_adds_event(self):
        """capture_error adds error event."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            collector.capture_error("Connection failed", context="TypeDB")
            return {
                "event_added": len(collector.events) == 1,
                "type_correct": collector.events[0].event_type == "error",
                "content_correct": "Connection failed" in collector.events[0].content
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Decision Capture Tests
    # =============================================================================

    @keyword("Capture Decision Creates Decision")
    def capture_decision_creates_decision(self):
        """capture_decision creates Decision object."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            decision = collector.capture_decision(
                decision_id="DECISION-007",
                name="Use TypeDB",
                context="Need graph database",
                rationale="TypeDB supports inference"
            )
            return {
                "id_correct": decision.id == "DECISION-007",
                "name_correct": decision.name == "Use TypeDB",
                "decision_added": len(collector.decisions) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Capture Decision Adds Event")
    def capture_decision_adds_event(self):
        """capture_decision also adds event."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            collector.capture_decision(
                decision_id="DECISION-008",
                name="Use ChromaDB",
                context="Need vector search",
                rationale="ChromaDB is simple"
            )
            return {
                "event_added": len(collector.events) == 1,
                "type_correct": collector.events[0].event_type == "decision",
                "content_has_id": "DECISION-008" in collector.events[0].content
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Task Capture Tests
    # =============================================================================

    @keyword("Capture Task Creates Task")
    def capture_task_creates_task(self):
        """capture_task creates Task object."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            task = collector.capture_task(
                task_id="P4.2",
                name="Implement SessionCollector",
                description="Create session evidence collector",
                status="in_progress",
                priority="HIGH"
            )
            return {
                "id_correct": task.id == "P4.2",
                "name_correct": task.name == "Implement SessionCollector",
                "status_correct": task.status == "in_progress",
                "priority_correct": task.priority == "HIGH",
                "task_added": len(collector.tasks) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Capture Task Adds Event")
    def capture_task_adds_event(self):
        """capture_task also adds event."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            collector.capture_task(
                task_id="RD-001",
                name="Research Haskell",
                description="Research Haskell MCP",
                status="pending"
            )
            return {
                "event_added": len(collector.events) == 1,
                "type_correct": collector.events[0].event_type == "task"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Session Log Generation Tests
    # =============================================================================

    @keyword("Generate Session Log Creates File")
    def generate_session_log_creates_file(self):
        """generate_session_log creates markdown file."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_prompt("Test prompt")
                log_path = collector.generate_session_log(Path(tmpdir))

                return {
                    "file_exists": Path(log_path).exists(),
                    "is_markdown": log_path.endswith(".md")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Header")
    def generate_session_log_contains_header(self):
        """Generated log contains session header."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("MY-TOPIC", evidence_dir=tmpdir)
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path) as f:
                    content = f.read()

                return {
                    "has_topic": "MY-TOPIC" in content,
                    "has_session_id": "Session ID:" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Decisions")
    def generate_session_log_contains_decisions(self):
        """Generated log contains decisions section."""
        try:
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

                return {
                    "has_decisions_section": "## Decisions" in content,
                    "has_decision_id": "DECISION-001" in content,
                    "has_decision_name": "Test Decision" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Thoughts")
    def generate_session_log_contains_thoughts(self):
        """Generated log contains Key Thoughts section."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_thought(
                    thought="This is a key reasoning step",
                    thought_type="hypothesis",
                    confidence=0.85
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_thoughts_section": "## Key Thoughts" in content,
                    "has_hypothesis": "Hypothesis" in content,
                    "has_reasoning": "key reasoning step" in content,
                    "has_confidence": "Confidence: 85" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Tool Calls")
    def generate_session_log_contains_tool_calls(self):
        """Generated log contains Tool Calls section."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_tool_call(
                    tool_name="governance_get_rule",
                    arguments={"rule_id": "RULE-001"},
                    result="Rule returned successfully",
                    duration_ms=150,
                    success=True
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_tool_calls_section": "## Tool Calls" in content,
                    "has_tool_name": "governance_get_rule" in content,
                    "has_duration": "150ms" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Initial Prompt")
    def generate_session_log_contains_initial_prompt(self):
        """Generated log contains initial prompt per SESSION-PROMPT-01-v1."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_intent(
                    goal="Fix the bug",
                    source="User request",
                    initial_prompt="Please fix the login bug that crashes on mobile"
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_intent_section": "## Session Intent" in content,
                    "has_initial_prompt": "### Initial Prompt" in content,
                    "has_prompt_content": "login bug that crashes on mobile" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Serialization Tests
    # =============================================================================

    @keyword("To Dict Returns Dict")
    def to_dict_returns_dict(self):
        """to_dict returns dictionary."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            result = collector.to_dict()
            return {
                "is_dict": isinstance(result, dict),
                "has_session_id": "session_id" in result,
                "has_topic": "topic" in result,
                "has_events_count": "events_count" in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("To JSON Returns Valid JSON")
    def to_json_returns_valid_json(self):
        """to_json returns valid JSON string."""
        try:
            from governance.session_collector import SessionCollector
            collector = SessionCollector("TEST")
            result = collector.to_json()
            parsed = json.loads(result)
            return {
                "valid_json": True,
                "topic_correct": parsed["topic"] == "TEST"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    # =============================================================================
    # Session Registry Tests
    # =============================================================================

    @keyword("Get Or Create Session Creates New")
    def get_or_create_session_creates_new(self):
        """get_or_create_session creates new session."""
        try:
            from governance.session_collector import get_or_create_session, _active_sessions
            _active_sessions.clear()
            collector = get_or_create_session("NEW-TOPIC")
            return {
                "created": collector is not None,
                "has_topic": "NEW-TOPIC" in collector.session_id
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Or Create Session Returns Existing")
    def get_or_create_session_returns_existing(self):
        """get_or_create_session returns existing session."""
        try:
            from governance.session_collector import get_or_create_session, _active_sessions
            _active_sessions.clear()
            collector1 = get_or_create_session("SAME-TOPIC")
            collector2 = get_or_create_session("SAME-TOPIC")
            return {"same_instance": collector1 is collector2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Active Sessions Returns IDs")
    def list_active_sessions_returns_ids(self):
        """list_active_sessions returns session IDs."""
        try:
            from governance.session_collector import (
                get_or_create_session,
                list_active_sessions,
                _active_sessions
            )
            _active_sessions.clear()
            get_or_create_session("TOPIC-A")
            get_or_create_session("TOPIC-B")
            sessions = list_active_sessions()
            return {"correct_count": len(sessions) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("End Session Removes And Generates Log")
    def end_session_removes_and_generates_log(self):
        """end_session removes session and generates log."""
        try:
            from governance.session_collector import (
                get_or_create_session,
                end_session,
                list_active_sessions,
                _active_sessions
            )
            _active_sessions.clear()
            collector = get_or_create_session("END-TEST")
            collector.capture_prompt("Test")

            with tempfile.TemporaryDirectory() as tmpdir:
                collector.evidence_dir = Path(tmpdir)
                log_path = end_session("END-TEST")

                return {
                    "log_generated": log_path is not None,
                    "session_removed": "END-TEST" not in [s for s in list_active_sessions()]
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # MCP Session Tools Tests
    # =============================================================================

    @keyword("Session Start Tool Exists")
    def session_start_tool_exists(self):
        """session_start MCP tool exists."""
        try:
            from governance.compat import session_start
            return {
                "exists": session_start is not None,
                "callable": callable(session_start)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Start Returns JSON")
    def session_start_returns_json(self):
        """session_start returns valid JSON."""
        try:
            from governance.compat import session_start
            from governance.session_collector import _active_sessions
            _active_sessions.clear()
            result = session_start("MCP-TEST", "research")
            parsed = json.loads(result)
            return {
                "has_session_id": "session_id" in parsed,
                "topic_correct": parsed["topic"] == "MCP-TEST"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Session Decision Tool Exists")
    def session_decision_tool_exists(self):
        """session_decision MCP tool exists."""
        try:
            from governance.compat import session_decision
            return {
                "exists": session_decision is not None,
                "callable": callable(session_decision)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Task Tool Exists")
    def session_task_tool_exists(self):
        """session_task MCP tool exists."""
        try:
            from governance.compat import session_task
            return {
                "exists": session_task is not None,
                "callable": callable(session_task)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session End Tool Exists")
    def session_end_tool_exists(self):
        """session_end MCP tool exists."""
        try:
            from governance.compat import session_end
            return {
                "exists": session_end is not None,
                "callable": callable(session_end)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session List Tool Exists")
    def session_list_tool_exists(self):
        """session_list MCP tool exists."""
        try:
            from governance.compat import session_list
            return {
                "exists": session_list is not None,
                "callable": callable(session_list)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Session Dataclasses Tests
    # =============================================================================

    @keyword("Session Event Dataclass Works")
    def session_event_dataclass_works(self):
        """SessionEvent dataclass works."""
        try:
            from governance.session_collector import SessionEvent
            event = SessionEvent(
                timestamp="2024-12-24T12:00:00",
                event_type="prompt",
                content="Test content",
                metadata={"key": "value"}
            )
            return {
                "timestamp_correct": event.timestamp == "2024-12-24T12:00:00",
                "type_correct": event.event_type == "prompt",
                "metadata_correct": event.metadata["key"] == "value"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Dataclass Works")
    def task_dataclass_works(self):
        """Task dataclass works."""
        try:
            from governance.session_collector import Task
            task = Task(
                id="P4.2",
                name="Test Task",
                description="A test task",
                status="pending",
                priority="HIGH"
            )
            return {
                "id_correct": task.id == "P4.2",
                "status_correct": task.status == "pending",
                "priority_correct": task.priority == "HIGH"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
