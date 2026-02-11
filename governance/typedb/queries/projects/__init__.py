"""
TypeDB Project Queries Module.

Per GOV-PROJECT-01-v1: Project hierarchy management.
Created: 2026-02-11
"""

from .crud import ProjectCRUDOperations
from .linking import ProjectLinkingOperations


class ProjectQueries(
    ProjectCRUDOperations,
    ProjectLinkingOperations,
):
    """
    Combined project query operations for TypeDB.

    Combines:
    - ProjectCRUDOperations: insert/get/list/delete project
    - ProjectLinkingOperations: link project↔plan, plan↔epic, epic↔task, project↔session

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'ProjectQueries',
    'ProjectCRUDOperations',
    'ProjectLinkingOperations',
]
