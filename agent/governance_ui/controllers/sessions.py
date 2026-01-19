"""
Sessions Controllers (GAP-FILE-005)
===================================
Controller functions for session CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-034: Session CRUD operations

Created: 2024-12-28
Updated: 2026-01-02 (GAP-UI-034)
"""

import httpx
from typing import Any


def register_sessions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register session-related controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.trigger("select_session")
    def select_session(session_id):
        """Handle session selection for detail view.

        Per GAP-UI-SESSION-TASKS-001: Also load tasks linked to this session.
        Uses @ctrl.trigger to match trigger() call from Vue click handler.
        """
        for session in state.sessions:
            if session.get('session_id') == session_id or session.get('id') == session_id:
                state.selected_session = session
                state.show_session_detail = True
                # Load session tasks (GAP-DATA-INTEGRITY-001 Phase 3)
                load_session_tasks(session_id)
                break

    def load_session_tasks(session_id):
        """Load tasks linked to a session via completed-in relation.

        Per GAP-DATA-INTEGRITY-001 Phase 3: UI navigation for relationships.
        Per GAP-UI-SESSION-TASKS-001: Fetch tasks from API endpoint.
        """
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
            # Populate form with selected session data
            state.form_session_id = state.selected_session.get('session_id') or state.selected_session.get('id', '')
            state.form_session_description = state.selected_session.get('description', '')
            state.form_session_status = state.selected_session.get('status', 'ACTIVE')
            state.form_session_agent_id = state.selected_session.get('agent_id', '')
        else:
            # Clear form for new session
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
        try:
            state.is_loading = True
            session_data = {
                "session_id": state.form_session_id or None,  # None triggers auto-generation
                "description": state.form_session_description,
                "agent_id": state.form_session_agent_id or None
            }

            with httpx.Client(timeout=10.0) as client:
                if state.session_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/sessions", json=session_data)
                else:
                    # Edit mode - update existing session
                    session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
                    update_data = {
                        "description": state.form_session_description,
                        "status": state.form_session_status,
                        "agent_id": state.form_session_agent_id or None
                    }
                    response = client.put(f"{api_base_url}/api/sessions/{session_id}", json=update_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Session {'created' if state.session_form_mode == 'create' else 'updated'} successfully"
                    # Reload sessions from API (per GAP-EXPLOR-API-001: now returns paginated response)
                    sessions_response = client.get(f"{api_base_url}/api/sessions?limit=100")
                    if sessions_response.status_code == 200:
                        data = sessions_response.json()
                        # Handle paginated response (items) or raw list (backward compatibility)
                        state.sessions = data.get("items", data) if isinstance(data, dict) else data
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

        try:
            state.is_loading = True
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')

            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{api_base_url}/api/sessions/{session_id}")

                if response.status_code == 204:
                    state.status_message = f"Session {session_id} deleted successfully"
                    # Reload sessions from API (per GAP-EXPLOR-API-001: now returns paginated response)
                    sessions_response = client.get(f"{api_base_url}/api/sessions?limit=100")
                    if sessions_response.status_code == 200:
                        data = sessions_response.json()
                        # Handle paginated response (items) or raw list (backward compatibility)
                        state.sessions = data.get("items", data) if isinstance(data, dict) else data
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
        """Attach evidence file to session via REST API.

        Per P11.5: Session Evidence Attachments.
        Per GAP-DATA-003: Evidence attachment functionality.
        Moved from handlers/session_handlers.py per GAP-UI-SESSION-TASKS-001.
        """
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

                    # Refresh the selected session to show new evidence
                    session_response = client.get(f"{api_base_url}/api/sessions?limit=100")
                    if session_response.status_code == 200:
                        data = session_response.json()
                        state.sessions = data.get("items", data) if isinstance(data, dict) else data
                        # Update selected session with refreshed data
                        for session in state.sessions:
                            sid = session.get('session_id') or session.get('id')
                            if sid == session_id:
                                state.selected_session = session
                                break
                else:
                    state.has_error = True
                    state.error_message = f"Failed to attach evidence: {response.status_code}"
            state.evidence_attach_loading = False
        except Exception as e:
            state.evidence_attach_loading = False
            state.has_error = True
            state.error_message = f"Failed to attach evidence: {str(e)}"
