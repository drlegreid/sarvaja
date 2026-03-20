"""
Task Navigation Controllers.

Per DOC-SIZE-01-v1: Extracted from tasks.py (392 lines).
Cross-view navigation for tasks (navigate_to_task, navigate_back_to_source).
"""

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace


def register_tasks_navigation(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register task navigation controllers.

    Per UI-NAV-01-v1: Entity Navigation - preserve source for back button.
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

        # Capture navigation source for back button (UI-NAV-01-v1)
        if source_view:
            state.nav_source_view = source_view
            state.nav_source_id = source_id
            state.nav_source_label = source_label or f"Back to {source_view}"
        else:
            state.nav_source_view = None
            state.nav_source_id = None
            state.nav_source_label = None

        # Switch to tasks view + clear prior task state (BUG-UI-STALE-DETAIL-004)
        state.active_view = 'tasks'
        state.show_session_detail = False
        state.show_decision_detail = False
        state.edit_task_mode = False
        state.task_execution_log = []
        state.show_task_execution = False
        state.show_task_execution_inline = False  # BUG-TASK-POPUP-001

        # Try to find task in existing list
        found = False
        for task in state.tasks:
            if task.get('task_id') == task_id or task.get('id') == task_id:
                state.selected_task = task
                state.show_task_detail = True
                found = True
                break

        # If not found, try to load it from API
        if not found:
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if response.status_code == 200:
                        state.selected_task = response.json()
                        state.show_task_detail = True
                    else:
                        state.error_message = f"Task {task_id} not found"
            except Exception as e:
                add_error_trace(state, f"Navigate to task failed: {e}", f"/api/tasks/{task_id}")
                state.error_message = f"Failed to load task {task_id}"

    @ctrl.trigger("navigate_back_to_source")
    def navigate_back_to_source():
        """Navigate back to the source entity (UI-NAV-01-v1)."""
        source_view = state.nav_source_view
        source_id = state.nav_source_id

        # Clear current detail view
        state.show_task_detail = False
        state.selected_task = None

        # Clear navigation context
        state.nav_source_view = None
        state.nav_source_id = None
        state.nav_source_label = None

        if source_view == 'sessions' and source_id:
            state.active_view = 'sessions'
            for session in state.sessions:
                sid = session.get('session_id') or session.get('id')
                if sid == source_id:
                    state.selected_session = session
                    state.show_session_detail = True
                    return
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/sessions/{source_id}")
                    if response.status_code == 200:
                        state.selected_session = response.json()
                        state.show_session_detail = True
            except Exception as e:
                add_error_trace(state, f"Navigate back to session failed: {e}", f"/api/sessions/{source_id}")
        elif source_view == 'rules' and source_id:
            state.active_view = 'rules'
            for rule in state.rules:
                rid = rule.get('rule_id') or rule.get('id')
                if rid == source_id:
                    state.selected_rule = rule
                    state.show_rule_detail = True
                    return
        elif source_view:
            state.active_view = source_view
