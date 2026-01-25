"""
RF-004: Robot Framework Library for Trace Event.

Wraps agent/governance_ui/trace_bar/trace_event.py for Robot Framework tests.
Per GAP-UI-TRACE-001: Trace bar request params visibility.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TraceEventLibrary:
    """Robot Framework library for Trace Event functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _normalize_none(self, value):
        """Convert Robot Framework None string to Python None."""
        if value is None or value == "None" or value == "${None}":
            return None
        return value

    def create_api_call_event(
        self,
        message: str,
        endpoint: str,
        method: str = "GET",
        status_code: int = None,
        duration_ms: float = None,
        request_body: Dict = None,
        response_body: Dict = None,
        request_headers: Dict = None
    ) -> Dict[str, Any]:
        """Create an API call trace event and return its dict representation."""
        from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType

        # Normalize None values from Robot Framework
        endpoint = self._normalize_none(endpoint)

        kwargs = {
            "event_type": TraceType.API_CALL,
            "message": message,
            "endpoint": endpoint,
            "method": method,
        }
        if status_code is not None:
            kwargs["status_code"] = int(status_code)
        if duration_ms is not None:
            kwargs["duration_ms"] = float(duration_ms)
        if request_body is not None:
            kwargs["request_body"] = request_body
        if response_body is not None:
            kwargs["response_body"] = response_body
        if request_headers is not None:
            kwargs["request_headers"] = request_headers

        event = TraceEvent(**kwargs)
        return event.to_dict()

    def create_ui_action_event(
        self,
        message: str,
        action: str = None,
        component: str = None,
        target: str = None
    ) -> Dict[str, Any]:
        """Create a UI action trace event and return its dict representation."""
        from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType

        kwargs = {
            "event_type": TraceType.UI_ACTION,
            "message": message,
        }
        if action is not None:
            kwargs["action"] = action
        if component is not None:
            kwargs["component"] = component
        if target is not None:
            kwargs["target"] = target

        event = TraceEvent(**kwargs)
        return event.to_dict()

    def get_path(self, event_dict: Dict) -> Optional[str]:
        """Get path from event dict."""
        return event_dict.get("path")

    def get_query_params(self, event_dict: Dict) -> Optional[Dict]:
        """Get query_params from event dict."""
        return event_dict.get("query_params")

    def get_event_type(self, event_dict: Dict) -> str:
        """Get event_type from event dict."""
        return event_dict.get("event_type")

    def get_query_param(self, event_dict: Dict, key: str) -> Any:
        """Get specific query param value."""
        params = event_dict.get("query_params") or {}
        return params.get(key)
