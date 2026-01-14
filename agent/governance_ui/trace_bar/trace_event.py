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

    # UI action fields
    action: Optional[str] = None  # click, input, navigate, etc.
    component: Optional[str] = None  # component name
    target: Optional[str] = None  # target element/view

    # Error fields
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "action": self.action,
            "component": self.component,
            "target": self.target,
            "error_message": self.error_message,
        }

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
