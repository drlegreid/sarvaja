"""
Workspaces Controller.

Handles: load, select, create, edit, delete workspace triggers.
Full CRUD for workspace entities in the dashboard.
"""

import logging
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_api_trace, add_error_trace

logger = logging.getLogger(__name__)


def register_workspace_controllers(
    state: Any, ctrl: Any, api_base_url: str
) -> dict:
    """Register workspace view controllers. Returns loader dict."""

    def load_workspaces():
        """Load workspaces from REST API."""
        state.workspaces_loading = True
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{api_base_url}/api/workspaces")
                add_api_trace(
                    state, "/api/workspaces", "GET",
                    resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.workspaces = resp.json()
                else:
                    state.workspaces = []

                # Also load workspace types
                types_resp = client.get(
                    f"{api_base_url}/api/workspaces/types"
                )
                if types_resp.status_code == 200:
                    types_data = types_resp.json()
                    state.workspace_types = types_data
                    state.workspace_type_options = [
                        t.get("type_id", t.get("name", ""))
                        for t in types_data
                    ]
        except Exception as e:
            add_error_trace(
                state, f"Load workspaces failed: {e}",
                "/api/workspaces",
            )
            state.workspaces = []
        finally:
            state.workspaces_loading = False

    @ctrl.trigger("load_workspaces")
    def _load_workspaces():
        load_workspaces()

    @ctrl.trigger("select_workspace")
    def select_workspace(workspace_id):
        """Select a workspace and show detail view."""
        if not workspace_id:
            return
        state.edit_workspace_mode = False
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{api_base_url}/api/workspaces/{workspace_id}"
                )
                add_api_trace(
                    state, f"/api/workspaces/{workspace_id}", "GET",
                    resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.selected_workspace = resp.json()
                    state.show_workspace_detail = True
                    # GAP-WS-DETAIL-UI: Fetch linked tasks
                    _load_workspace_tasks(workspace_id)
                else:
                    state.status_message = (
                        f"Workspace {workspace_id} not found"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Load workspace failed: {e}",
                f"/api/workspaces/{workspace_id}",
            )

    def _load_workspace_tasks(workspace_id):
        """Fetch tasks linked to a workspace. Per GAP-WS-DETAIL-UI."""
        state.workspace_tasks_loading = True
        state.workspace_tasks = []
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{api_base_url}/api/workspaces/{workspace_id}/tasks"
                )
                add_api_trace(
                    state,
                    f"/api/workspaces/{workspace_id}/tasks",
                    "GET", resp.status_code, 0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    state.workspace_tasks = data.get("items", [])
        except Exception as e:
            add_error_trace(
                state,
                f"Load workspace tasks failed: {e}",
                f"/api/workspaces/{workspace_id}/tasks",
            )
        finally:
            state.workspace_tasks_loading = False

    # ── Create ──────────────────────────────────────────────────

    @ctrl.trigger("show_create_workspace_form")
    def show_create_workspace_form():
        """Open the create workspace form."""
        state.show_workspace_form = True
        state.form_workspace_name = ""
        state.form_workspace_type = "generic"
        state.form_workspace_description = ""
        state.form_workspace_project_id = ""
        state.has_error = False

    @ctrl.trigger("cancel_workspace_form")
    def cancel_workspace_form():
        """Close the create workspace form."""
        state.show_workspace_form = False

    @ctrl.trigger("create_workspace")
    def create_workspace():
        """Create a new workspace via REST API."""
        if state.is_loading:
            return
        state.has_error = False
        name = (getattr(state, "form_workspace_name", "") or "").strip()
        if not name:
            state.has_error = True
            state.error_message = "Workspace name is required"
            return
        try:
            state.is_loading = True
            ws_data = {
                "name": name,
                "workspace_type": (
                    getattr(state, "form_workspace_type", "") or "generic"
                ).strip(),
                "description": (
                    getattr(state, "form_workspace_description", "") or ""
                ).strip() or None,
                "project_id": (
                    getattr(state, "form_workspace_project_id", "") or ""
                ).strip() or None,
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{api_base_url}/api/workspaces", json=ws_data
                )
                add_api_trace(
                    state, "/api/workspaces", "POST",
                    resp.status_code, 0,
                )
                if resp.status_code == 201:
                    state.status_message = "Workspace created"
                    state.show_workspace_form = False
                    load_workspaces()
                else:
                    state.has_error = True
                    state.error_message = (
                        f"Create failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Create workspace failed: {e}",
                "/api/workspaces",
            )
            state.has_error = True
            state.error_message = f"Create failed: {type(e).__name__}"
        finally:
            state.is_loading = False

    # ── Edit ────────────────────────────────────────────────────

    @ctrl.trigger("edit_workspace")
    def edit_workspace():
        """Enter workspace edit mode."""
        if state.selected_workspace:
            state.edit_workspace_mode = True
            state.edit_workspace_name = (
                state.selected_workspace.get("name") or ""
            )
            state.edit_workspace_description = (
                state.selected_workspace.get("description") or ""
            )
            state.edit_workspace_status = (
                state.selected_workspace.get("status") or "active"
            )

    @ctrl.trigger("cancel_workspace_edit")
    def cancel_workspace_edit():
        """Cancel workspace edit mode."""
        state.edit_workspace_mode = False

    @ctrl.trigger("submit_workspace_edit")
    def submit_workspace_edit():
        """Submit workspace edit via REST API."""
        if not state.selected_workspace or state.is_loading:
            return
        state.has_error = False
        name = (getattr(state, "edit_workspace_name", "") or "").strip()
        if not name:
            state.has_error = True
            state.error_message = "Workspace name is required"
            return
        workspace_id = state.selected_workspace.get("workspace_id")
        try:
            state.is_loading = True
            update_data = {
                "name": name,
                "description": (
                    getattr(state, "edit_workspace_description", "") or ""
                ).strip() or None,
                "status": (
                    getattr(state, "edit_workspace_status", "") or "active"
                ).strip(),
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.put(
                    f"{api_base_url}/api/workspaces/{workspace_id}",
                    json=update_data,
                )
                add_api_trace(
                    state, f"/api/workspaces/{workspace_id}", "PUT",
                    resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.status_message = "Workspace updated"
                    state.selected_workspace = resp.json()
                    state.edit_workspace_mode = False
                    load_workspaces()
                else:
                    state.has_error = True
                    state.error_message = (
                        f"Update failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Update workspace failed: {e}",
                f"/api/workspaces/{workspace_id}",
            )
            state.has_error = True
            state.error_message = f"Update failed: {type(e).__name__}"
        finally:
            state.is_loading = False

    # ── Delete ──────────────────────────────────────────────────

    @ctrl.trigger("confirm_delete_workspace")
    def confirm_delete_workspace():
        """Show delete confirmation."""
        state.show_workspace_delete_confirm = True

    @ctrl.trigger("cancel_delete_workspace")
    def cancel_delete_workspace():
        """Cancel delete confirmation."""
        state.show_workspace_delete_confirm = False

    @ctrl.trigger("delete_workspace")
    def delete_workspace():
        """Delete selected workspace via REST API."""
        if not state.selected_workspace or state.is_loading:
            return
        state.has_error = False
        workspace_id = state.selected_workspace.get("workspace_id")
        try:
            state.is_loading = True
            with httpx.Client(timeout=10.0) as client:
                resp = client.delete(
                    f"{api_base_url}/api/workspaces/{workspace_id}"
                )
                add_api_trace(
                    state, f"/api/workspaces/{workspace_id}", "DELETE",
                    resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.status_message = (
                        f"Workspace {workspace_id} deleted"
                    )
                    state.show_workspace_detail = False
                    state.selected_workspace = None
                    state.show_workspace_delete_confirm = False
                    load_workspaces()
                else:
                    state.has_error = True
                    state.error_message = (
                        f"Delete failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Delete workspace failed: {e}",
                f"/api/workspaces/{workspace_id}",
            )
            state.has_error = True
            state.error_message = f"Delete failed: {type(e).__name__}"
        finally:
            state.is_loading = False
            state.show_workspace_delete_confirm = False

    # ── Agent capabilities ──────────────────────────────────────

    @ctrl.trigger("load_agent_capabilities")
    def load_agent_capabilities(agent_id):
        """Load capabilities for the selected agent."""
        if not agent_id:
            return
        state.agent_capabilities_loading = True
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{api_base_url}/api/agents/{agent_id}/capabilities"
                )
                add_api_trace(
                    state,
                    f"/api/agents/{agent_id}/capabilities",
                    "GET", resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.agent_capabilities = resp.json()
                else:
                    state.agent_capabilities = []
        except Exception as e:
            add_error_trace(
                state, f"Load capabilities failed: {e}",
                f"/api/agents/{agent_id}/capabilities",
            )
            state.agent_capabilities = []
        finally:
            state.agent_capabilities_loading = False

    @ctrl.trigger("bind_capability")
    def bind_capability(agent_id, rule_id, category="general"):
        """Bind a rule to an agent via REST API."""
        if not agent_id or not rule_id:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{api_base_url}/api/capabilities",
                    json={
                        "agent_id": agent_id,
                        "rule_id": rule_id,
                        "category": category,
                    },
                )
                add_api_trace(
                    state, "/api/capabilities", "POST",
                    resp.status_code, 0,
                )
                if resp.status_code == 201:
                    state.status_message = (
                        f"Bound {rule_id} to {agent_id}"
                    )
                    load_agent_capabilities(agent_id)
                else:
                    state.status_message = (
                        f"Bind failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Bind capability failed: {e}",
                "/api/capabilities",
            )

    @ctrl.trigger("unbind_capability")
    def unbind_capability(agent_id, rule_id):
        """Unbind a rule from an agent via REST API."""
        if not agent_id or not rule_id:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.delete(
                    f"{api_base_url}/api/capabilities/{agent_id}/{rule_id}"
                )
                add_api_trace(
                    state,
                    f"/api/capabilities/{agent_id}/{rule_id}",
                    "DELETE", resp.status_code, 0,
                )
                if resp.status_code == 200:
                    state.status_message = (
                        f"Unbound {rule_id} from {agent_id}"
                    )
                    load_agent_capabilities(agent_id)
                else:
                    state.status_message = (
                        f"Unbind failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Unbind capability failed: {e}",
                f"/api/capabilities/{agent_id}/{rule_id}",
            )

    @ctrl.trigger("toggle_capability_status")
    def toggle_capability_status(agent_id, rule_id, current_status):
        """Toggle a capability status between active/suspended."""
        if not agent_id or not rule_id:
            return
        new_status = (
            "suspended" if current_status == "active" else "active"
        )
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.put(
                    f"{api_base_url}/api/capabilities/{agent_id}/{rule_id}/status",
                    json={"status": new_status},
                )
                add_api_trace(
                    state,
                    f"/api/capabilities/{agent_id}/{rule_id}/status",
                    "PUT", resp.status_code, 0,
                )
                if resp.status_code == 200:
                    load_agent_capabilities(agent_id)
                else:
                    state.status_message = (
                        f"Status update failed: {resp.status_code}"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Toggle capability failed: {e}",
                f"/api/capabilities/{agent_id}/{rule_id}/status",
            )

    return {"load_workspaces": load_workspaces}
