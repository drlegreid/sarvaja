"""
Projects Controller.

Per GOV-PROJECT-01-v1: Project hierarchy navigation.
Per RULE-012: Single Responsibility - only project controllers.

Handles: select_project, create_project triggers.
"""

import logging
import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_api_trace, add_error_trace

logger = logging.getLogger(__name__)


def register_project_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """Register project view controllers."""

    @ctrl.trigger("select_project")
    def select_project(project_id):
        """Select a project and load its sessions."""
        if not project_id:
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/projects/{project_id}")
                add_api_trace(
                    state, f"/api/projects/{project_id}", "GET",
                    response.status_code, 0,
                )
                if response.status_code == 200:
                    state.selected_project = response.json()
                    # Load sessions for this project
                    sess_resp = client.get(
                        f"{api_base_url}/api/projects/{project_id}/sessions"
                    )
                    add_api_trace(
                        state, f"/api/projects/{project_id}/sessions",
                        "GET", sess_resp.status_code, 0,
                    )
                    if sess_resp.status_code == 200:
                        data = sess_resp.json()
                        state.project_sessions = (
                            data.get("items", data) if isinstance(data, dict)
                            else data
                        )
                    else:
                        state.project_sessions = []
                        if sess_resp.status_code != 404:
                            logger.warning(
                                "Failed to load sessions for project %s: %s",
                                project_id, sess_resp.status_code,
                            )
                else:
                    state.status_message = f"Project {project_id} not found"
        except Exception as e:
            add_error_trace(
                state, f"Load project failed: {e}",
                f"/api/projects/{project_id}",
            )
            state.status_message = f"Error loading project: {e}"

    @ctrl.trigger("create_project")
    def create_project():
        """Create a new project (placeholder — opens form or dialog)."""
        state.status_message = "Project creation: use MCP mcp__gov-tasks__task_create()"
