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

    Requires a client with _execute_query, _client, database, and get_task attributes.
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
        resolution: str = "NONE"
    ) -> Optional[Task]:
        """
        Insert a new task into TypeDB.

        Per GAP-ARCH-001: Full task insertion with optional attributes.
        Per GAP-UI-046: Status/resolution lifecycle.

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

        Returns:
            Created Task object or None if failed
        """
        from typedb.driver import SessionType, TransactionType

        # Escape strings
        name_escaped = name.replace('"', '\\"')
        body_escaped = body.replace('"', '\\"') if body else None

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
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

                    insert_query = f"""
                        insert $t isa task,
                            {", ".join(insert_parts)};
                    """
                    tx.query.insert(insert_query)

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
                            tx.query.insert(rel_query)

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
                            tx.query.insert(rel_query)

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

    def update_task(self, task_id: str, status: str = None, name: str = None, phase: str = None) -> bool:
        """
        Update a task's attributes in TypeDB.

        Per P10.7-10.10: General task update method for MCP tools.

        Args:
            task_id: Task ID to update
            status: New status (optional)
            name: New name (optional)
            phase: New phase (optional)

        Returns:
            True if update succeeded, False otherwise
        """
        current = self.get_task(task_id)
        if not current:
            return False

        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # Update status if provided
                    if status and status != current.status:
                        delete_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $a isa task-status; $a "{current.status}";
                                $t has $a;
                            delete
                                $t has $a;
                        """
                        tx.query.delete(delete_query)
                        insert_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-status "{status}";
                        """
                        tx.query.insert(insert_query)

                    # Update name if provided
                    if name and name != current.name:
                        if current.name:
                            delete_query = f"""
                                match
                                    $t isa task, has task-id "{task_id}";
                                    $a isa task-name; $a "{current.name}";
                                    $t has $a;
                                delete
                                    $t has $a;
                            """
                            tx.query.delete(delete_query)
                        insert_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-name "{name}";
                        """
                        tx.query.insert(insert_query)

                    # Update phase if provided
                    if phase and phase != current.phase:
                        if current.phase:
                            delete_query = f"""
                                match
                                    $t isa task, has task-id "{task_id}";
                                    $a isa phase; $a "{current.phase}";
                                    $t has $a;
                                delete
                                    $t has $a;
                            """
                            tx.query.delete(delete_query)
                        insert_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has phase "{phase}";
                        """
                        tx.query.insert(insert_query)

                    tx.commit()
            return True
        except Exception as e:
            print(f"Failed to update task {task_id}: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from TypeDB."""
        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # Delete relationships first
                    rel_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                            $rel (implementing-task: $t) isa implements-rule;
                        delete
                            $rel isa implements-rule;
                    """
                    try:
                        tx.query.delete(rel_query)
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
                        tx.query.delete(rel_query2)
                    except Exception:
                        pass

                    # Delete task entity
                    delete_query = f"""
                        match $t isa task, has task-id "{task_id}";
                        delete $t isa task;
                    """
                    tx.query.delete(delete_query)
                    tx.commit()

            return True
        except Exception as e:
            print(f"Failed to delete task {task_id}: {e}")
            return False
