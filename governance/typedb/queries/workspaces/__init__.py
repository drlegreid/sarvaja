"""
TypeDB Workspace Queries Module.

Per EPIC-GOV-TASKS-V2 Phase 3: Workspace TypeDB Promotion.
Created: 2026-03-20
"""

from .crud import WorkspaceCRUDOperations
from .read import WorkspaceReadQueries
from .linking import WorkspaceLinkingOperations


class WorkspaceQueries(
    WorkspaceCRUDOperations,
    WorkspaceReadQueries,
    WorkspaceLinkingOperations,
):
    """
    Combined workspace query operations for TypeDB.

    Combines:
    - WorkspaceCRUDOperations: insert/get/list/update/delete workspace
    - WorkspaceReadQueries: get_all_workspaces (batch fetch with filters)
    - WorkspaceLinkingOperations: project + agent linking

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'WorkspaceQueries',
    'WorkspaceCRUDOperations',
    'WorkspaceReadQueries',
    'WorkspaceLinkingOperations',
]
