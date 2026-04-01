"""
TypeDB Task Queries Module.

Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)
Modularized from: governance/typedb/queries/tasks.py (652 lines)

Created: 2026-01-04
Updated: 2026-01-14 - Added TaskRelationshipOperations (GAP-TASK-LINK-003)
Updated: 2026-01-14 - Added TaskDetailOperations (GAP-TASK-LINK-004)

This module combines all task-related query mixins:
- TaskReadQueries: Task read operations
- TaskCRUDOperations: Create/update/delete tasks
- TaskLinkingOperations: Link tasks to rules, sessions, evidence
- TaskRelationshipOperations: Task-to-task relationships (parent/child, blocks)
- TaskDetailOperations: Task detail sections (business, design, arch, test)
"""

from .read import TaskReadQueries
from .crud import TaskCRUDOperations
from .linking import TaskLinkingOperations
from .relationships import TaskRelationshipOperations
from .details import TaskDetailOperations
from .comments import TaskCommentQueries  # SRVJ-FEAT-AUDIT-TRAIL-01 P8


class TaskQueries(
    TaskReadQueries,
    TaskCRUDOperations,
    TaskLinkingOperations,
    TaskRelationshipOperations,
    TaskDetailOperations,
    TaskCommentQueries,
):
    """
    Combined task query and CRUD operations for TypeDB.

    Combines all task-related mixins:
    - TaskReadQueries: get_all_tasks, get_available_tasks, get_task, _build_task_from_id
    - TaskCRUDOperations: insert_task, update_task_status, update_task, delete_task
    - TaskLinkingOperations: link_evidence_to_task, link_task_to_session,
      link_task_to_rule, get_task_evidence
    - TaskRelationshipOperations: link_parent_task, link_blocking_task, link_related_tasks,
      get_task_children, get_task_parent, get_tasks_blocking, get_related_tasks
    - TaskDetailOperations: update_task_business, update_task_design, update_task_architecture,
      update_task_test, update_task_details, get_task_details

    Requires a client with:
    - _execute_query(query)
    - _driver (TypeDB driver)
    - database (database name)

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'TaskQueries',
    'TaskReadQueries',
    'TaskCRUDOperations',
    'TaskLinkingOperations',
    'TaskRelationshipOperations',
    'TaskDetailOperations',
]
