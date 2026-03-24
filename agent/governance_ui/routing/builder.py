"""
Route builder — converts RouteState to URL hash strings.

Per FEAT-008: Named URI routing for dashboard navigation.
Per SRP: Only building logic, no parsing or state management.
"""

from .models import RouteState
from .registry import RouteRegistry

_registry = RouteRegistry()


def build_hash(route: RouteState) -> str:
    """Build a URL hash fragment from a RouteState.

    Args:
        route: The RouteState to convert.

    Returns:
        Hash string like '#/projects/WS-123/tasks/FEAT-008'.
    """
    config = _registry.get_config(route.view)
    if config is None:
        return "#/rules"

    segment = config.uri_segment

    # Special: projects list view
    if route.view == "projects" and not route.project_id and not route.entity_id:
        return "#/projects"

    # Standalone view (no project context, no entity)
    if not route.project_id and not route.entity_id:
        return f"#/{segment}"

    # Build with project context
    parts = ["#", "projects", route.project_id, segment]

    # Nested sub_view (e.g., tests/reports)
    if route.sub_view:
        parts.append(route.sub_view)

    # Entity detail
    if route.entity_id:
        parts.append(route.entity_id)

    return "/".join(parts)
