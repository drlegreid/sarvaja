"""
TypeDB Task Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-ARCH-001: Task TypeDB operations.

Created: 2024-12-28
"""

from datetime import datetime
from typing import List, Optional

from ..entities import Task


class TaskQueries:
    """
    Task query operations for TypeDB.

    Requires a client with _execute_query and _client attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_all_tasks(self, status: str = None, phase: str = None, agent_id: str = None) -> List[Task]:
        """
        Get all tasks from TypeDB with optional filters.

        Per GAP-ARCH-001: Tasks now stored in TypeDB, not in-memory.

        Args:
            status: Optional filter by status (TODO, IN_PROGRESS, DONE, BLOCKED)
            phase: Optional filter by phase (P1, P10, etc.)
            agent_id: Optional filter by assigned agent

        Returns:
            List of Task objects
        """
        # Build query with optional filters
        filters = []
        if status:
            filters.append(f'has task-status "{status}"')
        if phase:
            filters.append(f'has phase "{phase}"')

        filter_clause = ", ".join(filters) if filters else ""

        query = f"""
            match $t isa task,
                has task-id $id,
                has task-name $name,
                has task-status $status,
                has phase $phase{", " + filter_clause if filter_clause else ""};
            get $id, $name, $status, $phase;
        """
        results = self._execute_query(query)

        tasks = []
        for r in results:
            task = self._build_task_from_id(r.get("id"))
            if task:
                # Apply agent_id filter (stored as relationship, not queried above)
                if agent_id and task.agent_id != agent_id:
                    continue
                tasks.append(task)

        return tasks

    def get_available_tasks(self) -> List[Task]:
        """
        Get tasks available for agents to claim.

        Per TODO-6: Agent Task Backlog UI.
        Returns tasks with status TODO/pending and no agent_id assigned.
        Handles both uppercase (TODO) and lowercase (pending) status values.
        """
        # Get tasks with both "TODO" and "pending" statuses
        todo_tasks = self.get_all_tasks(status="TODO")
        pending_tasks = self.get_all_tasks(status="pending")
        all_available = todo_tasks + pending_tasks
        return [t for t in all_available if not t.agent_id]

    def _build_task_from_id(self, task_id: str) -> Optional[Task]:
        """Build a full Task object from TypeDB by ID."""
        # Get basic task attributes
        query = f"""
            match $t isa task, has task-id "{task_id}";
            $t has task-name $name,
               has task-status $status,
               has phase $phase;
            get $name, $status, $phase;
        """
        results = self._execute_query(query)
        if not results:
            return None

        r = results[0]
        task = Task(
            id=task_id,
            name=r.get("name"),
            status=r.get("status"),
            phase=r.get("phase")
        )

        # Get optional body attribute
        body_query = f"""
            match $t isa task, has task-id "{task_id}", has task-body $body;
            get $body;
        """
        body_results = self._execute_query(body_query)
        if body_results:
            task.body = body_results[0].get("body")

        # Get optional gap-reference attribute
        gap_query = f"""
            match $t isa task, has task-id "{task_id}", has gap-reference $gap;
            get $gap;
        """
        gap_results = self._execute_query(gap_query)
        if gap_results:
            task.gap_id = gap_results[0].get("gap")

        # Get optional agent-id attribute (E2E tests requirement)
        agent_query = f"""
            match $t isa task, has task-id "{task_id}", has agent-id $agent;
            get $agent;
        """
        agent_results = self._execute_query(agent_query)
        if agent_results:
            task.agent_id = agent_results[0].get("agent")

        # Get optional task-evidence attribute (E2E tests requirement)
        evidence_query = f"""
            match $t isa task, has task-id "{task_id}", has task-evidence $ev;
            get $ev;
        """
        evidence_results = self._execute_query(evidence_query)
        if evidence_results:
            task.evidence = evidence_results[0].get("ev")

        # Get optional task-completed-at attribute (E2E tests requirement)
        completed_query = f"""
            match $t isa task, has task-id "{task_id}", has task-completed-at $comp;
            get $comp;
        """
        completed_results = self._execute_query(completed_query)
        if completed_results:
            task.completed_at = completed_results[0].get("comp")

        # Get linked rules via implements-rule relationship
        rules_query = f"""
            match
                $t isa task, has task-id "{task_id}";
                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                $r has rule-id $rid;
            get $rid;
        """
        rules_results = self._execute_query(rules_query)
        if rules_results:
            task.linked_rules = [r.get("rid") for r in rules_results]

        # Get linked sessions via completed-in relationship
        sessions_query = f"""
            match
                $t isa task, has task-id "{task_id}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
                $s has session-id $sid;
            get $sid;
        """
        sessions_results = self._execute_query(sessions_query)
        if sessions_results:
            task.linked_sessions = [r.get("sid") for r in sessions_results]

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID with all attributes."""
        return self._build_task_from_id(task_id)

    def insert_task(
        self,
        task_id: str,
        name: str,
        status: str,
        phase: str,
        body: str = None,
        gap_id: str = None,
        linked_rules: List[str] = None,
        linked_sessions: List[str] = None
    ) -> Optional[Task]:
        """
        Insert a new task into TypeDB.

        Per GAP-ARCH-001: Full task insertion with optional attributes.

        Args:
            task_id: Unique task ID
            name: Task name/description
            status: Task status (TODO, IN_PROGRESS, DONE, BLOCKED)
            phase: Phase (P1, P10, etc.)
            body: Optional detailed description
            gap_id: Optional linked gap ID
            linked_rules: Optional list of rule IDs this task implements
            linked_sessions: Optional list of session IDs where task was completed

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
                    # Insert base task
                    insert_parts = [
                        f'has task-id "{task_id}"',
                        f'has task-name "{name_escaped}"',
                        f'has task-status "{status}"',
                        f'has phase "{phase}"'
                    ]
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

    def update_task_status(self, task_id: str, status: str, agent_id: str = None, evidence: str = None) -> Optional[Task]:
        """
        Update a task's status (and optionally assign agent and evidence).

        Per TODO-6: Agent task claiming uses this method.

        Args:
            task_id: Task ID to update
            status: New status (TODO, IN_PROGRESS, DONE, BLOCKED)
            agent_id: Optional agent ID to assign
            evidence: Optional completion evidence/notes

        Returns:
            Updated Task object or None if not found
        """
        current = self.get_task(task_id)
        if not current:
            return None

        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # Delete old status
                    delete_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                            $a isa task-status; $a "{current.status}";
                            $t has $a;
                        delete
                            $t has $a;
                    """
                    tx.query.delete(delete_query)

                    # Insert new status
                    insert_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-status "{status}";
                    """
                    tx.query.insert(insert_query)

                    # Update agent_id if provided (per E2E test requirements)
                    if agent_id:
                        # First delete old agent-id if exists
                        if current.agent_id:
                            delete_agent_query = f"""
                                match
                                    $t isa task, has task-id "{task_id}";
                                    $a isa agent-id; $a "{current.agent_id}";
                                    $t has $a;
                                delete
                                    $t has $a;
                            """
                            tx.query.delete(delete_agent_query)

                        # Insert new agent-id
                        insert_agent_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has agent-id "{agent_id}";
                        """
                        tx.query.insert(insert_agent_query)

                    # Update evidence if provided (per E2E test requirements)
                    if evidence:
                        evidence_escaped = evidence.replace('"', '\\"')
                        # First delete old evidence if exists
                        if current.evidence:
                            delete_evidence_query = f"""
                                match
                                    $t isa task, has task-id "{task_id}";
                                    $e isa task-evidence; $t has $e;
                                delete
                                    $t has $e;
                            """
                            tx.query.delete(delete_evidence_query)

                        # Insert new evidence
                        insert_evidence_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-evidence "{evidence_escaped}";
                        """
                        tx.query.insert(insert_evidence_query)

                    # Set completed_at when status is DONE (per E2E test requirements)
                    if status == "DONE" and not current.completed_at:
                        now = datetime.now()
                        timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                        insert_completed_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-completed-at {timestamp_str};
                        """
                        tx.query.insert(insert_completed_query)

                    tx.commit()

            return self.get_task(task_id)
        except Exception as e:
            print(f"Failed to update task {task_id}: {e}")
            return None

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
