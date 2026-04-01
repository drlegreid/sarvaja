"""
Sessions Controllers (GAP-FILE-005)
===================================
Controller functions for session CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py
Per GAP-UI-034: Session CRUD operations
Per DOC-SIZE-01-v1: Pagination in sessions_pagination.py,
    detail loaders in sessions_detail_loaders.py.
Per EPIC-PERF-TELEM-V1 P4: select_session uses ThreadPoolExecutor
    for parallel detail loaders.

Created: 2024-12-28
Updated: 2026-03-26 (P4: parallel session detail loading)
"""

import re

import httpx
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from governance.middleware.dashboard_log import log_action

# BUG-350-SES-001: Validate session_id before URL path interpolation
# (mirrors _AGENT_ID_RE in trust.py for agent_id validation)
_SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.\(\)]{1,200}$')
from agent.governance_ui.trace_bar.transforms import add_error_trace
from .sessions_pagination import register_sessions_pagination  # noqa: F401
from .sessions_detail_loaders import register_session_detail_loaders


def register_sessions_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register session-related controllers with Trame."""

    # Register pagination + filters; get load_sessions_page reference
    load_sessions_page = register_sessions_pagination(state, ctrl, api_base_url)

    # Register detail data loaders
    loaders = register_session_detail_loaders(state, api_base_url)

    @ctrl.trigger("select_session")
    def select_session(session_id):
        """Handle session selection for detail view.

        P4: Parallel detail loaders via ThreadPoolExecutor.
        Detail GET is synchronous (sets selected_session for UI),
        then 7 sub-loaders fire in parallel. Timeline is built after
        tools+thoughts complete. All state updates on main thread.
        """
        # BUG-350-SES-001: Validate session_id format before URL interpolation
        if not session_id or not isinstance(session_id, str) or not _SESSION_ID_RE.match(session_id):
            return
        log_action("sessions", "select", session_id=session_id)
        # BUG-UI-STALE-DETAIL-003: Clear prior session detail state
        state.session_tool_calls = []
        state.session_thinking_items = []
        state.session_timeline = []
        state.session_tasks = []
        state.session_evidence_html = ''
        state.evidence_search = ''
        state.session_transcript = []
        state.session_transcript_page = 1
        state.session_validation_data = None
        # Set loading flags for all sub-sections
        state.session_tool_calls_loading = True
        state.session_thinking_items_loading = True
        state.session_tasks_loading = True
        state.session_evidence_loading = True
        state.session_transcript_loading = True
        state.session_validation_loading = True
        # BUG-260-SESSION-001: Guard against None state.sessions
        for session in (state.sessions or []):
            if session.get('session_id') == session_id or session.get('id') == session_id:
                state.selected_session = session
                state.show_session_detail = True
                break

        # Step 1: Synchronous detail fetch (sets selected_session for UI)
        try:
            resp = httpx.get(f"{api_base_url}/api/sessions/{session_id}", timeout=10.0)
            if resp.status_code == 200:
                session_data = resp.json()
                # P0-2: Prefer server-computed duration, fallback to local
                if not session_data.get("duration"):
                    from agent.governance_ui.utils import compute_session_duration
                    session_data["duration"] = compute_session_duration(
                        session_data.get("start_time", ""),
                        session_data.get("end_time", ""),
                    )
                # BUG-UI-SESSIONS-DETAIL-001: Derive source_type for detail view
                if not session_data.get("source_type"):
                    sid = session_data.get("session_id", "")
                    if session_data.get("cc_session_uuid") or "-CC-" in sid:
                        session_data["source_type"] = "CC"
                    elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                        session_data["source_type"] = "Chat"
                    else:
                        session_data["source_type"] = "API"
                state.selected_session = session_data
                state.show_session_detail = True
        except Exception as e:
            add_error_trace(state, f"Load session detail failed: {type(e).__name__}",
                            f"/api/sessions/{session_id}")

        # Step 2: Fire 7 sub-loaders in parallel via fetch_* (no state mutation)
        with ThreadPoolExecutor(max_workers=4) as executor:
            f_evidence = executor.submit(loaders["fetch_evidence"], session_id)
            f_tasks = executor.submit(loaders["fetch_tasks"], session_id)
            f_tools = executor.submit(loaders["fetch_tool_calls"], session_id)
            f_thoughts = executor.submit(loaders["fetch_thinking_items"], session_id)
            f_ev_html = executor.submit(loaders["fetch_evidence_rendered"], session_id)
            f_transcript = executor.submit(loaders["fetch_transcript"], session_id)
            f_validation = executor.submit(loaders["fetch_validation"], session_id)

        # Step 3: Apply all results on main thread (Trame state NOT thread-safe)
        tools_data = f_tools.result()
        state.session_tool_calls = tools_data.get("session_tool_calls", [])
        state.session_tool_calls_loading = False
        if "_error" in tools_data:
            add_error_trace(state, tools_data["_error"], tools_data["_endpoint"])

        thoughts_data = f_thoughts.result()
        state.session_thinking_items = thoughts_data.get("session_thinking_items", [])
        state.session_thinking_items_loading = False
        if "_error" in thoughts_data:
            add_error_trace(state, thoughts_data["_error"], thoughts_data["_endpoint"])

        # Build timeline AFTER tools + thoughts are ready
        state.session_timeline = loaders["build_timeline_data"](
            tools_data.get("session_tool_calls", []),
            thoughts_data.get("session_thinking_items", []),
        )

        evidence_data = f_evidence.result()
        ev_files = evidence_data.get("evidence_files", [])
        if state.selected_session and ev_files:
            session_dict = dict(state.selected_session)
            session_dict['evidence_files'] = ev_files
            state.selected_session = session_dict
        if "_error" in evidence_data:
            add_error_trace(state, evidence_data["_error"], evidence_data["_endpoint"])

        tasks_data = f_tasks.result()
        state.session_tasks = tasks_data.get("session_tasks", [])
        state.session_tasks_loading = False
        if "_error" in tasks_data:
            add_error_trace(state, tasks_data["_error"], tasks_data["_endpoint"])

        ev_html_data = f_ev_html.result()
        state.session_evidence_html = ev_html_data.get("session_evidence_html", '')
        state.session_evidence_loading = False
        if "_error" in ev_html_data:
            add_error_trace(state, ev_html_data["_error"], ev_html_data["_endpoint"])

        transcript_data = f_transcript.result()
        state.session_transcript = transcript_data.get("session_transcript", [])
        state.session_transcript_page = transcript_data.get("session_transcript_page", 1)
        state.session_transcript_total = transcript_data.get("session_transcript_total", 0)
        state.session_transcript_has_more = transcript_data.get(
            "session_transcript_has_more", False
        )
        state.session_transcript_loading = False
        if "_error" in transcript_data:
            add_error_trace(state, transcript_data["_error"], transcript_data["_endpoint"])

        validation_data = f_validation.result()
        state.session_validation_data = validation_data.get("session_validation_data")
        state.session_validation_loading = False
        if "_error" in validation_data:
            add_error_trace(state, validation_data["_error"], validation_data["_endpoint"])

    @ctrl.trigger("navigate_to_rule_from_session")
    def navigate_to_rule_from_session(rule_id):
        """Navigate to a linked rule from session detail view."""
        if not rule_id:
            return
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        state.nav_source_view = 'sessions'
        state.nav_source_id = session_id
        state.nav_source_label = f'Session {session_id}' if session_id else 'Sessions'
        state.active_view = 'rules'
        state.show_session_detail = False
        # BUG-260-SESSION-002: Guard against None state.rules
        for rule in (state.rules or []):
            if rule.get('rule_id') == rule_id:
                state.selected_rule = rule
                state.show_rule_detail = True
                break

    @ctrl.trigger("navigate_to_decision_from_session")
    def navigate_to_decision_from_session(decision_id):
        """Navigate to a linked decision from session detail view."""
        if not decision_id:
            return
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        state.nav_source_view = 'sessions'
        state.nav_source_id = session_id
        state.nav_source_label = f'Session {session_id}' if session_id else 'Sessions'
        state.active_view = 'decisions'
        state.show_session_detail = False
        # BUG-260-SESSION-003: Guard against None state.decisions
        for dec in (state.decisions or []):
            if dec.get('decision_id') == decision_id or dec.get('id') == decision_id:
                state.selected_decision = dec
                state.show_decision_detail = True
                break

    @ctrl.trigger("close_session_detail")
    def close_session_detail():
        """Close session detail view and reset detail state."""
        state.show_session_detail = False
        state.selected_session = None
        state.session_tool_calls = []
        state.session_thinking_items = []
        state.session_timeline = []
        state.session_tasks = []
        state.session_evidence_html = ''
        state.evidence_search = ''
        state.session_transcript = []
        state.session_transcript_page = 1
        state.session_transcript_total = 0
        state.session_transcript_has_more = False
        state.session_transcript_expanded_entry = None

    @ctrl.trigger("load_transcript_page")
    def load_transcript_page(page):
        """Load a specific page of the transcript."""
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        if session_id:
            loaders["load_transcript"](session_id, page=page)

    @ctrl.trigger("expand_transcript_entry")
    def expand_transcript_entry(entry_index):
        """Expand a truncated transcript entry to show full content."""
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        if session_id:
            loaders["load_transcript_entry"](session_id, entry_index)

    @ctrl.trigger("toggle_transcript_thinking")
    def toggle_transcript_thinking():
        """Toggle thinking inclusion and reload transcript."""
        state.session_transcript_include_thinking = not state.session_transcript_include_thinking
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        if session_id:
            loaders["load_transcript"](session_id)

    @ctrl.trigger("toggle_transcript_user")
    def toggle_transcript_user():
        """Toggle user prompts inclusion and reload transcript."""
        state.session_transcript_include_user = not state.session_transcript_include_user
        session_id = None
        if state.selected_session:
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
        if session_id:
            loaders["load_transcript"](session_id)

    @ctrl.trigger("open_session_form")
    def open_session_form(mode="create"):
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

    @ctrl.trigger("close_session_form")
    def close_session_form():
        """Close session form."""
        state.show_session_form = False

    @ctrl.trigger("submit_session_form")
    def submit_session_form():
        """Submit session form (create/update) via REST API."""
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        log_action("sessions", state.session_form_mode, session_id=state.form_session_id)
        # BUG-UI-VALIDATION-001: Validate on create
        if state.session_form_mode == "create":
            sid = (state.form_session_id or "").strip()
            if not sid:
                state.has_error = True
                state.error_message = "Session ID is required"
                return
        try:
            state.is_loading = True
            session_data = {
                "session_id": (state.form_session_id or "").strip() or None,
                "description": (state.form_session_description or "").strip(),
                "agent_id": (state.form_session_agent_id or "").strip() or None
            }

            with httpx.Client(timeout=10.0) as client:
                if state.session_form_mode == "create":
                    response = client.post(f"{api_base_url}/api/sessions", json=session_data)
                else:
                    # BUG-UI-SESSION-GUARD-001: Guard against None selected_session
                    if not state.selected_session:
                        state.has_error = True
                        state.error_message = "No session selected for editing"
                        # BUG-S-03: Reset is_loading on early return
                        state.is_loading = False
                        return
                    session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
                    # BUG-350-SES-001: Validate session_id before URL interpolation
                    if not session_id or not _SESSION_ID_RE.match(str(session_id)):
                        state.has_error = True
                        state.error_message = "Invalid session ID format"
                        state.is_loading = False
                        return
                    update_data = {
                        "description": state.form_session_description,
                        "status": state.form_session_status,
                        "agent_id": state.form_session_agent_id or None
                    }
                    response = client.put(f"{api_base_url}/api/sessions/{session_id}", json=update_data)

                if response.status_code in (200, 201):
                    state.status_message = f"Session {'created' if state.session_form_mode == 'create' else 'updated'} successfully"
                    load_sessions_page()
                    # BUG-UI-FORMCLOSE-001: Only close form on success
                    state.show_session_form = False
                    state.show_session_detail = False
                    state.selected_session = None
                else:
                    state.has_error = True
                    # BUG-426-SES-001: Don't leak response.text (may contain internal paths/stack traces) via Trame WebSocket
                    state.error_message = f"API Error: {response.status_code}"

            state.is_loading = False
        except Exception as e:
            # BUG-453-SES-002: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Save session failed: {type(e).__name__}", "/api/sessions")
            state.is_loading = False
            state.has_error = True
            # BUG-385-SES-001: Don't leak httpx internals (URLs, connection errors) via Trame WebSocket
            state.error_message = f"Failed to save session: {type(e).__name__}"

    @ctrl.trigger("delete_session")
    def delete_session():
        """Delete selected session via REST API."""
        if not state.selected_session:
            return
        # BUG-UI-DOUBLECLICK-001: Prevent double-click race condition
        if state.is_loading:
            return
        state.has_error = False
        log_action("sessions", "delete", session_id=state.selected_session.get("session_id"))
        # BUG-UI-UNDEF-001: Pre-initialize to avoid NameError in except handler
        session_id = state.selected_session.get('session_id', 'unknown')
        try:
            state.is_loading = True
            session_id = state.selected_session.get('session_id') or state.selected_session.get('id')
            # BUG-350-SES-001: Validate session_id before URL interpolation
            if not session_id or not _SESSION_ID_RE.match(str(session_id)):
                state.has_error = True
                state.error_message = "Invalid session ID format"
                state.is_loading = False
                return

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
            # BUG-453-SES-003: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Delete session failed: {type(e).__name__}", f"/api/sessions/{session_id}")
            state.is_loading = False
            state.has_error = True
            # BUG-385-SES-002: Don't leak httpx internals via Trame WebSocket
            state.error_message = f"Failed to delete session: {type(e).__name__}"

    @ctrl.trigger("attach_evidence")
    def attach_evidence(session_id: str, evidence_path: str):
        """Attach evidence file to session via REST API."""
        if not session_id or not evidence_path:
            state.has_error = True
            state.error_message = "Session ID and evidence path are required"
            return
        # BUG-350-SES-001: Validate session_id before URL interpolation
        if not _SESSION_ID_RE.match(str(session_id)):
            state.has_error = True
            state.error_message = "Invalid session ID format"
            return
        # BUG-351-EVP-001: Validate evidence_path to prevent path traversal
        evidence_path = (evidence_path or "").strip()
        if ".." in evidence_path or evidence_path.startswith("/") or len(evidence_path) > 500:
            state.has_error = True
            state.error_message = "Invalid evidence path"
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
                    # Refresh detail view evidence (BUG-EVIDENCE-STALE-001)
                    loaders["load_evidence"](session_id)
                    loaders["load_evidence_rendered"](session_id)
                else:
                    state.has_error = True
                    state.error_message = f"Failed to attach evidence: {response.status_code}"
            state.evidence_attach_loading = False
        except Exception as e:
            # BUG-453-SES-004: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Attach evidence failed: {type(e).__name__}", f"/api/sessions/{session_id}/evidence")
            state.evidence_attach_loading = False
            state.has_error = True
            # BUG-385-SES-003: Don't leak httpx internals via Trame WebSocket
            state.error_message = f"Failed to attach evidence: {type(e).__name__}"
