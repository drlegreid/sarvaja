"""
TypeDB Task Queries Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/typedb/queries/tasks.py (652 lines)

Created: 2026-01-04

This module combines all task-related query mixins:
- TaskReadQueries: Task read operations
- TaskCRUDOperations: Create/update/delete tasks
- TaskLinkingOperations: Link tasks to rules, sessions, evidence
"""

from .read import TaskReadQueries
from .crud import TaskCRUDOperations
from .linking import TaskLinkingOperations


class TaskQueries(
    TaskReadQueries,
    TaskCRUDOperations,
    TaskLinkingOperations
):
    """
    Combined task query and CRUD operations for TypeDB.

    Combines all task-related mixins:
    - TaskReadQueries: get_all_tasks, get_available_tasks, get_task, _build_task_from_id
    - TaskCRUDOperations: insert_task, update_task_status, update_task, delete_task
    - TaskLinkingOperations: link_evidence_to_task, link_task_to_session,
      link_task_to_rule, get_task_evidence

    Requires a client with:
    - _execute_query(query)
    - _client (TypeDB client)
    - database (property for database name)

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'TaskQueries',
    'TaskReadQueries',
    'TaskCRUDOperations',
    'TaskLinkingOperations',
]
