"""
Route parser — converts URL hash strings to RouteState.

Per FEAT-008: Named URI routing for dashboard navigation.
Per SRP: Only parsing logic, no building or state management.

Supported patterns:
    #/projects/{project_id}/{view}/{entity_id}    → entity detail
    #/projects/{project_id}/{view}                → entity list
    #/projects/{project_id}/{view}/{sub}/{id}     → nested detail
    #/{view}                                      → standalone view
    #/projects                                    → projects list
"""

from .models import RouteState
from .registry import RouteRegistry

_DEFAULT_VIEW = "rules"
_registry = RouteRegistry()


def parse_hash(url_hash: str) -> RouteState:
    """Parse a URL hash fragment into a RouteState.

    Args:
        url_hash: The hash string, e.g. '#/projects/WS-123/tasks/FEAT-008'.
                  May or may not include the '#' prefix.

    Returns:
        RouteState with parsed view, entity_id, project_id, etc.
        Returns default route (rules list) for empty or invalid hashes.
    """
    path = _normalize_path(url_hash)
    segments = [s for s in path.split("/") if s]

    if not segments:
        return RouteState(view=_DEFAULT_VIEW)

    # Pattern: /projects/{project_id}/{view}/...
    if segments[0] == "projects":
        return _parse_project_path(segments[1:])

    # Pattern: /{standalone_view}
    return _parse_standalone(segments[0])


def _normalize_path(url_hash: str) -> str:
    """Strip '#' prefix and trailing slash."""
    path = url_hash.lstrip("#")
    return path.rstrip("/")


def _parse_project_path(segments: list) -> RouteState:
    """Parse segments after 'projects/'.

    Handles:
        []                           → projects list
        [{project_id}]               → projects list (with context — treat as list)
        [{project_id}, {view}]       → entity list
        [{project_id}, {view}, {id}] → entity detail
        [{project_id}, {view}, {sub}, {id}] → nested detail
    """
    if not segments:
        return RouteState(view="projects")

    project_id = segments[0]

    # Only project_id, no view segment — check if it's a known view
    if len(segments) == 1:
        if _registry.is_known_view(project_id):
            # Ambiguous: #/projects/{view_name} — treat as standalone view
            return _parse_standalone(project_id)
        return RouteState(view="projects", project_id=project_id)

    view_segment = segments[1]
    view_name = _registry.get_view_by_segment(view_segment)
    if view_name is None:
        return RouteState(view=_DEFAULT_VIEW)

    config = _registry.get_config(view_name)

    # Check for nested sub_view: /tests/reports/{id}
    if config and config.sub_views and len(segments) >= 3:
        potential_sub = segments[2]
        if potential_sub in config.sub_views:
            entity_id = segments[3] if len(segments) >= 4 else None
            return RouteState(
                view=view_name,
                sub_view=potential_sub,
                entity_id=entity_id,
                project_id=project_id,
            )

    # Entity detail: /projects/{id}/{view}/{entity_id}
    if len(segments) >= 3:
        # Remaining segments after view are the entity_id
        # Join in case entity_id contains slashes (shouldn't, but defensive)
        entity_id = "/".join(segments[2:])
        return RouteState(
            view=view_name,
            entity_id=entity_id,
            project_id=project_id,
        )

    # Entity list: /projects/{id}/{view}
    return RouteState(view=view_name, project_id=project_id)


def _parse_standalone(segment: str) -> RouteState:
    """Parse a standalone view segment."""
    view_name = _registry.get_view_by_segment(segment)
    if view_name is None:
        return RouteState(view=_DEFAULT_VIEW)
    return RouteState(view=view_name)
