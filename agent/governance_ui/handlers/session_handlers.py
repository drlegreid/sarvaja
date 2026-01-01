"""
Session and Decision entity handlers for Governance Dashboard.

Per RULE-012: Single Responsibility - session/decision selection operations.
Per RULE-019: UI/UX Standards - consistent handler patterns.
"""

import httpx
from typing import Any

API_BASE_URL = "http://localhost:8082"


def register_session_handlers(ctrl: Any, state: Any) -> None:
    """Register all session-related handlers with the controller."""

    @ctrl.set("select_session")
    def select_session(session_id: str) -> None:
        """Handle session selection for detail view."""
        for session in state.sessions:
            if session.get('session_id') == session_id or session.get('id') == session_id:
                state.selected_session = session
                state.show_session_detail = True
                break

    @ctrl.set("close_session_detail")
    def close_session_detail() -> None:
        """Close session detail view."""
        state.show_session_detail = False
        state.selected_session = None

    @ctrl.set("select_decision")
    def select_decision(decision_id: str) -> None:
        """Handle decision selection for detail view."""
        for decision in state.decisions:
            if decision.get('decision_id') == decision_id or decision.get('id') == decision_id:
                state.selected_decision = decision
                state.show_decision_detail = True
                break

    @ctrl.set("close_decision_detail")
    def close_decision_detail() -> None:
        """Close decision detail view."""
        state.show_decision_detail = False
        state.selected_decision = None

    @ctrl.trigger("start_session")
    def start_session() -> None:
        """Start a new session via REST API."""
        try:
            state.is_loading = True
            session_data = {
                "topic": state.new_session_topic or "General Session",
                "session_type": state.new_session_type or "general",
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{API_BASE_URL}/api/sessions", json=session_data)
                if response.status_code == 201:
                    state.status_message = "Session started successfully"
                    sessions_response = client.get(f"{API_BASE_URL}/api/sessions")
                    if sessions_response.status_code == 200:
                        state.sessions = sessions_response.json()
                else:
                    state.has_error = True
                    state.error_message = f"Failed to start session: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to start session: {str(e)}"

    @ctrl.trigger("end_session")
    def end_session() -> None:
        """End current session via REST API."""
        if not state.selected_session:
            return
        try:
            state.is_loading = True
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{API_BASE_URL}/api/sessions/{session_id}/end")
                if response.status_code == 200:
                    state.status_message = f"Session {session_id} ended"
                    sessions_response = client.get(f"{API_BASE_URL}/api/sessions")
                    if sessions_response.status_code == 200:
                        state.sessions = sessions_response.json()
                    state.show_session_detail = False
                    state.selected_session = None
                else:
                    state.has_error = True
                    state.error_message = f"Failed to end session: {response.status_code}"
            state.is_loading = False
        except Exception as e:
            state.is_loading = False
            state.has_error = True
            state.error_message = f"Failed to end session: {str(e)}"

    @ctrl.trigger("attach_evidence")
    def attach_evidence(session_id: str, evidence_path: str) -> None:
        """
        Attach evidence file to session via REST API.

        Per P11.5: Session Evidence Attachments.
        Per GAP-DATA-003: Evidence attachment functionality.
        """
        if not session_id or not evidence_path:
            state.has_error = True
            state.error_message = "Session ID and evidence path are required"
            return

        try:
            state.evidence_attach_loading = True
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/api/sessions/{session_id}/evidence",
                    json={"evidence_source": evidence_path}
                )
                if response.status_code == 201:
                    state.status_message = f"Evidence attached: {evidence_path}"
                    state.show_evidence_attach = False
                    state.evidence_attach_path = ""

                    # Refresh the selected session to show new evidence
                    session_response = client.get(f"{API_BASE_URL}/api/sessions")
                    if session_response.status_code == 200:
                        state.sessions = session_response.json()
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
