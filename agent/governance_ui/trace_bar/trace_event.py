"""
Trace Event Data Classes.

Per GAP-UI-048: Bottom bar with technical traces.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Created: 2026-01-14
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class TraceType(str, Enum):
    """Trace event types."""
    API_CALL = "api_call"
    UI_ACTION = "ui_action"
    ERROR = "error"
    MCP_CALL = "mcp_call"


@dataclass
class TraceEvent:
    """
    Trace event for the bottom bar.

    Represents a single traceable event (API call, UI action, error, etc.)
    """
    event_type: TraceType
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # API call fields
    endpoint: Optional[str] = None
    method: str = "GET"
    status_code: Optional[int] = None
    duration_ms: int = 0
    request_body: Optional[dict] = None  # Request payload
    response_body: Optional[dict] = None  # Response payload (truncated if large)
    request_headers: Optional[dict] = None  # Request headers

    # UI action fields
    action: Optional[str] = None  # click, input, navigate, etc.
    component: Optional[str] = None  # component name
    target: Optional[str] = None  # target element/view

    # Error fields
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        # Parse query params from endpoint for display (GAP-UI-TRACE-001)
        path, query_params = self._parse_endpoint()

        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "path": path,  # Path without query string
            "query_params": query_params,  # Parsed query params
            "method": self.method,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "request_body": self.request_body,
            "response_body": self.response_body,
            "request_headers": self.request_headers,
            "action": self.action,
            "component": self.component,
            "target": self.target,
            "error_message": self.error_message,
        }

    def _parse_endpoint(self) -> tuple:
        """
        Parse endpoint into path and query params.

        Per GAP-UI-TRACE-001: Separate params for better visibility.

        Returns:
            Tuple of (path, query_params_dict)
        """
        if not self.endpoint:
            return (None, None)

        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.endpoint)
        path = parsed.path

        query_params = None
        if parsed.query:
            # Parse query string into dict
            query_params = {}
            for key, values in parse_qs(parsed.query).items():
                # parse_qs returns lists, simplify single values
                query_params[key] = values[0] if len(values) == 1 else values

        return (path, query_params)

    @classmethod
    def from_dict(cls, data: dict) -> "TraceEvent":
        """Create TraceEvent from dictionary."""
        event_type = TraceType(data.get("event_type", "api_call"))
        timestamp = datetime.now()
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            event_type=event_type,
            message=data.get("message", ""),
            timestamp=timestamp,
            event_id=data.get("event_id", str(uuid.uuid4())[:8]),
            endpoint=data.get("endpoint"),
            method=data.get("method", "GET"),
            status_code=data.get("status_code"),
            duration_ms=data.get("duration_ms", 0),
            request_body=data.get("request_body"),
            response_body=data.get("response_body"),
            request_headers=data.get("request_headers"),
            action=data.get("action"),
            component=data.get("component"),
            target=data.get("target"),
            error_message=data.get("error_message"),
        )

    def format_display(self) -> str:
        """Format event for display in trace bar."""
        time_str = self.timestamp.strftime("%H:%M:%S")

        if self.event_type == TraceType.API_CALL:
            status = "OK" if self.status_code and self.status_code < 400 else "ERR"
            return f"[{time_str}] {self.method} {self.endpoint} - {self.duration_ms}ms - {self.status_code} {status}"

        elif self.event_type == TraceType.UI_ACTION:
            return f"[{time_str}] UI: {self.action} on {self.component}"

        elif self.event_type == TraceType.ERROR:
            return f"[{time_str}] ERROR: {self.error_message or self.message}"

        elif self.event_type == TraceType.MCP_CALL:
            return f"[{time_str}] MCP: {self.message} - {self.duration_ms}ms"

        return f"[{time_str}] {self.message}"

    @property
    def is_error(self) -> bool:
        """Check if this is an error event."""
        if self.event_type == TraceType.ERROR:
            return True
        if self.status_code and self.status_code >= 400:
            return True
        return False

    @property
    def css_class(self) -> str:
        """Get CSS class for styling."""
        if self.is_error:
            return "trace-error"
        if self.event_type == TraceType.UI_ACTION:
            return "trace-ui-action"
        if self.event_type == TraceType.MCP_CALL:
            return "trace-mcp-call"
        return "trace-api-call"
