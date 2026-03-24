"""
Task Linking Controllers
========================
Controller functions for linking sessions and documents to tasks.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
"""

import httpx as _httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace as _add_error_trace


def register_tasks_linking(state: Any, ctrl: Any, api_base_url: str,
                           httpx_mod=None, error_trace_fn=None) -> None:
    """Register task linking controllers with Trame.

    Args:
        httpx_mod: Injectable httpx module (for testability via hub's patchable reference).
        error_trace_fn: Injectable add_error_trace (for testability).
    """
    httpx = httpx_mod if httpx_mod is not None else _httpx
    add_error_trace = error_trace_fn if error_trace_fn is not None else _add_error_trace

    @ctrl.trigger("attach_document")
    def attach_document():
        """Attach a document to the selected task via REST API."""
        if not state.selected_task:
            return
        doc_path = getattr(state, 'attach_document_path', '')
        if not doc_path:
            state.has_error = True
            state.error_message = "Document path is required"
            return
        # BUG-UI-UNDEF-008: Pre-initialize to avoid NameError in except handler
        task_id = state.selected_task.get('task_id', 'unknown')
        try:
            task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{api_base_url}/api/tasks/{task_id}/documents",
                    json={"document_path": doc_path}
                )
                if response.status_code == 201:
                    state.status_message = f"Document attached to {task_id}"
                    # Refresh task detail
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
                else:
                    state.has_error = True
                    state.error_message = f"Attach failed: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Attach document failed: {e}", f"/api/tasks/{task_id}/documents")
            state.has_error = True
            state.error_message = f"Attach failed: {type(e).__name__}"  # BUG-476-CTK-6
        finally:
            state.show_attach_document_dialog = False
            state.attach_document_path = ""

    # --- Link Session dialog handlers (SRVJ-FEAT-011) ---

    @ctrl.trigger("open_link_session_dialog")
    def open_link_session_dialog():
        """Open the link session picker dialog. Fetches available sessions."""
        state.link_session_loading = True
        state.link_session_search = ""
        state.show_link_session_dialog = True
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions",
                    params={"limit": 100}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("sessions", []))
                    state.link_session_items = items
                else:
                    state.link_session_items = []
        except Exception as e:
            add_error_trace(state, f"Fetch sessions for link dialog failed: {e}", "/api/sessions")
            state.link_session_items = []
        finally:
            state.link_session_loading = False

    @ctrl.trigger("link_session_to_task")
    def link_session_to_task(session_id):
        """Link a session to the selected task via REST API."""
        if not state.selected_task or not session_id:
            return
        task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{api_base_url}/api/tasks/{task_id}/sessions/{session_id}"
                )
                if response.status_code == 201:
                    state.status_message = f"Session {session_id} linked to {task_id}"
                    # Refresh task detail to show new linked session
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
                else:
                    state.has_error = True
                    state.error_message = f"Link session failed: {response.status_code}"
        except Exception as e:
            add_error_trace(state, f"Link session failed: {e}", f"/api/tasks/{task_id}/sessions/{session_id}")
            state.has_error = True
            state.error_message = f"Link session failed: {type(e).__name__}"
        finally:
            # BUG-014: Always close dialog after link attempt
            state.show_link_session_dialog = False
            state.link_session_search = ""

    # --- Link Document dialog handlers (SRVJ-FEAT-012) ---

    @ctrl.trigger("open_link_document_dialog")
    def open_link_document_dialog():
        """Open the link document browser dialog. Fetches available documents."""
        state.link_document_loading = True
        state.link_document_search = ""
        state.link_document_selected = []
        state.show_link_document_dialog = True
        try:
            with httpx.Client(timeout=10.0) as client:
                # BUG-015: Use /api/files/list (workspace scan), not /api/documents (404)
                response = client.get(
                    f"{api_base_url}/api/files/list",
                    params={"directory": "docs", "pattern": "*.md", "recursive": "true"}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("documents", []))
                    # Normalize to [{path: ...}] format
                    normalized = []
                    for item in items:
                        if isinstance(item, str):
                            normalized.append({"path": item})
                        elif isinstance(item, dict):
                            path = item.get("path") or item.get("document_path") or item.get("id", "")
                            normalized.append({"path": path, **item})
                        else:
                            normalized.append({"path": str(item)})
                    state.link_document_items = normalized
                else:
                    state.link_document_items = []
        except Exception as e:
            add_error_trace(state, f"Fetch documents for link dialog failed: {e}", "/api/documents")
            state.link_document_items = []
        finally:
            state.link_document_loading = False

    @ctrl.trigger("link_documents_to_task")
    def link_documents_to_task():
        """Batch link selected documents to the selected task."""
        if not state.selected_task:
            return
        selected = getattr(state, 'link_document_selected', [])
        if not selected:
            return
        task_id = state.selected_task.get('id') or state.selected_task.get('task_id')
        linked_count = 0
        try:
            with httpx.Client(timeout=10.0) as client:
                for doc_path in selected:
                    response = client.post(
                        f"{api_base_url}/api/tasks/{task_id}/documents",
                        json={"document_path": doc_path}
                    )
                    if response.status_code == 201:
                        linked_count += 1
                if linked_count > 0:
                    state.status_message = f"{linked_count} document(s) linked to {task_id}"
                    # Refresh task detail
                    detail_resp = client.get(f"{api_base_url}/api/tasks/{task_id}")
                    if detail_resp.status_code == 200:
                        state.selected_task = detail_resp.json()
        except Exception as e:
            add_error_trace(state, f"Batch link documents failed: {e}", f"/api/tasks/{task_id}/documents")
            state.has_error = True
            state.error_message = f"Link documents failed: {type(e).__name__}"
        finally:
            state.show_link_document_dialog = False
            state.link_document_selected = []
            state.link_document_search = ""
