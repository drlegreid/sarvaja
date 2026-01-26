"""
Robot Framework Library for Task UI Event Types Tests.

Per: Phase 6.1, RULE-019 (UI/UX Design Standards), DOC-SIZE-01-v1.
Split from tests/test_task_ui.py
"""
import json
from pathlib import Path
from robot.api.deco import keyword


class TaskUIEventTypesLibrary:
    """Library for Task UI event types tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # AG-UI Event Type Tests
    # =========================================================================

    @keyword("AGUI Event Types Defined")
    def agui_event_types_defined(self):
        """All AG-UI event types are defined."""
        try:
            from agent.task_ui import AGUIEventType

            return {
                "run_started": AGUIEventType.RUN_STARTED.value == "RUN_STARTED",
                "text_message": AGUIEventType.TEXT_MESSAGE.value == "TEXT_MESSAGE",
                "tool_call_start": AGUIEventType.TOOL_CALL_START.value == "TOOL_CALL_START",
                "tool_call_end": AGUIEventType.TOOL_CALL_END.value == "TOOL_CALL_END",
                "state_delta": AGUIEventType.STATE_DELTA.value == "STATE_DELTA",
                "run_finished": AGUIEventType.RUN_FINISHED.value == "RUN_FINISHED",
                "run_error": AGUIEventType.RUN_ERROR.value == "RUN_ERROR"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Status Defined")
    def task_status_defined(self):
        """All task status values are defined."""
        try:
            from agent.task_ui import TaskStatus

            return {
                "pending": TaskStatus.PENDING.value == "pending",
                "running": TaskStatus.RUNNING.value == "running",
                "completed": TaskStatus.COMPLETED.value == "completed",
                "failed": TaskStatus.FAILED.value == "failed",
                "cancelled": TaskStatus.CANCELLED.value == "cancelled"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # AGUIEvent Tests
    # =========================================================================

    @keyword("AGUI Event Creation")
    def agui_event_creation(self):
        """AGUIEvent can be created with required fields."""
        try:
            from agent.task_ui import AGUIEvent, AGUIEventType

            event = AGUIEvent(
                type=AGUIEventType.RUN_STARTED,
                run_id="TASK-12345678"
            )

            return {
                "type_correct": event.type == AGUIEventType.RUN_STARTED,
                "run_id_correct": event.run_id == "TASK-12345678",
                "timestamp_exists": event.timestamp is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("AGUI Event With Data")
    def agui_event_with_data(self):
        """AGUIEvent can include data payload."""
        try:
            from agent.task_ui import AGUIEvent, AGUIEventType

            event = AGUIEvent(
                type=AGUIEventType.TEXT_MESSAGE,
                run_id="TASK-12345678",
                data={"role": "assistant", "content": "Hello!"}
            )

            return {
                "data_role": event.data["role"] == "assistant",
                "data_content": event.data["content"] == "Hello!"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("AGUI Event To SSE")
    def agui_event_to_sse(self):
        """AGUIEvent converts to SSE format correctly."""
        try:
            from agent.task_ui import AGUIEvent, AGUIEventType

            event = AGUIEvent(
                type=AGUIEventType.RUN_STARTED,
                run_id="TASK-12345678",
                data={"agent": "orchestrator"}
            )

            sse = event.to_sse()

            # Parse JSON payload
            if not sse.startswith("data: ") or not sse.endswith("\n\n"):
                return {"sse_format_valid": False}

            json_str = sse[6:-2]  # Remove "data: " prefix and "\n\n" suffix
            payload = json.loads(json_str)

            return {
                "starts_with_data": sse.startswith("data: "),
                "ends_with_newlines": sse.endswith("\n\n"),
                "type_correct": payload["type"] == "RUN_STARTED",
                "run_id_correct": payload["runId"] == "TASK-12345678",
                "agent_correct": payload["agent"] == "orchestrator",
                "has_timestamp": "timestamp" in payload
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"sse_format_valid": False}

    # =========================================================================
    # SSE Format Tests
    # =========================================================================

    @keyword("SSE Format Valid")
    def sse_format_valid(self):
        """SSE format is valid per specification."""
        try:
            from agent.task_ui import AGUIEvent, AGUIEventType

            event = AGUIEvent(
                type=AGUIEventType.TEXT_MESSAGE,
                run_id="TASK-TEST",
                data={"content": "Hello"}
            )

            sse = event.to_sse()
            starts_with_data = sse.startswith("data: ")
            ends_with_newlines = sse.endswith("\n\n")

            json_part = sse[6:-2]
            parsed = json.loads(json_part)

            return {
                "starts_with_data": starts_with_data,
                "ends_with_newlines": ends_with_newlines,
                "has_type": "type" in parsed,
                "has_run_id": "runId" in parsed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("SSE Escapes Special Chars")
    def sse_escapes_special_chars(self):
        """SSE properly escapes special characters in JSON."""
        try:
            from agent.task_ui import AGUIEvent, AGUIEventType

            event = AGUIEvent(
                type=AGUIEventType.TEXT_MESSAGE,
                run_id="TASK-TEST",
                data={"content": "Hello\nWorld\twith\ttabs"}
            )

            sse = event.to_sse()
            json_part = sse[6:-2]
            parsed = json.loads(json_part)

            return {
                "contains_special_chars": "Hello\nWorld\twith\ttabs" in parsed["content"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
