"""
Route models for Sarvaja URI routing.

Per FEAT-008: Named URI routing for dashboard navigation.
Per SRP: Models are pure data — no behavior beyond properties.

URI scheme:
    #/projects/{project_id}/{entity}/{entity_id}
    #/{standalone_view}
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass(frozen=True)
class RouteState:
    """Immutable representation of a parsed URI route.

    Attributes:
        view: The active view name (e.g., 'tasks', 'sessions', 'executive').
        sub_view: Optional nested view (e.g., 'reports' under 'tests').
        entity_id: Optional entity identifier for detail views.
        project_id: Optional project/workspace context.
    """

    view: str
    sub_view: Optional[str] = None
    entity_id: Optional[str] = None
    project_id: Optional[str] = None

    @property
    def is_detail(self) -> bool:
        """True when this route points to a specific entity."""
        return self.entity_id is not None


@dataclass(frozen=True)
class RouteConfig:
    """Configuration for a single routable view.

    Attributes:
        view_name: Internal view identifier (matches active_view state).
        uri_segment: URL path segment for this view.
        has_detail: Whether this view supports entity detail pages.
        standalone: Whether this view can appear without project context.
        sub_views: Optional mapping of sub_view_name → uri_segment.
    """

    view_name: str
    uri_segment: str
    has_detail: bool = False
    standalone: bool = False
    sub_views: Optional[Dict[str, str]] = field(default=None)
