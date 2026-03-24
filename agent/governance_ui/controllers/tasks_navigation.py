"""
Task Navigation Controllers.

Per DOC-SIZE-01-v1: Extracted from tasks.py (392 lines).
Cross-view navigation for tasks (navigate_to_task, navigate_back_to_source).
Per BUG-012: Cross-nav guard prevents on_view_change from wiping navigation state.
Per FEAT-008: Push route hash after cross-view navigation.
"""

import logging
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace

logger = logging.getLogger(__name__)


def _load_session_from_api(api_base_url: str, session_id: str):
    """Load a session from REST API. Returns dict or None."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_base_url}/api/sessions/{session_id}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.warning("Session API load failed for %s: %s", session_id, e)
    return None


def _load_task_from_api(api_base_url: str, task_id: str):
    """Load a task from REST API. Returns dict or None."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_base_url}/api/tasks/{task_id}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.warning("Task API load failed for %s: %s", task_id, e)
    return None


def register_tasks_navigation(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register task navigation controllers.

    Per UI-NAV-01-v1: Entity Navigation - preserve source for back button.
    Per BUG-012: Sets cross_nav_in_progress guard before changing active_view
    so that on_view_change skips its destructive reset of detail flags.
    """

    @ctrl.trigger("navigate_to_task")
    def navigate_to_task(task_id, source_view=None, source_id=None, source_label=None):
        """Navigate to task from another view (e.g., session detail).

        Args:
            task_id: Task to navigate to
            source_view: View we came from ('sessions', 'rules', etc.)
            source_id: ID of source entity (session_id, rule_id, etc.)
            source_label: Human-readable label for back button
        """
        if not task_id:
            return

        # Load entity BEFORE changing view (BUG-012: load-first pattern)
        task_data = None
        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                task_data = task
                break

        if not task_data:
            task_data = _load_task_from_api(api_base_url, task_id)

        if not task_data:
            state.error_message = f"Task {task_id} not found"
            add_error_trace(state, f"Task {task_id} not found", f"/api/tasks/{task_id}")
            return

        # Capture navigation source for back button (UI-NAV-01-v1)
        if source_view:
            state.nav_source_view = source_view
            state.nav_source_id = source_id
            state.nav_source_label = source_label or f"Back to {source_view}"
        else:
            state.nav_source_view = None
            state.nav_source_id = None
            state.nav_source_label = None

        # BUG-012: Guard flag — tells on_view_change to skip destructive reset
        state.cross_nav_in_progress = True

        # Switch to tasks view + set detail state
        state.active_view = 'tasks'
        state.show_session_detail = False
        state.show_decision_detail = False
        state.edit_task_mode = False
        state.task_execution_log = []
        state.show_task_execution = False
        state.show_task_execution_inline = False  # BUG-TASK-POPUP-001
        state.selected_task = task_data
        state.show_task_detail = True

    @ctrl.trigger("navigate_to_session")
    def navigate_to_session(session_id, source_view=None, source_id=None, source_label=None):
        """Navigate from task detail to session detail view. Phase 9d: Concern 1.

        Per BUG-012: Load session BEFORE changing active_view. If load fails,
        don't change view at all — show error inline instead of silent rollback.

        Args:
            session_id: Session to navigate to
            source_view: View we came from (typically 'tasks')
            source_id: Task ID for back navigation
            source_label: Human-readable label for back button
        """
        if not session_id:
            return

        # BUG-012: Load entity BEFORE changing view — if load fails, stay put
        session_data = None
        for session in state.sessions:
            sid = session.get('session_id') or session.get('id')
            if sid == session_id:
                session_data = session
                break

        if not session_data:
            session_data = _load_session_from_api(api_base_url, session_id)

        if not session_data:
            # Don't change view — show error on current view
            state.error_message = f"Session {session_id} not found"
            add_error_trace(
                state, f"Session {session_id} not found",
                f"/api/sessions/{session_id}",
            )
            return

        # Capture navigation source for back button (UI-NAV-01-v1)
        if source_view:
            state.nav_source_view = source_view
            state.nav_source_id = source_id
            state.nav_source_label = source_label or f"Back to {source_view}"

        # BUG-012: Guard flag — tells on_view_change to skip destructive reset
        state.cross_nav_in_progress = True

        # Switch to sessions view + set detail state
        state.active_view = 'sessions'
        state.show_task_detail = False
        state.selected_session = session_data
        state.show_session_detail = True

        # BUG-013: Force Trame reactivity after cross-view navigation.
        # BUG-012: Do NOT dirty('active_view') — it triggers on_view_change
        # a second time after the guard flag was already consumed.
        state.dirty('show_session_detail')
        state.dirty('show_task_detail')

    @ctrl.trigger("navigate_back_to_source")
    def navigate_back_to_source():
        """Navigate back to the source entity (UI-NAV-01-v1).

        Per BUG-012: Load source entity BEFORE changing view, use guard flag.
        """
        source_view = state.nav_source_view
        source_id = state.nav_source_id

        # Load source entity BEFORE changing view (BUG-012: load-first)
        entity_data = None
        target_view = source_view or 'tasks'

        if source_view == 'tasks' and source_id:
            for task in state.tasks:
                if task.get('task_id') == source_id or task.get('id') == source_id:
                    entity_data = task
                    break
            if not entity_data:
                entity_data = _load_task_from_api(api_base_url, source_id)
        elif source_view == 'sessions' and source_id:
            for session in state.sessions:
                sid = session.get('session_id') or session.get('id')
                if sid == source_id:
                    entity_data = session
                    break
            if not entity_data:
                entity_data = _load_session_from_api(api_base_url, source_id)
        elif source_view == 'rules' and source_id:
            for rule in state.rules:
                rid = rule.get('rule_id') or rule.get('id')
                if rid == source_id:
                    entity_data = rule
                    break

        # Clear ALL detail view states to prevent ghost views
        state.show_task_detail = False
        state.selected_task = None
        state.show_session_detail = False
        state.show_decision_detail = False
        state.edit_task_mode = False
        state.task_execution_log = []
        state.show_task_execution = False

        # Clear navigation context
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None

        # BUG-012: Guard flag — prevents on_view_change from re-clearing state
        state.cross_nav_in_progress = True

        state.active_view = target_view

        # Set detail state if entity was loaded
        if source_view == 'tasks' and entity_data:
            state.selected_task = entity_data
            state.show_task_detail = True
        elif source_view == 'sessions' and entity_data:
            state.selected_session = entity_data
            state.show_session_detail = True
        elif source_view == 'rules' and entity_data:
            state.selected_rule = entity_data
            state.show_rule_detail = True

        # Force reactivity — BUG-012: Do NOT dirty('active_view') to avoid
        # re-triggering on_view_change after guard consumed.
        state.dirty('show_task_detail')
        state.dirty('show_session_detail')
