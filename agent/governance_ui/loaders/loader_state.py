"""
Loader State Data Classes.

Per GAP-UI-047: Reactive loaders with trace status.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Provides data structures for tracking:
- Loading status per component
- API call trace metadata
- Progress information

Created: 2026-01-14
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class APITrace:
    """
    API call trace metadata.

    Tracks endpoint, method, timing, and response for debugging/monitoring.
    """
    endpoint: str = ""
    method: str = "GET"
    status: str = "pending"  # pending, loading, success, error
    status_code: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    error_message: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "status": self.status,
            "status_code": self.status_code,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "request_id": self.request_id,
            "error_message": self.error_message,
        }


@dataclass
class ProgressInfo:
    """
    Progress information for paginated/streaming loads.

    Tracks items loaded and total expected for progress display.
    """
    progress_percent: int = 0
    items_loaded: int = 0
    total_items: Optional[int] = None
    current_page: int = 1
    total_pages: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "progress_percent": self.progress_percent,
            "items_loaded": self.items_loaded,
            "total_items": self.total_items,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
        }


@dataclass
class LoaderState:
    """
    Complete loading state for a component.

    Combines loading status, error tracking, trace metadata, and progress.
    """
    is_loading: bool = False
    has_error: bool = False
    error_message: str = ""
    trace: Optional[APITrace] = None
    progress: Optional[ProgressInfo] = None
    last_loaded: Optional[datetime] = None
    items_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "is_loading": self.is_loading,
            "has_error": self.has_error,
            "error_message": self.error_message,
            "trace": self.trace.to_dict() if self.trace else None,
            "progress": self.progress.to_dict() if self.progress else None,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "items_count": self.items_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoaderState":
        """Create LoaderState from dictionary."""
        trace = None
        if data.get("trace"):
            trace = APITrace(
                endpoint=data["trace"].get("endpoint", ""),
                method=data["trace"].get("method", "GET"),
                status=data["trace"].get("status", "pending"),
                status_code=data["trace"].get("status_code"),
                request_id=data["trace"].get("request_id", ""),
                error_message=data["trace"].get("error_message", ""),
            )

        progress = None
        if data.get("progress"):
            progress = ProgressInfo(
                progress_percent=data["progress"].get("progress_percent", 0),
                items_loaded=data["progress"].get("items_loaded", 0),
                total_items=data["progress"].get("total_items"),
            )

        return cls(
            is_loading=data.get("is_loading", False),
            has_error=data.get("has_error", False),
            error_message=data.get("error_message", ""),
            trace=trace,
            progress=progress,
            items_count=data.get("items_count", 0),
        )


# Component-specific loading states
COMPONENT_LOADERS = [
    "rules",
    "sessions",
    "decisions",
    "tasks",
    "backlog",
    "agents",
    "monitor",
    "executive",
    "chat",
    "file_viewer",
    "task_execution",
    "infra",
    "workflow",
    "evidence",
]


def get_initial_loader_states() -> dict:
    """
    Get initial loading states for all components.

    Returns dictionary of component_name -> LoaderState.to_dict()
    for use in Trame state initialization.
    """
    states = {}
    for component in COMPONENT_LOADERS:
        states[f"{component}_loader"] = LoaderState().to_dict()
        states[f"{component}_loading"] = False  # Shorthand for quick checks
    return states
