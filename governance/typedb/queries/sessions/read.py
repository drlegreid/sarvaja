"""TypeDB Session Read Queries. Per RULE-032. Created: 2026-01-04."""

import time
from typing import List, Optional
from ...entities import Session


# EPIC-PERF-TELEM-V1 P3: Map TypeDB attribute names → Session dataclass fields
_SESSION_ATTR_MAP = {
    "session-name": "name",
    "session-description": "description",
    "session-file-path": "file_path",
    "started-at": "started_at",
    "completed-at": "completed_at",
    "agent-id": "agent_id",
    "cc-session-uuid": "cc_session_uuid",
    "cc-project-slug": "cc_project_slug",
    "cc-git-branch": "cc_git_branch",
    "cc-external-name": "cc_external_name",
}

# CC integer attributes need int coercion
_SESSION_INT_ATTRS = {
    "cc-tool-count": "cc_tool_count",
    "cc-thinking-chars": "cc_thinking_chars",
    "cc-compaction-count": "cc_compaction_count",
}

# EPIC-PERF-TELEM-V1 P3: Relation query templates for batch fetch
# (query_template, var_name, session_attr, mode: "list"|"dedup"|"count")
_SESSION_RELATION_QUERIES = [
    (
        'match $s isa work-session, has session-id "{sid}"; '
        '(applying-session: $s, applied-rule: $r) isa session-applied-rule; '
        '$r has rule-id $rid; select $rid;',
        "rid", "linked_rules_applied", "list",
    ),
    (
        'match $s isa work-session, has session-id "{sid}"; '
        '(deciding-session: $s, session-made-decision: $d) isa session-decision; '
        '$d has decision-id $did; select $did;',
        "did", "linked_decisions", "list",
    ),
    (
        'match $s isa work-session, has session-id "{sid}"; '
        '(evidence-session: $s, session-evidence: $e) isa has-evidence; '
        '$e has evidence-source $src; select $src;',
        "src", "evidence_files", "dedup",
    ),
    (
        'match $s isa work-session, has session-id "{sid}"; '
        '(completed-task: $t, hosting-session: $s) isa completed-in; '
        'select $t;',
        "t", "tasks_completed", "count",
    ),
]


