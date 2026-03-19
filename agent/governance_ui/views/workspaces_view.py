"""
Workspaces View for Governance Dashboard.

Per RULE-012: Single Responsibility - only workspace list/detail/form UI.
Entry point for the workspaces view module.
"""

from .workspaces import (
    build_workspaces_list_view,
    build_workspace_detail_view,
    build_workspace_form_view,
)


def build_workspaces_view() -> None:
    """Build the complete Workspaces view including list, detail, and form."""
    build_workspaces_list_view()
    build_workspace_detail_view()
    build_workspace_form_view()
