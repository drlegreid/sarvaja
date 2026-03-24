"""
Route registry — single source of truth for view ↔ URI mappings.

Per FEAT-008: Named URI routing for dashboard navigation.
Per DRY: All route definitions in one place.
"""

from typing import Dict, List, Optional, Set

from .models import RouteConfig


# Entity views: support list + detail, require project context
_ENTITY_VIEWS: List[RouteConfig] = [
    RouteConfig(view_name="tasks", uri_segment="tasks", has_detail=True),
    RouteConfig(view_name="sessions", uri_segment="sessions", has_detail=True),
    RouteConfig(view_name="rules", uri_segment="rules", has_detail=True),
    RouteConfig(view_name="agents", uri_segment="agents", has_detail=True),
    RouteConfig(view_name="decisions", uri_segment="decisions", has_detail=True),
    RouteConfig(view_name="workspaces", uri_segment="workspaces", has_detail=True),
]

# Standalone views: no entity detail, no project context required
_STANDALONE_VIEWS: List[RouteConfig] = [
    RouteConfig(view_name="executive", uri_segment="executive", standalone=True),
    RouteConfig(view_name="monitor", uri_segment="monitor", standalone=True),
    RouteConfig(view_name="workflow", uri_segment="workflow", standalone=True),
    RouteConfig(view_name="chat", uri_segment="chat", standalone=True),
    RouteConfig(view_name="impact", uri_segment="impact", standalone=True),
    RouteConfig(view_name="trust", uri_segment="trust", standalone=True),
    RouteConfig(view_name="audit", uri_segment="audit", standalone=True),
    RouteConfig(view_name="infra", uri_segment="infra", standalone=True),
    RouteConfig(view_name="metrics", uri_segment="metrics", standalone=True),
    RouteConfig(
        view_name="tests",
        uri_segment="tests",
        standalone=True,
        sub_views={"reports": "reports"},
    ),
    RouteConfig(view_name="projects", uri_segment="projects", standalone=True),
]


class RouteRegistry:
    """Central registry mapping view names to URI segments.

    Thread-safe: config is built once at init, then read-only.
    """

    def __init__(self) -> None:
        self._by_view: Dict[str, RouteConfig] = {}
        self._by_segment: Dict[str, str] = {}  # segment → view_name
        for config in _ENTITY_VIEWS + _STANDALONE_VIEWS:
            self._by_view[config.view_name] = config
            self._by_segment[config.uri_segment] = config.view_name

    def is_known_view(self, view_name: str) -> bool:
        """Check if a view name is registered."""
        return view_name in self._by_view

    def get_config(self, view_name: str) -> Optional[RouteConfig]:
        """Get RouteConfig for a view, or None if unknown."""
        return self._by_view.get(view_name)

    def get_segment(self, view_name: str) -> Optional[str]:
        """Get URI segment for a view name."""
        config = self._by_view.get(view_name)
        return config.uri_segment if config else None

    def get_view_by_segment(self, segment: str) -> Optional[str]:
        """Reverse lookup: URI segment → view name."""
        return self._by_segment.get(segment)

    def all_views(self) -> Set[str]:
        """Return all registered view names."""
        return set(self._by_view.keys())

    def entity_views(self) -> Set[str]:
        """Return views that support detail pages."""
        return {v for v, c in self._by_view.items() if c.has_detail}

    def standalone_views(self) -> Set[str]:
        """Return standalone views (no project context)."""
        return {v for v, c in self._by_view.items() if c.standalone}
