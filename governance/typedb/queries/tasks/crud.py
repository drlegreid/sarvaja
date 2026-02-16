"""
TypeDB Task CRUD Operations.

Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/tasks.py

Created: 2026-01-04
Updated: 2026-01-14 - Extracted update_task_status to status.py
Updated: 2026-01-30 - DRY attribute update helper, print→logger
"""

import logging
from datetime import datetime
from typing import List, Optional

from ...entities import Task
from .status import update_task_status as _update_task_status

logger = logging.getLogger(__name__)


def _update_attribute(tx, task_id: str, attr_name: str, old_value: str, new_value: str):
    """Delete old attribute value and insert new one for a task. DRY helper for TypeDB 3.x."""
    # BUG-TYPEQL-ESCAPE-TASK-001: Escape task_id for TypeQL safety
    tid = task_id.replace('"', '\\"')
    new_escaped = new_value.replace('"', '\\"')
    if old_value:
        old_escaped = old_value.replace('"', '\\"')
        tx.query(f'''
            match $t isa task, has task-id "{tid}", has {attr_name} $v;
                $v == "{old_escaped}";
            delete has $v of $t;
        ''').resolve()
    tx.query(f'''
        match $t isa task, has task-id "{tid}";
        insert $t has {attr_name} "{new_escaped}";
    ''').resolve()


def _set_lifecycle_timestamps(tx, task_id: str, new_status: str, current):
    """Set claimed_at / completed_at timestamps on status transitions.

    Mirrors the logic from update_task_status() so that update_task()
    also handles lifecycle timestamps correctly.
    """
    # BUG-TYPEQL-ESCAPE-TASK-001: Escape task_id
    tid = task_id.replace('"', '\\"')
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    if new_status == "IN_PROGRESS" and not current.claimed_at:
        tx.query(f'''
            match $t isa task, has task-id "{tid}";
            insert $t has task-claimed-at {now_str};
        ''').resolve()

    if new_status in ("DONE", "CLOSED") and not current.completed_at:
        tx.query(f'''
            match $t isa task, has task-id "{tid}";
            insert $t has task-completed-at {now_str};
        ''').resolve()


