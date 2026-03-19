"""Workspaces View Subpackage."""
from .list import build_workspaces_list_view
from .detail import build_workspace_detail_view
from .form import build_workspace_form_view

__all__ = [
    "build_workspaces_list_view",
    "build_workspace_detail_view",
    "build_workspace_form_view",
]
