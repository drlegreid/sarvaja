"""
Route sync bridge — bidirectional state ↔ URL hash synchronization.

Per FEAT-008: Named URI routing for dashboard navigation.
Per SRP: Only sync logic between Trame state and URL.

State → URL:  When active_view / selected_* changes, push to browser hash.
URL → State:  When browser hash changes (back/forward), update Trame state.
"""

from typing import Any, Optional

from .models import RouteState
from .parser import parse_hash
from .builder import build_hash
from .registry import RouteRegistry

_registry = RouteRegistry()

# Maps view name → (selected_entity_attr, id_field_in_entity)
_ENTITY_ID_FIELDS = {
    "tasks": ("selected_task", "task_id"),
    "sessions": ("selected_session", "session_id"),
    "rules": ("selected_rule", "id"),
    "agents": ("selected_agent", "agent_id"),
    "decisions": ("selected_decision", "decision_id"),
    "workspaces": ("selected_workspace", "workspace_id"),
}

# Maps view name → show_*_detail flag name
_DETAIL_FLAGS = {
    "tasks": "show_task_detail",
    "sessions": "show_session_detail",
    "rules": "show_rule_detail",
    "agents": "show_agent_detail",
    "decisions": "show_decision_detail",
    "workspaces": "show_workspace_detail",
}


class RouteSyncBridge:
    """Bidirectional bridge between Trame state and URL hash.

    Attributes:
        default_project_id: Project ID used when state doesn't specify one.
    """

    def __init__(self, default_project_id: str = "WS-9147535A") -> None:
        self.default_project_id = default_project_id

    def state_to_hash(self, state: Any) -> str:
        """Convert current Trame state to a URL hash string.

        Reads active_view, show_*_detail, and selected_* to build the route.
        """
        view = getattr(state, "active_view", "rules") or "rules"
        config = _registry.get_config(view)

        if config is None:
            return "#/rules"

        # Standalone views — no project context
        if config.standalone and not config.has_detail:
            return f"#/{config.uri_segment}"

        # Determine if we're in a detail view
        entity_id = None
        detail_flag = self._detail_flag(view)
        if detail_flag and getattr(state, detail_flag, False):
            entity_attr, _ = _ENTITY_ID_FIELDS.get(view, (None, None))
            if entity_attr:
                entity = getattr(state, entity_attr, None)
                entity_id = self._extract_entity_id(view, entity)

        project_id = getattr(state, "current_project_id", None) or self.default_project_id

        route = RouteState(
            view=view,
            entity_id=entity_id,
            project_id=project_id,
        )
        return build_hash(route)

    def hash_to_state(self, url_hash: str, state: Any) -> None:
        """Apply a parsed URL hash to Trame state.

        Sets active_view and, for detail routes, sets the pending entity ID
        for the controller to load via API.
        """
        route = parse_hash(url_hash)

        state.active_view = route.view

        # Reset all detail flags
        for flag in _DETAIL_FLAGS.values():
            setattr(state, flag, False)

        # If detail route, flag it and store pending entity_id
        if route.is_detail:
            detail_flag = self._detail_flag(route.view)
            if detail_flag:
                setattr(state, detail_flag, True)
            # Store pending entity_id for controller to load
            state._pending_entity_id = route.entity_id
        else:
            state._pending_entity_id = None

    def _extract_entity_id(self, view: str, entity: Any) -> Optional[str]:
        """Extract the entity ID string from an entity object/dict.

        Args:
            view: The view name (determines which field to read).
            entity: The entity dict or object.

        Returns:
            Entity ID string or None.
        """
        if entity is None:
            return None
        if not isinstance(entity, dict):
            return None

        _, id_field = _ENTITY_ID_FIELDS.get(view, (None, None))
        if id_field is None:
            return None

        # Try primary field, then fallback to 'id'
        return entity.get(id_field) or entity.get("id")

    def _detail_flag(self, view: str) -> Optional[str]:
        """Get the show_*_detail flag name for a view.

        Returns None for views that don't have detail pages.
        """
        return _DETAIL_FLAGS.get(view)

    @staticmethod
    def generate_js_push(url_hash: str) -> str:
        """Generate JS code to push a hash to browser URL.

        This is called from Python to update the browser's address bar
        without triggering a page reload.
        """
        escaped = url_hash.replace("'", "\\'")
        return f"if (window.location.hash !== '{escaped}') {{ window.location.hash = '{escaped}'; }}"

    @staticmethod
    def generate_js_listener(trigger_name: str) -> str:
        """Generate JS code for a hashchange event listener.

        Args:
            trigger_name: The Trame trigger name to call on hash change.

        Returns:
            JS code that listens for hashchange and calls the trigger.
        """
        return (
            f"window.addEventListener('hashchange', function() {{"
            f" trame.trigger('{trigger_name}', [window.location.hash]);"
            f" }});"
        )
