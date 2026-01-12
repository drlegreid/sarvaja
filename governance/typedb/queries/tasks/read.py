"""
TypeDB Task Read Queries.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/tasks.py

Created: 2026-01-04
"""

from typing import List, Optional

from ...entities import Task


class TaskReadQueries:
    """
    Task read query operations for TypeDB.

    Requires a client with _execute_query attribute.
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

        # Get optional task-created-at attribute (GAP-UI-035: datetime columns)
        created_query = f"""
            match $t isa task, has task-id "{task_id}", has task-created-at $created;
            get $created;
        """
        created_results = self._execute_query(created_query)
        if created_results:
            task.created_at = created_results[0].get("created")

        # Get optional task-claimed-at attribute (GAP-UI-035: datetime columns)
        claimed_query = f"""
            match $t isa task, has task-id "{task_id}", has task-claimed-at $claimed;
            get $claimed;
        """
        claimed_results = self._execute_query(claimed_query)
        if claimed_results:
            task.claimed_at = claimed_results[0].get("claimed")

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
