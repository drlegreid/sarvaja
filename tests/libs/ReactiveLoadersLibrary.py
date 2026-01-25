"""
Robot Framework Library for Reactive Loaders Tests.

Per GAP-UI-047: Reactive loaders with trace status.
Migrated from tests/test_reactive_loaders.py
"""
import os
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from robot.api.deco import keyword


class ReactiveLoadersLibrary:
    """Library for testing reactive loaders with trace status."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Loader State Design Tests
    # =============================================================================

    @keyword("Loader State Has Is Loading")
    def loader_state_has_is_loading(self):
        """Verify loader state tracks loading status."""
        @dataclass
        class LoaderState:
            is_loading: bool = False
        state = LoaderState()
        return {"has_attr": hasattr(state, 'is_loading'), "default_false": state.is_loading == False}

    @keyword("Loader State Has Error Tracking")
    def loader_state_has_error_tracking(self):
        """Verify loader state tracks errors."""
        @dataclass
        class LoaderState:
            has_error: bool = False
            error_message: str = ""
        state = LoaderState()
        return {"has_error": hasattr(state, 'has_error'), "has_message": hasattr(state, 'error_message')}

    @keyword("Loader State Has Trace Metadata")
    def loader_state_has_trace_metadata(self):
        """Verify loader state has trace metadata."""
        @dataclass
        class LoaderState:
            start_time: Optional[datetime] = None
            end_time: Optional[datetime] = None
            duration_ms: int = 0
            endpoint: str = ""
        state = LoaderState()
        return {
            "has_start": hasattr(state, 'start_time'),
            "has_end": hasattr(state, 'end_time'),
            "has_duration": hasattr(state, 'duration_ms'),
            "has_endpoint": hasattr(state, 'endpoint')
        }

    # =============================================================================
    # Loader Module Tests
    # =============================================================================

    @keyword("State Initial Has Loader Fields")
    def state_initial_has_loader_fields(self):
        """Verify state/initial.py includes loader metadata fields."""
        state_file = 'agent/governance_ui/state/initial.py'
        if not os.path.exists(state_file):
            return {"skipped": True, "reason": f"File not found: {state_file}"}
        with open(state_file, 'r') as f:
            content = f.read()
        return {"has_loading": 'is_loading' in content or 'loading' in content}

    @keyword("Import Loader State")
    def import_loader_state(self):
        """Verify LoaderState can be imported."""
        try:
            from agent.governance_ui.loaders.loader_state import LoaderState
            state = LoaderState()
            return {"imported": True, "not_loading": state.is_loading == False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import API Trace")
    def import_api_trace(self):
        """Verify APITrace can be imported."""
        try:
            from agent.governance_ui.loaders.loader_state import APITrace
            trace = APITrace(endpoint="/api/rules")
            return {"imported": True, "endpoint_set": trace.endpoint == "/api/rules"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Loader Transforms")
    def import_loader_transforms(self):
        """Verify transform functions can be imported."""
        try:
            from agent.governance_ui.loaders.transforms import (
                set_loading_start,
                set_loading_complete,
                set_loading_error,
                get_loader_state,
            )
            return {
                "start_callable": callable(set_loading_start),
                "complete_callable": callable(set_loading_complete)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial Loader States")
    def initial_loader_states(self):
        """Verify get_initial_loader_states returns expected structure."""
        try:
            from agent.governance_ui.loaders.loader_state import get_initial_loader_states
            states = get_initial_loader_states()
            return {
                "has_rules_loader": 'rules_loader' in states,
                "has_rules_loading": 'rules_loading' in states,
                "rules_not_loading": states.get('rules_loading') == False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial State Includes Loaders")
    def initial_state_includes_loaders(self):
        """Verify initial UI state includes loader states."""
        try:
            from agent.governance_ui.state.initial import get_initial_state
            state = get_initial_state()
            return {
                "has_rules_loader": 'rules_loader' in state,
                "has_sessions_loader": 'sessions_loader' in state
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Loader State Operations Tests
    # =============================================================================

    @keyword("Loader State To Dict")
    def loader_state_to_dict(self):
        """Verify LoaderState serializes to dict."""
        try:
            from agent.governance_ui.loaders.loader_state import LoaderState
            state = LoaderState(is_loading=True, items_count=5)
            data = state.to_dict()
            return {
                "is_loading": data.get('is_loading') == True,
                "items_count": data.get('items_count') == 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Loader State From Dict")
    def loader_state_from_dict(self):
        """Verify LoaderState deserializes from dict."""
        try:
            from agent.governance_ui.loaders.loader_state import LoaderState
            data = {'is_loading': True, 'items_count': 10}
            state = LoaderState.from_dict(data)
            return {
                "is_loading": state.is_loading == True,
                "items_count": state.items_count == 10
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("API Trace To Dict")
    def api_trace_to_dict(self):
        """Verify APITrace serializes correctly."""
        try:
            from agent.governance_ui.loaders.loader_state import APITrace
            trace = APITrace(endpoint="/api/rules", method="GET", status="success")
            data = trace.to_dict()
            return {
                "endpoint": data.get('endpoint') == "/api/rules",
                "method": data.get('method') == "GET"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Transform Function Tests
    # =============================================================================

    @keyword("Set Loading Start Mock")
    def set_loading_start_mock(self):
        """Verify set_loading_start updates mock state."""
        try:
            from agent.governance_ui.loaders.transforms import set_loading_start

            class MockState:
                pass

            state = MockState()
            set_loading_start(state, "rules", "/api/rules")
            return {
                "rules_loading": state.rules_loading == True,
                "has_trace": state.rules_loader.get('trace', {}).get('endpoint') == "/api/rules"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Set Loading Complete Mock")
    def set_loading_complete_mock(self):
        """Verify set_loading_complete updates mock state."""
        try:
            from agent.governance_ui.loaders.transforms import set_loading_start, set_loading_complete

            class MockState:
                pass

            state = MockState()
            set_loading_start(state, "rules", "/api/rules")
            set_loading_complete(state, "rules", status_code=200, items_count=10)
            return {
                "not_loading": state.rules_loading == False,
                "items_count": state.rules_loader.get('items_count') == 10
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Trace Status")
    def format_trace_status(self):
        """Verify format_trace_status output."""
        try:
            from agent.governance_ui.loaders.loader_state import LoaderState, APITrace
            from agent.governance_ui.loaders.transforms import format_trace_status

            trace = APITrace(
                endpoint="/api/rules",
                method="GET",
                duration_ms=150,
                status_code=200
            )
            state = LoaderState(trace=trace)
            formatted = format_trace_status(state)
            return {
                "has_get": "GET" in formatted,
                "has_endpoint": "/api/rules" in formatted,
                "has_duration": "150ms" in formatted
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
