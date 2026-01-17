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

    def _safe_query(self, query: str) -> list:
        """Execute query with graceful handling of missing types (GAP-UI-EXP-009)."""
        try:
            return self._execute_query(query)
        except Exception:
            # Type may not exist in older TypeDB schemas
            return []

    def get_all_tasks(self, status: str = None, phase: str = None, agent_id: str = None) -> List[Task]:
        """
        Get all tasks from TypeDB with optional filters.

        Per GAP-ARCH-001: Tasks now stored in TypeDB, not in-memory.
        Per GAP-UI-046: Status/resolution lifecycle.
        Per EPIC-DR-001: Optimized from N+1 (16 queries × N tasks) to ~19 batch queries.
        Previous: 50 tasks = 800 queries (7.5s). Now: 50 tasks = 19 queries (~500ms target).

        Args:
            status: Optional filter by status (OPEN, IN_PROGRESS, CLOSED per GAP-UI-046)
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

        # Query 1: Get all tasks with required attributes
        query = f"""
            match $t isa task,
                has task-id $id,
                has task-name $name,
                has task-status $status,
                has phase $phase{", " + filter_clause if filter_clause else ""};
            get $id, $name, $status, $phase;
        """
        results = self._execute_query(query)

        # Build task map for batch attribute assignment
        tasks = []
        task_map = {}
        for r in results:
            task_id = r.get("id")
            task = Task(
                id=task_id,
                name=r.get("name"),
                status=r.get("status"),
                phase=r.get("phase")
            )
            tasks.append(task)
            task_map[task_id] = task

        if not tasks:
            return []

        # Batch fetch all optional attributes (~13 queries instead of 13 × N)
        self._batch_fetch_task_attributes(task_map)

        # Batch fetch relationships (3 queries instead of 3 × N)
        self._batch_fetch_task_relationships(task_map)

        # Apply agent_id filter if specified
        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]

        return tasks

    def _batch_fetch_task_attributes(self, task_map: dict) -> None:
        """Batch fetch all optional attributes for tasks (EPIC-DR-001 optimization)."""
        # Define attribute queries: (attribute_name, query, result_key, task_attr)
        attr_queries = [
            ("task-body", "match $t isa task, has task-id $id, has task-body $v; get $id, $v;", "v", "body"),
            ("task-resolution", "match $t isa task, has task-id $id, has task-resolution $v; get $id, $v;", "v", "resolution"),
            ("gap-reference", "match $t isa task, has task-id $id, has gap-reference $v; get $id, $v;", "v", "gap_id"),
            ("agent-id", "match $t isa task, has task-id $id, has agent-id $v; get $id, $v;", "v", "agent_id"),
            ("task-evidence", "match $t isa task, has task-id $id, has task-evidence $v; get $id, $v;", "v", "evidence"),
            ("task-completed-at", "match $t isa task, has task-id $id, has task-completed-at $v; get $id, $v;", "v", "completed_at"),
            ("task-created-at", "match $t isa task, has task-id $id, has task-created-at $v; get $id, $v;", "v", "created_at"),
            ("task-claimed-at", "match $t isa task, has task-id $id, has task-claimed-at $v; get $id, $v;", "v", "claimed_at"),
            ("task-business", "match $t isa task, has task-id $id, has task-business $v; get $id, $v;", "v", "business"),
            ("task-design", "match $t isa task, has task-id $id, has task-design $v; get $id, $v;", "v", "design"),
            ("task-architecture", "match $t isa task, has task-id $id, has task-architecture $v; get $id, $v;", "v", "architecture"),
            ("task-test", "match $t isa task, has task-id $id, has task-test $v; get $id, $v;", "v", "test_section"),
        ]

        for attr_name, query, result_key, task_attr in attr_queries:
            try:
                results = self._execute_query(query)
                for r in results:
                    task_id = r.get("id")
                    if task_id in task_map:
                        setattr(task_map[task_id], task_attr, r.get(result_key))
            except Exception:
                # Attribute type may not exist in schema (GAP-UI-EXP-009)
                pass

    def _batch_fetch_task_relationships(self, task_map: dict) -> None:
        """Batch fetch relationships for all tasks (EPIC-DR-001 optimization)."""
        # Batch fetch linked rules
        try:
            rules_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                    $r has rule-id $rid;
                get $tid, $rid;
            """)
            for r in rules_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_rules:
                        task_map[tid].linked_rules = []
                    task_map[tid].linked_rules.append(r.get("rid"))
        except Exception:
            pass

        # Batch fetch linked sessions
        try:
            sessions_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (completed-task: $t, hosting-session: $s) isa completed-in;
                    $s has session-id $sid;
                get $tid, $sid;
            """)
            for r in sessions_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_sessions:
                        task_map[tid].linked_sessions = []
                    task_map[tid].linked_sessions.append(r.get("sid"))
        except Exception:
            pass

        # Batch fetch linked commits
        try:
            commits_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (implementing-commit: $c, implemented-task: $t) isa task-commit;
                    $c has commit-sha $sha;
                get $tid, $sha;
            """)
            for r in commits_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_commits:
                        task_map[tid].linked_commits = []
                    task_map[tid].linked_commits.append(r.get("sha"))
        except Exception:
            pass

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

        # All optional queries use _safe_query to handle missing types (GAP-UI-EXP-009)

        # Get optional body attribute
        body_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-body $body;
            get $body;
        ''')
        if body_results:
            task.body = body_results[0].get("body")

        # Get optional task-resolution attribute (GAP-UI-046)
        resolution_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-resolution $res;
            get $res;
        ''')
        if resolution_results:
            task.resolution = resolution_results[0].get("res")

        # Get optional gap-reference attribute
        gap_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has gap-reference $gap;
            get $gap;
        ''')
        if gap_results:
            task.gap_id = gap_results[0].get("gap")

        # Get optional agent-id attribute (E2E tests requirement)
        agent_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has agent-id $agent;
            get $agent;
        ''')
        if agent_results:
            task.agent_id = agent_results[0].get("agent")

        # Get optional task-evidence attribute (E2E tests requirement)
        evidence_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-evidence $ev;
            get $ev;
        ''')
        if evidence_results:
            task.evidence = evidence_results[0].get("ev")

        # Get optional task-completed-at attribute (E2E tests requirement)
        completed_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-completed-at $comp;
            get $comp;
        ''')
        if completed_results:
            task.completed_at = completed_results[0].get("comp")

        # Get optional task-created-at attribute (GAP-UI-035)
        created_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-created-at $created;
            get $created;
        ''')
        if created_results:
            task.created_at = created_results[0].get("created")

        # Get optional task-claimed-at attribute (GAP-UI-035)
        claimed_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-claimed-at $claimed;
            get $claimed;
        ''')
        if claimed_results:
            task.claimed_at = claimed_results[0].get("claimed")

        # Get linked rules via implements-rule relationship
        rules_results = self._safe_query(f'''
            match
                $t isa task, has task-id "{task_id}";
                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                $r has rule-id $rid;
            get $rid;
        ''')
        if rules_results:
            task.linked_rules = [r.get("rid") for r in rules_results]

        # Get linked sessions via completed-in relationship
        sessions_results = self._safe_query(f'''
            match
                $t isa task, has task-id "{task_id}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
                $s has session-id $sid;
            get $sid;
        ''')
        if sessions_results:
            task.linked_sessions = [r.get("sid") for r in sessions_results]

        # Get linked commits via task-commit relationship (GAP-TASK-LINK-002)
        commits_results = self._safe_query(f'''
            match
                $t isa task, has task-id "{task_id}";
                (implementing-commit: $c, implemented-task: $t) isa task-commit;
                $c has commit-sha $sha;
            get $sha;
        ''')
        if commits_results:
            task.linked_commits = [r.get("sha") for r in commits_results]

        # Get task detail sections (GAP-TASK-LINK-004, TASK-TECH-01-v1)
        business_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-business $biz;
            get $biz;
        ''')
        if business_results:
            task.business = business_results[0].get("biz")

        design_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-design $des;
            get $des;
        ''')
        if design_results:
            task.design = design_results[0].get("des")

        arch_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-architecture $arch;
            get $arch;
        ''')
        if arch_results:
            task.architecture = arch_results[0].get("arch")

        test_results = self._safe_query(f'''
            match $t isa task, has task-id "{task_id}", has task-test $test;
            get $test;
        ''')
        if test_results:
            task.test_section = test_results[0].get("test")

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID with all attributes."""
        return self._build_task_from_id(task_id)
