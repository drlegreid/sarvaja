"""
TypeDB Task CRUD Operations.

Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/tasks.py

Created: 2026-01-04
Updated: 2026-01-14 - Extracted update_task_status to status.py
"""

from datetime import datetime
from typing import List, Optional

from ...entities import Task
from .status import update_task_status as _update_task_status


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
        document_path: str = None
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

                insert_parts = [
                    f'has task-id "{task_id}"',
                    f'has task-name "{name_escaped}"',
                    f'has task-status "{status}"',
                    f'has phase "{phase}"',
                    f'has task-created-at {timestamp_str}'
                ]
                # GAP-UI-046: task-resolution (may not exist in older schemas)
                if resolution:
                    insert_parts.append(f'has task-resolution "{resolution}"')
                if body_escaped:
                    insert_parts.append(f'has task-body "{body_escaped}"')
                if gap_id:
                    insert_parts.append(f'has gap-reference "{gap_id}"')
                # GAP-GAPS-TASKS-001: Unified work item attributes
                if item_type:
                    insert_parts.append(f'has item-type "{item_type}"')
                if document_path:
                    doc_path_escaped = document_path.replace('"', '\\"')
                    insert_parts.append(f'has document-path "{doc_path_escaped}"')

                insert_query = f"""
                    insert $t isa task,
                        {", ".join(insert_parts)};
                """
                tx.query(insert_query).resolve()

                # Create relationships to rules
                if linked_rules:
                    for rule_id in linked_rules:
                        rel_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $r isa rule-entity, has rule-id "{rule_id}";
                            insert
                                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                        """
                        tx.query(rel_query).resolve()

                # Create relationships to sessions
                if linked_sessions:
                    for session_id in linked_sessions:
                        rel_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                (completed-task: $t, hosting-session: $s) isa completed-in;
                        """
                        tx.query(rel_query).resolve()

                tx.commit()

            return self.get_task(task_id)
        except Exception as e:
            print(f"Failed to insert task {task_id}: {e}")
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
        document_path: str = None
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
                # Update status if provided
                if status and status != current.status:
                    # TypeDB 3.x: has $var of $entity
                    delete_query = f"""
                        match
                            $t isa task, has task-id "{task_id}", has task-status $s;
                            $s == "{current.status}";
                        delete
                            has $s of $t;
                    """
                    tx.query(delete_query).resolve()
                    insert_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-status "{status}";
                    """
                    tx.query(insert_query).resolve()

                # Update name if provided
                if name and name != current.name:
                    if current.name:
                        # TypeDB 3.x: has $var of $entity
                        name_escaped = current.name.replace('"', '\\"')
                        delete_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has task-name $n;
                                $n == "{name_escaped}";
                            delete
                                has $n of $t;
                        """
                        tx.query(delete_query).resolve()
                    insert_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-name "{name_escaped}";
                    """
                    tx.query(insert_query).resolve()

                # Update phase if provided
                if phase and phase != current.phase:
                    phase_escaped = phase.replace('"', '\\"')
                    if current.phase:
                        current_phase_escaped = current.phase.replace('"', '\\"')
                        # TypeDB 3.x: has $var of $entity
                        delete_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has phase $p;
                                $p == "{current_phase_escaped}";
                            delete
                                has $p of $t;
                        """
                        tx.query(delete_query).resolve()
                    insert_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has phase "{phase_escaped}";
                    """
                    tx.query(insert_query).resolve()

                # GAP-GAPS-TASKS-001: Update item_type if provided
                if item_type:
                    item_type_escaped = item_type.replace('"', '\\"')
                    current_item_type = getattr(current, 'item_type', None)
                    if current_item_type and current_item_type != item_type:
                        current_item_escaped = current_item_type.replace('"', '\\"')
                        delete_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has item-type $it;
                                $it == "{current_item_escaped}";
                            delete
                                has $it of $t;
                        """
                        tx.query(delete_query).resolve()
                    if current_item_type != item_type:
                        insert_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has item-type "{item_type_escaped}";
                        """
                        tx.query(insert_query).resolve()

                # GAP-GAPS-TASKS-001: Update document_path if provided
                if document_path:
                    current_doc_path = getattr(current, 'document_path', None)
                    doc_path_escaped = document_path.replace('"', '\\"')
                    if current_doc_path and current_doc_path != document_path:
                        current_escaped = current_doc_path.replace('"', '\\"')
                        delete_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has document-path $dp;
                                $dp == "{current_escaped}";
                            delete
                                has $dp of $t;
                        """
                        tx.query(delete_query).resolve()
                    if current_doc_path != document_path:
                        insert_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has document-path "{doc_path_escaped}";
                        """
                        tx.query(insert_query).resolve()

                tx.commit()
            return True
        except Exception as e:
            print(f"Failed to update task {task_id}: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from TypeDB."""
        from typedb.driver import TransactionType

        try:
            # TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete relationships first
                rel_query = f"""
                    match
                        $t isa task, has task-id "{task_id}";
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
                        $t isa task, has task-id "{task_id}";
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
                    match $t isa task, has task-id "{task_id}";
                    delete $t;
                """
                tx.query(delete_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            print(f"Failed to delete task {task_id}: {e}")
            return False
