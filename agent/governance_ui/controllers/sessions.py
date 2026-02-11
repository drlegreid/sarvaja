"""
Sessions Controllers (GAP-FILE-005)
===================================
Controller functions for session CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-034: Session CRUD operations
Per DOC-SIZE-01-v1: Pagination in sessions_pagination.py.

Created: 2024-12-28
Updated: 2026-01-02 (GAP-UI-034)
"""

import httpx
from typing import Any

from governance.middleware.dashboard_log import log_action
from .sessions_pagination import register_sessions_pagination  # noqa: F401


def register_sessions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register session-related controllers with Trame."""

    # Register pagination + filters; get load_sessions_page reference
    load_sessions_page = register_sessions_pagination(state, ctrl, api_base_url)

    @ctrl.trigger("select_session")
    def select_session(session_id):
        """Handle session selection for detail view."""
        log_action("sessions", "select", session_id=session_id)
        for session in state.sessions:
            if session.get('session_id') == session_id or session.get('id') == session_id:
                state.selected_session = session
                state.show_session_detail = True
                break

        try:
            resp = httpx.get(f"{api_base_url}/api/sessions/{session_id}", timeout=10.0)
            if resp.status_code == 200:
                state.selected_session = resp.json()
        except Exception:
            pass

        load_session_tasks(session_id)
        load_session_tool_calls(session_id)
        load_session_thinking_items(session_id)

    def load_session_tool_calls(session_id):
        """Load tool calls for a session. Per B.3."""
        if not session_id:
            return
        try:
            state.session_tool_calls = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions/{session_id}/tool_calls")
                if response.status_code == 200:
                    data = response.json()
                    state.session_tool_calls = data.get('tool_calls', [])
        except Exception:
            state.session_tool_calls = []

    def load_session_thinking_items(session_id):
        """Load thinking/reasoning items for a session. Per B.3."""
        if not session_id:
            return
        try:
            state.session_thinking_items = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions/{session_id}/thoughts")
                if response.status_code == 200:
                    data = response.json()
                    state.session_thinking_items = data.get('thoughts', [])
        except Exception:
            state.session_thinking_items = []

    def load_session_tasks(session_id):
        """Load tasks linked to a session."""
        if not session_id:
            return
        try:
            state.session_tasks_loading = True
            state.session_tasks = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions/{session_id}/tasks")
                if response.status_code == 200:
                    data = response.json()
                    state.session_tasks = data.get('tasks', [])
                else:
                    state.session_tasks = []
            state.session_tasks_loading = False
        except Exception as e:
            state.session_tasks_loading = False
            state.session_tasks = []
            state.error_message = f"Failed to load session tasks: {str(e)}"

    @ctrl.set("close_session_detail")
    def close_session_detail():
        """Close session detail view."""
        state.show_session_detail = False
        state.selected_session = None

    @ctrl.set("show_session_form")
    def show_session_form(mode="create"):
        """Show session create/edit form."""
        state.session_form_mode = mode
        if mode == "edit" and state.selected_session:
            state.form_session_id = state.selected_session.get('session_id') or state.selected_session.get('id', '')
            state.form_session_description = state.selected_session.get('description', '')
            state.form_session_status = state.selected_session.get('status', 'ACTIVE')
            state.form_session_agent_id = state.selected_session.get('agent_id', '')
        else:
            state.form_session_id = ''
            state.form_session_description = ''
            state.form_session_status = 'ACTIVE'
            state.form_session_agent_id = ''
        state.show_session_form = True

    @ctrl.set("close_session_form")
    def close_session_form():
        """Close session form."""
        state.show_session_form = False

    @ctrl.trigger("submit_session_form")
    def submit_session_form():
        """Submit session form (create/update) via REST API."""
        log_action("sessions", state.session_form_mode, session_id=state.form_session_id)
        try:
            state.is_loading = True
            session_data = {
                "session_id": state.form_session_id or None,
                "description": state.form_session_description,
                "agent_id": state.form_session_agent_id or None
            }

            with httpx.Client(timeout=10.0) as client:
                if state.session_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/sessions", json=session_data)
                else:
                    session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
                    update_data = {
                        "description": state.form_session_description,
                        "status": state.form_session_status,
                        "agent_id": state.form_session_agent_id or None
                    }
                    response = client.put(f"{api_base_url}/api/sessions/{session_id}", json=update_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Session {'created' if state.session_form_mode == 'create' else 'updated'} successfully"
                    load_sessions_page()
                else:
                    state.has_error = True
                    state.error_message = f"API Error: {response.status_code} - {response.text}"

            state.show_session_form = False
            state.show_session_detail = False
            state.selected_session = None
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to save session: {str(e)}"
            state.show_session_form = False
            state.status_message = f"Session saved (offline mode - API unavailable: {str(e)})"

    @ctrl.trigger("delete_session")
    def delete_session():
        """Delete selected session via REST API."""
        if not state.selected_session:
            return
        log_action("sessions", "delete", session_id=state.selected_session.get("session_id"))
        try:
            state.is_loading = True
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')

            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{api_base_url}/api/sessions/{session_id}")

                if response.status_code == 204:
                    state.status_message = f"Session {session_id} deleted successfully"
                    load_sessions_page()
                    state.show_session_detail = False
                    state.selected_session = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to delete: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to delete session: {str(e)}"
            state.status_message = f"Delete failed (offline mode): {str(e)}"

    @ctrl.trigger("attach_evidence")
    def attach_evidence(session_id: str, evidence_path: str):
        """Attach evidence file to session via REST API."""
        if not session_id or not evidence_path:
            state.has_error = True
            state.error_message = "Session ID and evidence path are required"
            return
        try:
            state.evidence_attach_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{api_base_url}/api/sessions/{session_id}/evidence",
                    json={"evidence_source": evidence_path}
                )
                if response.status_code == 201:
                    state.status_message = f"Evidence attached: {evidence_path}"
                    state.show_evidence_attach = False
                    state.evidence_attach_path = ""
                    load_sessions_page()
                else:
                    state.has_error = True
                    state.error_message = f"Failed to attach evidence: {response.status_code}"
            state.evidence_attach_loading = False
        except Exception as e:
            state.evidence_attach_loading = False
            state.has_error = True
            state.error_message = f"Failed to attach evidence: {str(e)}"