class TaskCRUDOperations:
    """
    Task CRUD operations for TypeDB.

    Requires a client with _execute_query, _driver, database, and get_task attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def insert_task(
        self,
        task_id: str,
        name: str,
        status: str,
        phase: str,
        body: str = None,
        gap_id: str = None,
        linked_rules: List[str] = None,
        linked_sessions: List[str] = None,
        resolution: str = "NONE",
        item_type: str = None,
        document_path: str = None,
        agent_id: str = None,
        priority: str = None,
        task_type: str = None
    ) -> Optional[Task]:
        """
        Insert a new task into TypeDB.

        Per GAP-ARCH-001: Full task insertion with optional attributes.
        Per GAP-UI-046: Status/resolution lifecycle.
        Per GAP-GAPS-TASKS-001: Unified work item support.

        Args:
            task_id: Unique task ID
            name: Task name/description
            status: Task status (OPEN, IN_PROGRESS, CLOSED per GAP-UI-046)
            phase: Phase (P1, P10, etc.)
            body: Optional detailed description
            gap_id: Optional linked gap ID
            linked_rules: Optional list of rule IDs this task implements
            linked_sessions: Optional list of session IDs where task was completed
            resolution: Task resolution (NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED)
            item_type: Work item type - "gap", "task", or "rd" (GAP-GAPS-TASKS-001)
            document_path: Path to source document (GAP-GAPS-TASKS-001)

        Returns:
            Created Task object or None if failed
        """
        from typedb.driver import TransactionType

        # Escape strings
        name_escaped = name.replace('"', '\\"')
        body_escaped = body.replace('"', '\\"') if body else None

        try:
            # TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Insert base task with created_at timestamp (GAP-UI-035)
                now = datetime.now()
                timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')

                # BUG-TYPEQL-ESCAPE-001: Escape all user-provided fields
                status_escaped = status.replace('"', '\\"') if status else "TODO"
                phase_escaped = phase.replace('"', '\\"') if phase else ""

                # BUG-TYPEQL-ESCAPE-TASK-001: Escape task_id
                task_id_escaped = task_id.replace('"', '\\"')
                insert_parts = [
                    f'has task-id "{task_id_escaped}"',
                    f'has task-name "{name_escaped}"',
                    f'has task-status "{status_escaped}"',
                    f'has phase "{phase_escaped}"',
                    f'has task-created-at {timestamp_str}'
                ]
                # GAP-UI-046: task-resolution (may not exist in older schemas)
                if resolution:
                    resolution_escaped = resolution.replace('"', '\\"')
                    insert_parts.append(f'has task-resolution "{resolution_escaped}"')
                if body_escaped:
                    insert_parts.append(f'has task-body "{body_escaped}"')
                if gap_id:
                    gap_id_escaped = gap_id.replace('"', '\\"')
                    insert_parts.append(f'has gap-reference "{gap_id_escaped}"')
                # GAP-GAPS-TASKS-001: Unified work item attributes
                if item_type:
                    item_type_escaped = item_type.replace('"', '\\"')
                    insert_parts.append(f'has item-type "{item_type_escaped}"')
                if document_path:
                    doc_path_escaped = document_path.replace('"', '\\"')
                    insert_parts.append(f'has document-path "{doc_path_escaped}"')
                if agent_id:
                    agent_id_escaped = agent_id.replace('"', '\\"')
                    insert_parts.append(f'has agent-id "{agent_id_escaped}"')
                # BUG-TASK-TAXONOMY-001: Task classification
                if priority:
                    priority_escaped = priority.replace('"', '\\"')
                    insert_parts.append(f'has task-priority "{priority_escaped}"')
                if task_type:
                    task_type_escaped = task_type.replace('"', '\\"')
                    insert_parts.append(f'has task-type "{task_type_escaped}"')

                insert_query = f"""
                    insert $t isa task,
                        {", ".join(insert_parts)};
                """
                tx.query(insert_query).resolve()

                # Create relationships to rules
                if linked_rules:
                    for rule_id in linked_rules:
                        # BUG-TYPEQL-ESCAPE-TASK-001: Escape IDs in relationship queries
                        rid = rule_id.replace('"', '\\"')
                        rel_query = f"""
                            match
                                $t isa task, has task-id "{task_id_escaped}";
                                $r isa rule-entity, has rule-id "{rid}";
                            insert
                                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                        """
                        tx.query(rel_query).resolve()

                # Create relationships to sessions
                if linked_sessions:
                    for session_id in linked_sessions:
                        # BUG-TYPEQL-ESCAPE-TASK-001: Escape session_id
                        sid = session_id.replace('"', '\\"')
                        rel_query = f"""
                            match
                                $t isa task, has task-id "{task_id_escaped}";
                                $s isa work-session, has session-id "{sid}";
                            insert
                                (completed-task: $t, hosting-session: $s) isa completed-in;
                        """
                        tx.query(rel_query).resolve()

                tx.commit()

            return self.get_task(task_id)
        except Exception as e:
            logger.error(f"Failed to insert task {task_id}: {e}")
            return None

    def update_task_status(
        self,
        task_id: str,
        status: str,
        agent_id: str = None,
        evidence: str = None,
        resolution: str = None
    ) -> Optional[Task]:
        """
        Update a task's status (and optionally assign agent, evidence, resolution).

        Per TODO-6: Agent task claiming uses this method.
        Per GAP-UI-046: Status/resolution lifecycle.
        Delegates to status.py per DOC-SIZE-01-v1.

        Args:
            task_id: Task ID to update
            status: New status (OPEN, IN_PROGRESS, CLOSED per GAP-UI-046)
            agent_id: Optional agent ID to assign
            evidence: Optional completion evidence/notes
            resolution: Optional resolution (NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED)

        Returns:
            Updated Task object or None if not found
        """
        return _update_task_status(self, task_id, status, agent_id, evidence, resolution)

    def update_task(
        self,
        task_id: str,
        status: str = None,
        name: str = None,
        phase: str = None,
        item_type: str = None,
        document_path: str = None,
        priority: str = None,
        task_type: str = None
    ) -> bool:
        """
        Update a task's attributes in TypeDB.

        Per P10.7-10.10: General task update method for MCP tools.
        Per GAP-GAPS-TASKS-001: Unified work item support.

        Args:
            task_id: Task ID to update
            status: New status (optional)
            name: New name (optional)
            phase: New phase (optional)
            item_type: Work item type - "gap", "task", or "rd" (optional)
            document_path: Path to source document (optional)

        Returns:
            True if update succeeded, False otherwise
        """
        current = self.get_task(task_id)
        if not current:
            return False

        from typedb.driver import TransactionType

        try:
            # TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                if status and status != current.status:
                    _update_attribute(tx, task_id, "task-status", current.status, status)
                    # Lifecycle timestamps — mirror update_task_status() logic
                    _set_lifecycle_timestamps(tx, task_id, status, current)
                elif status and status == current.status:
                    # Repair: set missing timestamps even when status unchanged
                    _set_lifecycle_timestamps(tx, task_id, status, current)
                if name and name != current.name:
                    _update_attribute(tx, task_id, "task-name", current.name, name)
                if phase and phase != current.phase:
                    _update_attribute(tx, task_id, "phase", current.phase, phase)
                if item_type:
                    current_item_type = getattr(current, 'item_type', None)
                    if current_item_type != item_type:
                        _update_attribute(tx, task_id, "item-type", current_item_type, item_type)
                if document_path:
                    current_doc_path = getattr(current, 'document_path', None)
                    if current_doc_path != document_path:
                        _update_attribute(tx, task_id, "document-path", current_doc_path, document_path)
                # BUG-TASK-TAXONOMY-001: Task classification
                if priority:
                    current_priority = getattr(current, 'priority', None)
                    if current_priority != priority:
                        _update_attribute(tx, task_id, "task-priority", current_priority, priority)
                if task_type:
                    current_task_type = getattr(current, 'task_type', None)
                    if current_task_type != task_type:
                        _update_attribute(tx, task_id, "task-type", current_task_type, task_type)
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from TypeDB."""
        from typedb.driver import TransactionType

        # BUG-TYPEQL-ESCAPE-TASK-001: Escape task_id for TypeQL safety
        task_id_escaped = task_id.replace('"', '\\"')

        try:
            # TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete relationships first
                rel_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $rel (implementing-task: $t) isa implements-rule;
                    delete
                        $rel isa implements-rule;
                """
                try:
                    tx.query(rel_query).resolve()
                except Exception:
                    pass  # Relationship may not exist

                rel_query2 = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $rel (completed-task: $t) isa completed-in;
                    delete
                        $rel isa completed-in;
                """
                try:
                    tx.query(rel_query2).resolve()
                except Exception:
                    pass

                # Delete task entity (TypeDB 3.x: delete $var; not $var isa type;)
                delete_query = f"""
                    match $t isa task, has task-id "{task_id_escaped}";
                    delete $t;
                """
                tx.query(delete_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
