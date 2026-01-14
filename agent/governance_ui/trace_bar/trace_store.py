"""
Trace Store Data Class.

Per GAP-UI-048: Bottom bar with technical traces.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Created: 2026-01-14
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .trace_event import TraceEvent, TraceType


@dataclass
class TraceStore:
    """
    Store for managing trace events.

    Maintains a bounded list of trace events with filtering support.
    """
    events: List[TraceEvent] = field(default_factory=list)
    max_events: int = 100
    filter_type: Optional[TraceType] = None

    def add_event(self, event: TraceEvent) -> None:
        """Add a trace event, maintaining max_events limit."""
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def get_filtered_events(self) -> List[TraceEvent]:
        """Get events filtered by current filter_type."""
        if self.filter_type is None:
            return self.events
        return [e for e in self.events if e.event_type == self.filter_type]

    def clear(self) -> None:
        """Clear all events."""
        self.events = []

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "events": [e.to_dict() for e in self.events],
            "max_events": self.max_events,
            "filter_type": self.filter_type.value if self.filter_type else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraceStore":
        """Create TraceStore from dictionary."""
        events = [TraceEvent.from_dict(e) for e in data.get("events", [])]
        filter_type = None
        if data.get("filter_type"):
            try:
                filter_type = TraceType(data["filter_type"])
            except ValueError:
                pass

        return cls(
            events=events,
            max_events=data.get("max_events", 100),
            filter_type=filter_type,
        )

    @property
    def event_count(self) -> int:
        """Get total event count."""
        return len(self.events)

    @property
    def error_count(self) -> int:
        """Get error event count."""
        return sum(1 for e in self.events if e.is_error)

    @property
    def api_call_count(self) -> int:
        """Get API call count."""
        return sum(1 for e in self.events if e.event_type == TraceType.API_CALL)

    @property
    def last_event(self) -> Optional[TraceEvent]:
        """Get most recent event."""
        return self.events[-1] if self.events else None

    def get_summary(self) -> dict:
        """Get summary statistics."""
        return {
            "total": self.event_count,
            "errors": self.error_count,
            "api_calls": self.api_call_count,
            "ui_actions": sum(1 for e in self.events if e.event_type == TraceType.UI_ACTION),
            "last_event": self.last_event.format_display() if self.last_event else None,
        }


def get_initial_trace_state() -> Dict[str, Any]:
    """
    Get initial trace bar state.

    Returns dictionary for use in Trame state initialization.
    """
    return {
        # Trace bar visibility
        "trace_bar_visible": True,
        "trace_bar_expanded": False,

        # Trace events
        "trace_events": [],
        "trace_events_count": 0,
        "trace_error_count": 0,

        # Filter
        "trace_filter": None,  # 'api_call', 'ui_action', 'error', or None

        # Summary (for collapsed view)
        "trace_last_event": None,
        "trace_summary": {
            "total": 0,
            "errors": 0,
            "api_calls": 0,
            "ui_actions": 0,
        },
    }
