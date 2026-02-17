"""TypeDB Task Read Queries. Per RULE-032. Created: 2026-01-04."""

from typing import List, Optional

from ...entities import Task

class TaskReadQueries:
    """Task read query operations for TypeDB. Mixin pattern for TypeDBClient."""

    def _safe_query(self, query: str) -> list:
        """Execute query with graceful handling of missing types (GAP-UI-EXP-009)."""
        try:
            return self._execute_query(query)
        except Exception:
            # Type may not exist in older TypeDB schemas
            return []

    def _fetch_task_attr(self, task_id: str, attr_name: str, var_name: str) -> Optional[str]:
        """Fetch a single optional attribute for a task. DRY helper for _build_task_from_id."""
        # BUG-298-READ-001: Escape backslash FIRST, then quotes (correct order)
        tid = task_id.replace('\\', '\\\\').replace('"', '\\"')
        results = self._safe_query(
            f'match $t isa task, has task-id "{tid}", has {attr_name} ${var_name}; select ${var_name};'
        )
        return results[0].get(var_name) if results else None

    def _fetch_task_relation(self, task_id: str, query: str, var_name: str) -> List[str]:
        """Fetch a list of related IDs for a task. DRY helper for relationship queries."""
        # BUG-298-READ-001: Escape backslash FIRST, then quotes (correct order)
        tid = task_id.replace('\\', '\\\\').replace('"', '\\"')
        results = self._safe_query(query.format(task_id=tid))
        # BUG-TASK-EXTRACT-002: Return [] not None when no results (matches List[str] return type)
        return [r.get(var_name) for r in results] if results else []

    def get_all_tasks(self, status: str = None, phase: str = None, agent_id: str = None) -> List[Task]:
        """Get all tasks with optional filters. Per EPIC-DR-001: batch queries optimization."""
        filters = []
        if status:
            # BUG-298-READ-002: Escape backslash FIRST, then quotes (correct order)
            status_esc = status.replace('\\', '\\\\').replace('"', '\\"')
            filters.append(f'has task-status "{status_esc}"')
        if phase:
            phase_esc = phase.replace('\\', '\\\\').replace('"', '\\"')
            filters.append(f'has phase "{phase_esc}"')

        filter_clause = ", ".join(filters) if filters else ""
        query = f"""
            match $t isa task,
                has task-id $id,
                has task-name $name,
                has task-status $status,
                has phase $phase{", " + filter_clause if filter_clause else ""};
            select $id, $name, $status, $phase;
        """
        results = self._execute_query(query)
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
        self._batch_fetch_task_attributes(task_map)
        self._batch_fetch_task_relationships(task_map)
        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]

        return tasks

    def _batch_fetch_task_attributes(self, task_map: dict) -> None:
        """Batch fetch all optional attributes for tasks."""
        attr_queries = [
            ("task-body", "match $t isa task, has task-id $id, has task-body $v; select $id, $v;", "v", "body"),
            ("task-resolution", "match $t isa task, has task-id $id, has task-resolution $v; select $id, $v;", "v", "resolution"),
            ("gap-reference", "match $t isa task, has task-id $id, has gap-reference $v; select $id, $v;", "v", "gap_id"),
            ("agent-id", "match $t isa task, has task-id $id, has agent-id $v; select $id, $v;", "v", "agent_id"),
            ("task-evidence", "match $t isa task, has task-id $id, has task-evidence $v; select $id, $v;", "v", "evidence"),
            ("task-completed-at", "match $t isa task, has task-id $id, has task-completed-at $v; select $id, $v;", "v", "completed_at"),
            ("task-created-at", "match $t isa task, has task-id $id, has task-created-at $v; select $id, $v;", "v", "created_at"),
            ("task-claimed-at", "match $t isa task, has task-id $id, has task-claimed-at $v; select $id, $v;", "v", "claimed_at"),
            ("task-business", "match $t isa task, has task-id $id, has task-business $v; select $id, $v;", "v", "business"),
            ("task-design", "match $t isa task, has task-id $id, has task-design $v; select $id, $v;", "v", "design"),
            ("task-architecture", "match $t isa task, has task-id $id, has task-architecture $v; select $id, $v;", "v", "architecture"),
            ("task-test", "match $t isa task, has task-id $id, has task-test $v; select $id, $v;", "v", "test_section"),
            # GAP-GAPS-TASKS-001: Unified work item attributes
            ("item-type", "match $t isa task, has task-id $id, has item-type $v; select $id, $v;", "v", "item_type"),
            ("document-path", "match $t isa task, has task-id $id, has document-path $v; select $id, $v;", "v", "document_path"),
            # BUG-TASK-TAXONOMY-001: Task classification
            ("task-priority", "match $t isa task, has task-id $id, has task-priority $v; select $id, $v;", "v", "priority"),
            ("task-type", "match $t isa task, has task-id $id, has task-type $v; select $id, $v;", "v", "task_type"),
        ]

        for attr_name, query, result_key, task_attr in attr_queries:
            try:
                results = self._execute_query(query)
                for r in results:
                    task_id = r.get("id")
                    if task_id in task_map:
                        setattr(task_map[task_id], task_attr, r.get(result_key))
            except Exception:
                pass

    def _batch_fetch_task_relationships(self, task_map: dict) -> None:
        """Batch fetch relationships for all tasks."""
        try:
            rules_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                    $r has rule-id $rid;
                select $tid, $rid;
            """)
            for r in rules_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_rules:
                        task_map[tid].linked_rules = []
                    task_map[tid].linked_rules.append(r.get("rid"))
        except Exception:
            pass
        try:
            sessions_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (completed-task: $t, hosting-session: $s) isa completed-in;
                    $s has session-id $sid;
                select $tid, $sid;
            """)
            for r in sessions_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_sessions:
                        task_map[tid].linked_sessions = []
                    task_map[tid].linked_sessions.append(r.get("sid"))
        except Exception:
            pass
        try:
            commits_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (implementing-commit: $c, implemented-task: $t) isa task-commit;
                    $c has commit-sha $sha;
                select $tid, $sha;
            """)
            for r in commits_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_commits:
                        task_map[tid].linked_commits = []
                    task_map[tid].linked_commits.append(r.get("sha"))
        except Exception:
            pass
        # Task document management: linked documents
        try:
            docs_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    $d isa document, has document-path $dpath;
                    (referencing-document: $d, referenced-task: $t) isa document-references-task;
                select $tid, $dpath;
            """)
            for r in docs_results:
                tid = r.get("tid")
                if tid in task_map:
                    if not task_map[tid].linked_documents:
                        task_map[tid].linked_documents = []
                    task_map[tid].linked_documents.append(r.get("dpath"))
        except Exception:
            pass

    def get_available_tasks(self) -> List[Task]:
        """Get tasks available for agents (status TODO/pending, no agent assigned)."""
        todo_tasks = self.get_all_tasks(status="TODO")
        pending_tasks = self.get_all_tasks(status="pending")
        all_available = todo_tasks + pending_tasks
        return [t for t in all_available if not t.agent_id]

    def _build_task_from_id(self, task_id: str) -> Optional[Task]:
        """Build a full Task object from TypeDB by ID."""
        # BUG-TYPEQL-ESCAPE-TASK-002: Escape task_id for TypeQL safety
        tid = task_id.replace('"', '\\"')
        query = f"""
            match $t isa task, has task-id "{tid}";
            $t has task-name $name,
               has task-status $status,
               has phase $phase;
            select $name, $status, $phase;
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

        # Fetch all optional scalar attributes via DRY helper (GAP-UI-EXP-009)
        optional_attrs = [
            ("task-body", "body", "body"),
            ("task-resolution", "res", "resolution"),        # GAP-UI-046
            ("gap-reference", "gap", "gap_id"),
            ("agent-id", "agent", "agent_id"),
            ("task-evidence", "ev", "evidence"),
            ("task-completed-at", "comp", "completed_at"),
            ("task-created-at", "created", "created_at"),    # GAP-UI-035
            ("task-claimed-at", "claimed", "claimed_at"),    # GAP-UI-035
            ("task-business", "biz", "business"),            # TASK-TECH-01-v1
            ("task-design", "des", "design"),
            ("task-architecture", "arch", "architecture"),
            ("task-test", "test", "test_section"),
            ("item-type", "itype", "item_type"),             # GAP-GAPS-TASKS-001
            ("document-path", "dpath", "document_path"),
            ("task-priority", "pri", "priority"),              # BUG-TASK-TAXONOMY-001
            ("task-type", "ttype", "task_type"),               # BUG-TASK-TAXONOMY-001
        ]
        for attr_name, var_name, task_attr in optional_attrs:
            value = self._fetch_task_attr(task_id, attr_name, var_name)
            if value is not None:
                setattr(task, task_attr, value)

        # Fetch relationship lists via DRY helper
        task.linked_rules = self._fetch_task_relation(task_id, '''
            match $t isa task, has task-id "{task_id}";
                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                $r has rule-id $rid; select $rid;''', "rid")
        task.linked_sessions = self._fetch_task_relation(task_id, '''
            match $t isa task, has task-id "{task_id}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
                $s has session-id $sid; select $sid;''', "sid")
        task.linked_commits = self._fetch_task_relation(task_id, '''
            match $t isa task, has task-id "{task_id}";
                (implementing-commit: $c, implemented-task: $t) isa task-commit;
                $c has commit-sha $sha; select $sha;''', "sha")
        task.linked_documents = self._fetch_task_relation(task_id, '''
            match $t isa task, has task-id "{task_id}";
                (referencing-document: $d, referenced-task: $t) isa document-references-task;
                $d has document-path $dpath; select $dpath;''', "dpath")

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID with all attributes."""
        return self._build_task_from_id(task_id)
