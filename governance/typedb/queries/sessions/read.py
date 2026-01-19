"""TypeDB Session Read Queries. Per RULE-032. Created: 2026-01-04."""

from typing import List, Optional
from ...entities import Session

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
        try:
            completed_results = self._execute_query("match $s isa work-session, has session-id $id, has completed-at $v; select $id, $v;")
            completed_ids = set()
            for r in completed_results:
                session_id = r.get("id")
                if session_id in session_map:
                    session_map[session_id].completed_at, session_map[session_id].status = r.get("v"), "COMPLETED"
                    completed_ids.add(session_id)
            for sid, session in session_map.items():
                if sid not in completed_ids:
                    session.status = "ACTIVE"
        except Exception:
            for session in session_map.values():
                session.status = "ACTIVE"

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
                    session_map[sid].evidence_files.append(r.get("src"))
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

    def _build_session_from_id(self, session_id: str) -> Optional[Session]:
        """Build a full Session object from TypeDB by ID."""
        session = Session(id=session_id)
        name_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has session-name $name; select $name;')
        if name_results:
            session.name = name_results[0].get("name")
        desc_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has session-description $desc; select $desc;')
        if desc_results:
            session.description = desc_results[0].get("desc")
        path_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has session-file-path $path; select $path;')
        if path_results:
            session.file_path = path_results[0].get("path")
        start_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has started-at $start; select $start;')
        if start_results:
            session.started_at = start_results[0].get("start")
        end_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has completed-at $end; select $end;')
        if end_results:
            session.completed_at, session.status = end_results[0].get("end"), "COMPLETED"
        else:
            session.status = "ACTIVE"
        agent_results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}", has agent-id $agent; select $agent;')
        if agent_results:
            session.agent_id = agent_results[0].get("agent")
        rules_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (applying-session: $s, applied-rule: $r) isa session-applied-rule;
                $r has rule-id $rid;
            select $rid;
        """
        rules_results = self._execute_query(rules_query)
        if rules_results:
            session.linked_rules_applied = [r.get("rid") for r in rules_results]
        decisions_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (deciding-session: $s, session-made-decision: $d) isa session-decision;
                $d has decision-id $did;
            select $did;
        """
        decisions_results = self._execute_query(decisions_query)
        if decisions_results:
            session.linked_decisions = [r.get("did") for r in decisions_results]
        evidence_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (evidence-session: $s, session-evidence: $e) isa has-evidence;
                $e has evidence-source $src;
            select $src;
        """
        evidence_results = self._execute_query(evidence_query)
        if evidence_results:
            session.evidence_files = [r.get("src") for r in evidence_results]
        tasks_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
            select $t;
        """
        tasks_results = self._execute_query(tasks_query)
        session.tasks_completed = len(tasks_results)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID with all attributes."""
        results = self._execute_query(f'match $s isa work-session, has session-id "{session_id}"; select $s;')
        return self._build_session_from_id(session_id) if results else None

    def get_tasks_for_session(self, session_id: str) -> list[dict]:
        """Get all tasks linked to a session via completed-in relation."""
        query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
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
