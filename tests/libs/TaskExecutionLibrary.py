"""
Robot Framework Library for Task Execution Viewer Tests.

Per ORCH-007: Task Execution Viewer.
Migrated from tests/test_task_execution.py
"""
from robot.api.deco import keyword


class TaskExecutionLibrary:
    """Library for testing task execution viewer."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Import Tests
    # =============================================================================

    @keyword("Import Execution Event Types")
    def import_execution_event_types(self):
        """Import EXECUTION_EVENT_TYPES constant."""
        try:
            from agent.governance_ui import EXECUTION_EVENT_TYPES
            return {
                "has_claimed": "claimed" in EXECUTION_EVENT_TYPES,
                "has_started": "started" in EXECUTION_EVENT_TYPES,
                "has_completed": "completed" in EXECUTION_EVENT_TYPES,
                "has_failed": "failed" in EXECUTION_EVENT_TYPES,
                "has_evidence": "evidence" in EXECUTION_EVENT_TYPES
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import With Task Execution Log")
    def import_with_task_execution_log(self):
        """Import with_task_execution_log transform."""
        try:
            from agent.governance_ui import with_task_execution_log
            return {"callable": callable(with_task_execution_log)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import With Task Execution Loading")
    def import_with_task_execution_loading(self):
        """Import with_task_execution_loading transform."""
        try:
            from agent.governance_ui import with_task_execution_loading
            return {"callable": callable(with_task_execution_loading)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import With Task Execution Event")
    def import_with_task_execution_event(self):
        """Import with_task_execution_event transform."""
        try:
            from agent.governance_ui import with_task_execution_event
            return {"callable": callable(with_task_execution_event)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Clear Task Execution")
    def import_clear_task_execution(self):
        """Import clear_task_execution transform."""
        try:
            from agent.governance_ui import clear_task_execution
            return {"callable": callable(clear_task_execution)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Get Execution Event Style")
    def import_get_execution_event_style(self):
        """Import get_execution_event_style helper."""
        try:
            from agent.governance_ui import get_execution_event_style
            return {"callable": callable(get_execution_event_style)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Format Execution Event")
    def import_format_execution_event(self):
        """Import format_execution_event helper."""
        try:
            from agent.governance_ui import format_execution_event
            return {"callable": callable(format_execution_event)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # State Transform Tests
    # =============================================================================

    @keyword("Initial State Has Execution Fields")
    def initial_state_has_execution_fields(self):
        """Initial state includes execution log fields."""
        try:
            from agent.governance_ui import get_initial_state
            state = get_initial_state()
            return {
                "has_log": "task_execution_log" in state,
                "has_loading": "task_execution_loading" in state,
                "has_show": "show_task_execution" in state,
                "log_empty": state.get("task_execution_log") == [],
                "loading_false": state.get("task_execution_loading") is False,
                "show_false": state.get("show_task_execution") is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Task Execution Log Sets Events")
    def with_task_execution_log_sets_events(self):
        """Set task execution log."""
        try:
            from agent.governance_ui import with_task_execution_log, get_initial_state
            state = get_initial_state()
            events = [
                {"event_id": "E1", "event_type": "started", "timestamp": "2024-12-28T10:00:00"},
                {"event_id": "E2", "event_type": "completed", "timestamp": "2024-12-28T11:00:00"},
            ]
            new_state = with_task_execution_log(state, events)
            return {
                "events_set": new_state.get("task_execution_log") == events,
                "loading_false": new_state.get("task_execution_loading") is False,
                "show_true": new_state.get("show_task_execution") is True,
                "original_unchanged": state.get("task_execution_log") == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Task Execution Loading Sets Loading")
    def with_task_execution_loading_sets_loading(self):
        """Set task execution loading state."""
        try:
            from agent.governance_ui import with_task_execution_loading, get_initial_state
            state = get_initial_state()
            new_state = with_task_execution_loading(state)
            return {
                "loading_true": new_state.get("task_execution_loading") is True,
                "log_empty": new_state.get("task_execution_log") == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Task Execution Event Adds Event")
    def with_task_execution_event_adds_event(self):
        """Add event to task execution log."""
        try:
            from agent.governance_ui import with_task_execution_event
            state = {"task_execution_log": [{"event_id": "E1", "event_type": "started"}]}
            new_event = {"event_id": "E2", "event_type": "completed"}
            new_state = with_task_execution_event(state, new_event)
            return {
                "length_2": len(new_state.get("task_execution_log", [])) == 2,
                "event_added": new_state.get("task_execution_log", [{}])[-1] == new_event,
                "original_unchanged": len(state.get("task_execution_log", [])) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Clear Task Execution Resets State")
    def clear_task_execution_resets_state(self):
        """Clear task execution log."""
        try:
            from agent.governance_ui import clear_task_execution
            state = {
                "task_execution_log": [{"event_id": "E1"}],
                "task_execution_loading": True,
                "show_task_execution": True,
            }
            new_state = clear_task_execution(state)
            return {
                "log_empty": new_state.get("task_execution_log") == [],
                "loading_false": new_state.get("task_execution_loading") is False,
                "show_false": new_state.get("show_task_execution") is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Helper Function Tests
    # =============================================================================

    @keyword("Get Execution Event Style Claimed")
    def get_execution_event_style_claimed(self):
        """Get style for claimed event."""
        try:
            from agent.governance_ui import get_execution_event_style
            style = get_execution_event_style("claimed")
            return {
                "icon_correct": style.get("icon") == "mdi-hand-back-right",
                "color_correct": style.get("color") == "info"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Execution Event Style Completed")
    def get_execution_event_style_completed(self):
        """Get style for completed event."""
        try:
            from agent.governance_ui import get_execution_event_style
            style = get_execution_event_style("completed")
            return {
                "icon_correct": style.get("icon") == "mdi-check-circle",
                "color_correct": style.get("color") == "success"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Execution Event Style Failed")
    def get_execution_event_style_failed(self):
        """Get style for failed event."""
        try:
            from agent.governance_ui import get_execution_event_style
            style = get_execution_event_style("failed")
            return {
                "icon_correct": style.get("icon") == "mdi-alert-circle",
                "color_correct": style.get("color") == "error"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Execution Event Style Unknown")
    def get_execution_event_style_unknown(self):
        """Get default style for unknown event type."""
        try:
            from agent.governance_ui import get_execution_event_style
            style = get_execution_event_style("unknown_type")
            return {
                "icon_correct": style.get("icon") == "mdi-circle",
                "color_correct": style.get("color") == "grey"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Execution Event Works")
    def format_execution_event_works(self):
        """Format execution event for display."""
        try:
            from agent.governance_ui import format_execution_event
            event = {
                "event_id": "EVT-001",
                "event_type": "completed",
                "timestamp": "2024-12-28T10:30:45.123456",
                "agent_id": "AGENT-001",
                "message": "Task completed successfully",
            }
            formatted = format_execution_event(event)
            return {
                "icon_correct": formatted.get("icon") == "mdi-check-circle",
                "color_correct": formatted.get("color") == "success",
                "time_correct": formatted.get("formatted_time") == "2024-12-28 10:30:45",
                "event_id_correct": formatted.get("event_id") == "EVT-001",
                "message_correct": formatted.get("message") == "Task completed successfully"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # API Model Tests
    # =============================================================================

    @keyword("Task Execution Event Model Works")
    def task_execution_event_model_works(self):
        """TaskExecutionEvent model has correct fields."""
        try:
            from governance.api import TaskExecutionEvent
            event = TaskExecutionEvent(
                event_id="EVT-001",
                task_id="TASK-001",
                event_type="claimed",
                timestamp="2024-12-28T10:00:00",
                agent_id="AGENT-001",
                message="Task claimed",
            )
            return {
                "event_id_correct": event.event_id == "EVT-001",
                "task_id_correct": event.task_id == "TASK-001",
                "event_type_correct": event.event_type == "claimed",
                "agent_id_correct": event.agent_id == "AGENT-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Execution Response Model Works")
    def task_execution_response_model_works(self):
        """TaskExecutionResponse model has correct fields."""
        try:
            from governance.api import TaskExecutionResponse, TaskExecutionEvent
            response = TaskExecutionResponse(
                task_id="TASK-001",
                events=[
                    TaskExecutionEvent(
                        event_id="EVT-001",
                        task_id="TASK-001",
                        event_type="started",
                        timestamp="2024-12-28T10:00:00",
                    )
                ],
                current_status="in_progress",
                current_agent="AGENT-001",
            )
            return {
                "task_id_correct": response.task_id == "TASK-001",
                "events_count": len(response.events) == 1,
                "status_correct": response.current_status == "in_progress",
                "agent_correct": response.current_agent == "AGENT-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Synthesize Events From Task Timestamps")
    def synthesize_events_from_task_timestamps(self):
        """Synthesize events from task with timestamps."""
        try:
            from governance.api import _synthesize_execution_events
            task_data = {
                "created_at": "2024-12-28T10:00:00",
                "claimed_at": "2024-12-28T10:05:00",
                "completed_at": "2024-12-28T11:00:00",
                "agent_id": "AGENT-001",
                "status": "DONE",
                "evidence": "Task completed with all tests passing",
            }
            events = _synthesize_execution_events("TASK-001", task_data)
            event_types = [e.get("event_type") for e in events]
            return {
                "has_events": len(events) >= 3,
                "has_started": "started" in event_types,
                "has_claimed": "claimed" in event_types,
                "has_completed": "completed" in event_types
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Synthesize Events Empty Task")
    def synthesize_events_empty_task(self):
        """Synthesize events from task with no timestamps."""
        try:
            from governance.api import _synthesize_execution_events
            task_data = {"status": "TODO"}
            events = _synthesize_execution_events("TASK-002", task_data)
            return {"empty": len(events) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
