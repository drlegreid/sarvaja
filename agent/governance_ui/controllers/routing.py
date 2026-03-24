"""
Routing controller — wires RouteSyncBridge into Trame dashboard.

Per FEAT-008: Named URI routing for dashboard navigation.
Per SRVJ-FEAT-015: Same-view deep link entity loading.
Per SRP: Only routing-related controller registration.

Responsibilities:
    1. On state change (active_view, show_*_detail) → push hash to browser
    2. On hashchange (browser back/forward) → update state from hash
    3. On same-view hashchange → load entity directly (on_view_change won't fire)
    4. On initial load → parse current hash and navigate
"""

import logging
from typing import Any, Optional

from agent.governance_ui.routing.sync import RouteSyncBridge
from agent.governance_ui.state.constants import DEFAULT_WORKSPACE_ID

logger = logging.getLogger(__name__)


def _load_entity_for_deep_link(
    state: Any, api_base_url: str, view: str, entity_id: str,
) -> None:
    """Load an entity from API for deep link / same-view navigation.

    Called when on_route_change detects a same-view detail navigation
    (e.g., #/tasks → #/tasks/BUG-012) where on_view_change won't fire.

    Args:
        state: Trame state object.
        api_base_url: REST API base URL (e.g., http://localhost:8082).
        view: Target view name ('tasks', 'sessions', etc.).
        entity_id: Entity ID to load from API.
    """
    from agent.governance_ui.controllers.tasks_navigation import (
        _load_session_from_api, _load_task_from_api,
    )

    if view == "tasks":
        data = _load_task_from_api(api_base_url, entity_id)
        if data:
            state.selected_task = data
            state.show_task_detail = True
        else:
            state.show_task_detail = False
            state.has_error = True
            state.error_message = f"Task {entity_id} not found"
    elif view == "sessions":
        data = _load_session_from_api(api_base_url, entity_id)
        if data:
            state.selected_session = data
            state.show_session_detail = True
        else:
            state.show_session_detail = False
            state.has_error = True
            state.error_message = f"Session {entity_id} not found"


def register_routing_controller(
    state: Any, ctrl: Any, api_base_url: Optional[str] = None,
) -> RouteSyncBridge:
    """Register routing controller with Trame server.

    Args:
        state: Trame state object.
        ctrl: Trame controller object.
        api_base_url: REST API URL for deep link entity loading.

    Returns:
        The RouteSyncBridge instance for use by other controllers.
    """
    bridge = RouteSyncBridge(default_project_id=DEFAULT_WORKSPACE_ID)

    @ctrl.trigger("on_route_change")
    def on_route_change(url_hash: str):
        """Handle browser hashchange (back/forward navigation).

        Per SRVJ-FEAT-015: When the view doesn't change (same-view nav),
        on_view_change won't fire, so we must load the entity directly.
        When the view changes, on_view_change handles it via _pending_entity_id.
        """
        prev_view = getattr(state, "active_view", "rules")

        logger.debug("Route change from browser: %s (prev=%s)", url_hash, prev_view)
        bridge.hash_to_state(url_hash, state)

        new_view = getattr(state, "active_view", "rules")
        pending_id = getattr(state, "_pending_entity_id", None)

        if prev_view == new_view:
            # Same-view navigation — on_view_change won't fire.
            # Must handle entity loading + route sync here.
            state._pending_entity_id = None
            if pending_id and api_base_url:
                _load_entity_for_deep_link(state, api_base_url, new_view, pending_id)
            # Sync route_hash so JS polling doesn't overwrite browser hash
            state.route_hash = bridge.state_to_hash(state)

    @ctrl.trigger("push_route")
    def push_route():
        """Push current state to browser URL hash via reactive state."""
        state.route_hash = bridge.state_to_hash(state)

    return bridge
