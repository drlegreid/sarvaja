"""
Workspaces Controller.

Handles: load_workspaces, select_workspace, create_workspace_dialog triggers.
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
                else:
                    state.status_message = (
                        f"Workspace {workspace_id} not found"
                    )
        except Exception as e:
            add_error_trace(
                state, f"Load workspace failed: {e}",
                f"/api/workspaces/{workspace_id}",
            )

    @ctrl.trigger("create_workspace_dialog")
    def create_workspace_dialog():
        """Placeholder for workspace creation dialog."""
        state.status_message = (
            "Workspace creation: use POST /api/workspaces"
        )

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

    return {"load_workspaces": load_workspaces}
