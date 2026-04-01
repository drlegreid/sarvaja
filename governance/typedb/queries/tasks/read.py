"""TypeDB Task Read Queries. Per RULE-032. Created: 2026-01-04."""

import time
from typing import List, Optional

from ...entities import Task


# EPIC-PERF-TELEM-V1 P2: Map TypeDB attribute names → Task dataclass fields
_TASK_ATTR_MAP = {
    "task-body": "body",
    "task-resolution": "resolution",
    "gap-reference": "gap_id",
    "agent-id": "agent_id",
    "task-evidence": "evidence",
    "task-completed-at": "completed_at",
    "task-created-at": "created_at",
    "task-claimed-at": "claimed_at",
    "task-business": "business",
    "task-design": "design",
    "task-architecture": "architecture",
    "task-test": "test_section",
    "item-type": "item_type",
    "document-path": "document_path",
    "task-priority": "priority",
    "task-type": "task_type",
    "task-summary": "summary",
    "resolution-notes": "resolution_notes",
    "task-layer": "layer",
    "task-concern": "concern",
    "task-method": "method",
}

# EPIC-PERF-TELEM-V1 P2: Relation query templates for batch fetch
# (query_template, var_name, task_attr, is_list)
_RELATION_QUERIES = [
    (
        'match $t isa task, has task-id "{tid}"; '
        '(implementing-task: $t, implemented-rule: $r) isa implements-rule; '
        '$r has rule-id $rid; select $rid;',
        "rid", "linked_rules", True,
    ),
    (
        'match $t isa task, has task-id "{tid}"; '
        '(completed-task: $t, hosting-session: $s) isa completed-in; '
        '$s has session-id $sid; select $sid;',
        "sid", "linked_sessions", True,
    ),
    (
        'match $t isa task, has task-id "{tid}"; '
        '(implementing-commit: $c, implemented-task: $t) isa task-commit; '
        '$c has commit-sha $sha; select $sha;',
        "sha", "linked_commits", True,
    ),
    (
        'match $t isa task, has task-id "{tid}"; '
        '(referencing-document: $d, referenced-task: $t) isa document-references-task; '
        '$d has document-path $dpath; select $dpath;',
        "dpath", "linked_documents", True,
    ),
    (
        'match $t isa task, has task-id "{tid}"; '
        '(task-workspace: $w, assigned-task: $t) isa workspace-has-task; '
        '$w has workspace-id $wid; select $wid;',
        "wid", "workspace_id", False,
    ),
]

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
            ("task-summary", "match $t isa task, has task-id $id, has task-summary $v; select $id, $v;", "v", "summary"),
            # P17: Resolution narrative
            ("resolution-notes", "match $t isa task, has task-id $id, has resolution-notes $v; select $id, $v;", "v", "resolution_notes"),
            # EPIC-TASK-TAXONOMY-V2: Orthogonal tag dimensions
            ("task-layer", "match $t isa task, has task-id $id, has task-layer $v; select $id, $v;", "v", "layer"),
            ("task-concern", "match $t isa task, has task-id $id, has task-concern $v; select $id, $v;", "v", "concern"),
            ("task-method", "match $t isa task, has task-id $id, has task-method $v; select $id, $v;", "v", "method"),
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
        # EPIC-GOV-TASKS-V2 Phase 4: workspace assignment
        try:
            ws_results = self._execute_query("""
                match
                    $t isa task, has task-id $tid;
                    (task-workspace: $w, assigned-task: $t) isa workspace-has-task;
                    $w has workspace-id $wid;
                select $tid, $wid;
            """)
            for r in ws_results:
                tid = r.get("tid")
                if tid in task_map:
                    task_map[tid].workspace_id = r.get("wid")
        except Exception:
            pass

    def get_available_tasks(self) -> List[Task]:
        """Get tasks available for agents (status TODO/pending, no agent assigned)."""
        todo_tasks = self.get_all_tasks(status="TODO")
        pending_tasks = self.get_all_tasks(status="pending")
        all_available = todo_tasks + pending_tasks
        return [t for t in all_available if not t.agent_id]

    # ── EPIC-PERF-TELEM-V1 P2: Consolidated query methods ──────────

    def _get_concept_type_label(self, concept) -> Optional[str]:
        """Extract attribute type label from a TypeDB attribute concept."""
        try:
            type_obj = concept.get_type()
            label = type_obj.get_label()
            return label.name if hasattr(label, "name") else str(label)
        except Exception:
            return None

    def _fetch_all_entity_attrs(self, escaped_tid: str) -> Optional[dict]:
        """Fetch ALL attributes of a task in one TypeDB query.

        Returns {type_label: value} or None if task not found.
        Replaces 22 individual _fetch_task_attr() calls + 1 core query.
        """
        query = f'match $t isa task, has task-id "{escaped_tid}"; $t has $a; select $a;'

        if not self._connected:
            return None

        from typedb.driver import TransactionType

        attr_map = {}
        t0 = time.monotonic()

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                iterator = tx.query(query).resolve()
                if iterator is None:
                    self._record_query_timing(t0, query)
                    return None

                for result in iterator:
                    concept = result.get("a")
                    if concept is None:
                        continue
                    type_label = self._get_concept_type_label(concept)
                    value = self._concept_to_value(concept)
                    if type_label and value is not None:
                        attr_map[type_label] = value
        except Exception:
            self._record_query_timing(t0, query)
            return None

        self._record_query_timing(t0, query)
        return attr_map if attr_map else None

    def _fetch_task_relations_batch(self, escaped_tid: str, task) -> None:
        """Fetch all 5 relation types in a single TypeDB transaction.

        Replaces 5 individual _fetch_task_relation() calls with 1 transaction.
        """
        if not self._connected:
            return

        from typedb.driver import TransactionType

        t0 = time.monotonic()

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                for query_tpl, var_name, task_attr, is_list in _RELATION_QUERIES:
                    try:
                        query = query_tpl.format(tid=escaped_tid)
                        iterator = tx.query(query).resolve()
                        values = []
                        if iterator:
                            for result in iterator:
                                concept = result.get(var_name)
                                val = self._concept_to_value(concept) if concept else None
                                if val is not None:
                                    values.append(val)
                        if is_list:
                            setattr(task, task_attr, values)
                        elif values:
                            setattr(task, task_attr, values[0])
                    except Exception:
                        if is_list:
                            setattr(task, task_attr, [])
        except Exception:
            pass

        self._record_query_timing(t0, "batch-relations")

    def _build_task_from_id(self, task_id: str) -> Optional[Task]:
        """Build a full Task object from TypeDB by ID.

        EPIC-PERF-TELEM-V1 P2: Consolidated from 28 queries to 2 operations.
        - Op 1: All attributes via $t has $a (replaces 1 core + 22 attr queries)
        - Op 2: All relations in 1 transaction (replaces 5 relation queries)
        """
        # BUG-302-READ-003: Escape backslash FIRST, then quotes (correct order)
        tid = task_id.replace('\\', '\\\\').replace('"', '\\"')

        # Op 1: All attributes in one query
        attrs = self._fetch_all_entity_attrs(tid)
        if not attrs:
            return None

        task = Task(
            id=task_id,
            name=attrs.get("task-name"),
            status=attrs.get("task-status"),
            phase=attrs.get("phase"),
        )

        # Map optional attributes from consolidated result
        for typedb_attr, task_field in _TASK_ATTR_MAP.items():
            val = attrs.get(typedb_attr)
            if val is not None:
                setattr(task, task_field, val)

        # Op 2: All relations in one transaction
        self._fetch_task_relations_batch(tid, task)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID with all attributes."""
        return self._build_task_from_id(task_id)
