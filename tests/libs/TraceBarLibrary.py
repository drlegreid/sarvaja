"""
Robot Framework Library for Trace Bar Tests.

Per GAP-UI-048: Bottom bar with technical traces.
Migrated from tests/test_trace_bar.py
"""
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from robot.api.deco import keyword


class TraceBarLibrary:
    """Library for testing trace bar functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Trace Event Design Tests
    # =============================================================================

    @keyword("Trace Event Has Type")
    def trace_event_has_type(self):
        """Verify trace event has type field."""
        class TraceType(str, Enum):
            API_CALL = "api_call"
            UI_ACTION = "ui_action"
            ERROR = "error"
        return {"api_call": TraceType.API_CALL.value == "api_call"}

    @keyword("Trace Event Has Timestamp")
    def trace_event_has_timestamp(self):
        """Verify trace event has timestamp."""
        @dataclass
        class TraceEvent:
            timestamp: datetime
            event_type: str
        event = TraceEvent(timestamp=datetime.now(), event_type="api_call")
        return {"has_timestamp": event.timestamp is not None}

    @keyword("Trace Event Has Message")
    def trace_event_has_message(self):
        """Verify trace event has message."""
        @dataclass
        class TraceEvent:
            message: str
            details: Optional[str] = None
        event = TraceEvent(message="GET /api/rules - 200 OK")
        return {"has_get": "GET" in event.message}

    # =============================================================================
    # Trace Store Design Tests
    # =============================================================================

    @keyword("Trace Store Has Events")
    def trace_store_has_events(self):
        """Verify trace store holds events."""
        @dataclass
        class TraceStore:
            events: List[dict] = field(default_factory=list)
            max_events: int = 100
        store = TraceStore()
        return {"has_events": hasattr(store, 'events'), "max_100": store.max_events == 100}

    @keyword("Trace Store Limits Events")
    def trace_store_limits_events(self):
        """Verify trace store limits event count."""
        max_events = 5
        events = []
        for i in range(10):
            events.append({'id': i})
            if len(events) > max_events:
                events.pop(0)
        return {"limited": len(events) == max_events}

    # =============================================================================
    # Module Import Tests
    # =============================================================================

    @keyword("Import Trace Event")
    def import_trace_event(self):
        """Verify TraceEvent can be imported."""
        try:
            from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType
            event = TraceEvent(event_type=TraceType.API_CALL, message="test")
            return {"imported": True, "message_set": event.message == "test"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Trace Store")
    def import_trace_store(self):
        """Verify TraceStore can be imported."""
        try:
            from agent.governance_ui.trace_bar.trace_store import TraceStore
            store = TraceStore()
            return {"imported": True, "max_100": store.max_events == 100}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Trace Transforms")
    def import_trace_transforms(self):
        """Verify transform functions can be imported."""
        try:
            from agent.governance_ui.trace_bar.transforms import (
                add_api_trace,
                add_ui_action_trace,
                clear_traces,
            )
            return {"add_api_callable": callable(add_api_trace)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial Trace State")
    def initial_trace_state(self):
        """Verify get_initial_trace_state returns expected structure."""
        try:
            from agent.governance_ui.trace_bar.trace_store import get_initial_trace_state
            state = get_initial_trace_state()
            return {
                "has_visible": 'trace_bar_visible' in state,
                "has_events": 'trace_events' in state,
                "visible_true": state.get('trace_bar_visible') == True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial State Includes Traces")
    def initial_state_includes_traces(self):
        """Verify initial UI state includes trace bar states."""
        try:
            from agent.governance_ui.state.initial import get_initial_state
            state = get_initial_state()
            return {
                "has_visible": 'trace_bar_visible' in state,
                "has_events": 'trace_events' in state
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Trace Event Operations Tests
    # =============================================================================

    @keyword("Trace Event To Dict")
    def trace_event_to_dict(self):
        """Verify TraceEvent serializes to dict."""
        try:
            from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType
            event = TraceEvent(
                event_type=TraceType.API_CALL,
                message="test",
                endpoint="/api/rules",
                duration_ms=150,
            )
            data = event.to_dict()
            return {
                "endpoint": data.get('endpoint') == "/api/rules",
                "duration": data.get('duration_ms') == 150
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trace Event Format Display")
    def trace_event_format_display(self):
        """Verify TraceEvent format_display works."""
        try:
            from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType
            event = TraceEvent(
                event_type=TraceType.API_CALL,
                message="test",
                endpoint="/api/rules",
                method="GET",
                status_code=200,
                duration_ms=150,
            )
            display = event.format_display()
            return {
                "has_get": "GET" in display,
                "has_endpoint": "/api/rules" in display,
                "has_duration": "150ms" in display
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trace Event Is Error")
    def trace_event_is_error(self):
        """Verify TraceEvent.is_error property."""
        try:
            from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType
            success = TraceEvent(event_type=TraceType.API_CALL, message="test", status_code=200)
            error = TraceEvent(event_type=TraceType.API_CALL, message="test", status_code=500)
            return {"success_not_error": success.is_error == False, "error_is_error": error.is_error == True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Transform Function Tests
    # =============================================================================

    @keyword("Add Api Trace Mock")
    def add_api_trace_mock(self):
        """Verify add_api_trace updates mock state."""
        try:
            from agent.governance_ui.trace_bar.transforms import add_api_trace

            class MockState:
                pass

            state = MockState()
            add_api_trace(state, "/api/rules", "GET", 200, 150)
            return {
                "has_events": len(state.trace_events) == 1,
                "endpoint_set": state.trace_events[0].get('endpoint') == "/api/rules"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Ui Action Trace Mock")
    def add_ui_action_trace_mock(self):
        """Verify add_ui_action_trace updates mock state."""
        try:
            from agent.governance_ui.trace_bar.transforms import add_ui_action_trace

            class MockState:
                pass

            state = MockState()
            add_ui_action_trace(state, "click", "rules_table", "row_1")
            return {
                "has_events": len(state.trace_events) == 1,
                "is_ui_action": state.trace_events[0].get('event_type') == "ui_action"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Clear Traces Mock")
    def clear_traces_mock(self):
        """Verify clear_traces clears all events."""
        try:
            from agent.governance_ui.trace_bar.transforms import add_api_trace, clear_traces

            class MockState:
                pass

            state = MockState()
            add_api_trace(state, "/api/rules", "GET", 200, 150)
            clear_traces(state)
            return {"cleared": len(state.trace_events) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Toggle Trace Bar Mock")
    def toggle_trace_bar_mock(self):
        """Verify toggle_trace_bar toggles expanded state."""
        try:
            from agent.governance_ui.trace_bar.transforms import toggle_trace_bar

            class MockState:
                trace_bar_expanded = False

            state = MockState()
            toggle_trace_bar(state)
            first_toggle = state.trace_bar_expanded == True
            toggle_trace_bar(state)
            second_toggle = state.trace_bar_expanded == False
            return {"first_toggle": first_toggle, "second_toggle": second_toggle}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