class SessionReadQueries:
    """Session read query operations for TypeDB. Mixin pattern for TypeDBClient."""

    def get_all_sessions(self) -> List[Session]:
        """Get all work sessions from TypeDB. Per EPIC-DR-001: batch query optimization."""
        query = """
            match $s isa work-session,
                has session-id $id;
            select $id;
        """
        results = self._execute_query(query)
        sessions, session_map = [], {}
        for r in results:
            session_id = r.get("id")
            if session_id:
                session = Session(id=session_id)
                sessions.append(session)
                session_map[session_id] = session
        if not sessions:
            return []
        self._batch_fetch_session_attributes(session_map)
        self._batch_fetch_session_relationships(session_map)
        return sessions

    def _batch_fetch_session_attributes(self, session_map: dict) -> None:
        """Batch fetch all optional attributes for sessions."""
        attr_queries = [
            ("match $s isa work-session, has session-id $id, has session-name $v; select $id, $v;", "v", "name"),
            ("match $s isa work-session, has session-id $id, has session-description $v; select $id, $v;", "v", "description"),
            ("match $s isa work-session, has session-id $id, has session-file-path $v; select $id, $v;", "v", "file_path"),
            ("match $s isa work-session, has session-id $id, has started-at $v; select $id, $v;", "v", "started_at"),
            ("match $s isa work-session, has session-id $id, has agent-id $v; select $id, $v;", "v", "agent_id"),
            # Claude Code session attributes (SESSION-CC-01-v1)
            ("match $s isa work-session, has session-id $id, has cc-session-uuid $v; select $id, $v;", "v", "cc_session_uuid"),
            ("match $s isa work-session, has session-id $id, has cc-project-slug $v; select $id, $v;", "v", "cc_project_slug"),
            ("match $s isa work-session, has session-id $id, has cc-git-branch $v; select $id, $v;", "v", "cc_git_branch"),
            ("match $s isa work-session, has session-id $id, has cc-external-name $v; select $id, $v;", "v", "cc_external_name"),
        ]
        # CC integer attributes (separate to handle type)
        cc_int_queries = [
            ("match $s isa work-session, has session-id $id, has cc-tool-count $v; select $id, $v;", "v", "cc_tool_count"),
            ("match $s isa work-session, has session-id $id, has cc-thinking-chars $v; select $id, $v;", "v", "cc_thinking_chars"),
            ("match $s isa work-session, has session-id $id, has cc-compaction-count $v; select $id, $v;", "v", "cc_compaction_count"),
        ]

        for query, result_key, session_attr in attr_queries:
            try:
                results = self._execute_query(query)
                for r in results:
                    session_id = r.get("id")
                    if session_id in session_map:
                        setattr(session_map[session_id], session_attr, r.get(result_key))
            except Exception:
                pass
        for query, result_key, session_attr in cc_int_queries:
            try:
                results = self._execute_query(query)
                for r in results:
                    session_id = r.get("id")
                    if session_id in session_map:
                        val = r.get(result_key)
                        setattr(session_map[session_id], session_attr, int(val) if val is not None else None)
            except Exception:
                pass
        # BUG-SESSIONS-ONGOING-001: Infer status from completed-at attribute.
        # Previously blindly set ALL sessions without completed-at to "ACTIVE",
        # causing dashboard to show every session as "ongoing".
        try:
            completed_results = self._execute_query("match $s isa work-session, has session-id $id, has completed-at $v; select $id, $v;")
            completed_ids = set()
            for r in completed_results:
                session_id = r.get("id")
                if session_id in session_map:
                    session_map[session_id].completed_at = r.get("v")
                    session_map[session_id].status = "COMPLETED"
                    completed_ids.add(session_id)
            for sid, session in session_map.items():
                if sid not in completed_ids:
                    # Only mark as ACTIVE if session has started_at (real active session).
                    # For ingested/backfilled sessions without completed-at,
                    # the merge layer in get_all_sessions_from_typedb() will
                    # check _sessions_store for the real status.
                    if session.started_at:
                        session.status = "ACTIVE"
                    else:
                        session.status = "UNKNOWN"
        except Exception:
            # On exception, leave entity defaults (status="ACTIVE").
            # The merge layer in get_all_sessions_from_typedb() will
            # check _sessions_store for the real status.
            pass

    def _batch_fetch_session_relationships(self, session_map: dict) -> None:
        """Batch fetch relationships for all sessions."""
        try:
            rules_results = self._execute_query("""
                match
                    $s isa work-session, has session-id $sid;
                    (applying-session: $s, applied-rule: $r) isa session-applied-rule;
                    $r has rule-id $rid;
                select $sid, $rid;
            """)
            for r in rules_results:
                sid = r.get("sid")
                if sid in session_map:
                    if not session_map[sid].linked_rules_applied:
                        session_map[sid].linked_rules_applied = []
                    session_map[sid].linked_rules_applied.append(r.get("rid"))
        except Exception:
            pass
        try:
            decisions_results = self._execute_query("""
                match
                    $s isa work-session, has session-id $sid;
                    (deciding-session: $s, session-made-decision: $d) isa session-decision;
                    $d has decision-id $did;
                select $sid, $did;
            """)
            for r in decisions_results:
                sid = r.get("sid")
                if sid in session_map:
                    if not session_map[sid].linked_decisions:
                        session_map[sid].linked_decisions = []
                    session_map[sid].linked_decisions.append(r.get("did"))
        except Exception:
            pass
        try:
            evidence_results = self._execute_query("""
                match
                    $s isa work-session, has session-id $sid;
                    (evidence-session: $s, session-evidence: $e) isa has-evidence;
                    $e has evidence-source $src;
                select $sid, $src;
            """)
            for r in evidence_results:
                sid = r.get("sid")
                if sid in session_map:
                    if not session_map[sid].evidence_files:
                        session_map[sid].evidence_files = []
                    src = r.get("src")
                    if src and src not in session_map[sid].evidence_files:
                        session_map[sid].evidence_files.append(src)
        except Exception:
            pass
        try:
            tasks_results = self._execute_query("""
                match
                    $s isa work-session, has session-id $sid;
                    (completed-task: $t, hosting-session: $s) isa completed-in;
                select $sid, $t;
            """)
            task_counts = {}
            for r in tasks_results:
                sid = r.get("sid")
                task_counts[sid] = task_counts.get(sid, 0) + 1
            for sid, count in task_counts.items():
                if sid in session_map:
                    session_map[sid].tasks_completed = count
        except Exception:
            pass

    # ── EPIC-PERF-TELEM-V1 P3: Consolidated query methods ──────────

    def _get_concept_type_label(self, concept) -> Optional[str]:
        """Extract attribute type label from a TypeDB attribute concept."""
        try:
            type_obj = concept.get_type()
            label = type_obj.get_label()
            return label.name if hasattr(label, "name") else str(label)
        except Exception:
            return None

    def _fetch_all_session_attrs(self, escaped_sid: str) -> Optional[dict]:
        """Fetch ALL attributes of a session in one TypeDB query.

        Returns {type_label: value} or None if session not found.
        Replaces 13 individual queries (6 scalar + 7 CC attrs).
        """
        query = f'match $s isa work-session, has session-id "{escaped_sid}"; $s has $a; select $a;'

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

    def _fetch_session_relations_batch(self, escaped_sid: str, session) -> None:
        """Fetch all 4 relation types in a single TypeDB transaction.

        Replaces 4 individual relation queries with 1 transaction.
        Handles dedup for evidence_files and count for tasks_completed.
        """
        if not self._connected:
            return

        from typedb.driver import TransactionType

        t0 = time.monotonic()

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                for query_tpl, var_name, session_attr, mode in _SESSION_RELATION_QUERIES:
                    try:
                        query = query_tpl.format(sid=escaped_sid)
                        iterator = tx.query(query).resolve()
                        values = []
                        if iterator:
                            for result in iterator:
                                concept = result.get(var_name)
                                val = self._concept_to_value(concept) if concept else None
                                if val is not None:
                                    values.append(val)
                        if mode == "list":
                            setattr(session, session_attr, values)
                        elif mode == "dedup":
                            setattr(session, session_attr,
                                    list(dict.fromkeys(values)))
                        elif mode == "count":
                            session.tasks_completed = len(values)
                    except Exception:
                        if mode in ("list", "dedup"):
                            setattr(session, session_attr, [])
        except Exception:
            pass

        self._record_query_timing(t0, "batch-session-relations")

    def _build_session_from_id(self, session_id: str) -> Optional[Session]:
        """Build a full Session object from TypeDB by ID.

        EPIC-PERF-TELEM-V1 P3: Consolidated from 19 queries to 2 operations.
        - Op 1: All attributes via $s has $a (replaces 1 existence + 13 attr queries)
        - Op 2: All relations in 1 transaction (replaces 4 relation queries)
        """
        # BUG-310-READ-001: Backslash-first escape order (was quote-only)
        sid = session_id.replace('\\', '\\\\').replace('"', '\\"')

        # Op 1: All attributes in one query
        attrs = self._fetch_all_session_attrs(sid)
        if not attrs:
            return None

        session = Session(id=session_id)

        # Map string attributes from consolidated result
        for typedb_attr, session_field in _SESSION_ATTR_MAP.items():
            val = attrs.get(typedb_attr)
            if val is not None:
                setattr(session, session_field, val)

        # Map integer attributes with coercion
        for typedb_attr, session_field in _SESSION_INT_ATTRS.items():
            val = attrs.get(typedb_attr)
            if val is not None:
                try:
                    setattr(session, session_field, int(val))
                except (ValueError, TypeError):
                    pass

        # BUG-SESSIONS-ONGOING-001: Infer status from completed-at
        if session.completed_at:
            session.status = "COMPLETED"
        elif session.started_at:
            session.status = "ACTIVE"
        else:
            session.status = "UNKNOWN"

        # Op 2: All relations in one transaction
        self._fetch_session_relations_batch(sid, session)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID with all attributes."""
        return self._build_session_from_id(session_id)

    def get_tasks_for_session(self, session_id: str) -> list[dict]:
        """Get all tasks linked to a session via completed-in relation."""
        # BUG-310-READ-001: Backslash-first escape order (was quote-only)
        sid = session_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $s isa work-session, has session-id "{sid}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
                $t has task-id $tid, has task-name $name, has task-status $status;
            select $tid, $name, $status;
        """
        results = self._execute_query(query)

        tasks = []
        for r in results:
            tasks.append({
                "task_id": r.get("tid"),
                "name": r.get("name"),
                "status": r.get("status")
            })

        return tasks
