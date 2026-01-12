"""
TypeDB Session Read Queries.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/sessions.py

Created: 2026-01-04
"""

from typing import List, Optional

from ...entities import Session


class SessionReadQueries:
    """
    Session read query operations for TypeDB.

    Requires a client with _execute_query attribute.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_all_sessions(self) -> List[Session]:
        """Get all work sessions from TypeDB."""
        query = """
            match $s isa work-session,
                has session-id $id;
            get $id;
        """
        results = self._execute_query(query)
        return [self._build_session_from_id(r.get("id")) for r in results if r.get("id")]

    def _build_session_from_id(self, session_id: str) -> Optional[Session]:
        """Build a full Session object from TypeDB by ID."""
        # Get basic attributes (session-id is required, others optional)
        session = Session(id=session_id)

        # Get session-name
        name_query = f"""
            match $s isa work-session, has session-id "{session_id}", has session-name $name;
            get $name;
        """
        name_results = self._execute_query(name_query)
        if name_results:
            session.name = name_results[0].get("name")

        # Get description
        desc_query = f"""
            match $s isa work-session, has session-id "{session_id}", has session-description $desc;
            get $desc;
        """
        desc_results = self._execute_query(desc_query)
        if desc_results:
            session.description = desc_results[0].get("desc")

        # Get file path
        path_query = f"""
            match $s isa work-session, has session-id "{session_id}", has session-file-path $path;
            get $path;
        """
        path_results = self._execute_query(path_query)
        if path_results:
            session.file_path = path_results[0].get("path")

        # Get started-at
        start_query = f"""
            match $s isa work-session, has session-id "{session_id}", has started-at $start;
            get $start;
        """
        start_results = self._execute_query(start_query)
        if start_results:
            session.started_at = start_results[0].get("start")

        # Get completed-at
        end_query = f"""
            match $s isa work-session, has session-id "{session_id}", has completed-at $end;
            get $end;
        """
        end_results = self._execute_query(end_query)
        if end_results:
            session.completed_at = end_results[0].get("end")
            session.status = "COMPLETED"
        else:
            session.status = "ACTIVE"

        # Get agent-id (E2E tests requirement)
        agent_query = f"""
            match $s isa work-session, has session-id "{session_id}", has agent-id $agent;
            get $agent;
        """
        agent_results = self._execute_query(agent_query)
        if agent_results:
            session.agent_id = agent_results[0].get("agent")

        # Get linked rules via session-applied-rule relationship
        rules_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (applying-session: $s, applied-rule: $r) isa session-applied-rule;
                $r has rule-id $rid;
            get $rid;
        """
        rules_results = self._execute_query(rules_query)
        if rules_results:
            session.linked_rules_applied = [r.get("rid") for r in rules_results]

        # Get linked decisions via session-decision relationship
        decisions_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (deciding-session: $s, session-made-decision: $d) isa session-decision;
                $d has decision-id $did;
            get $did;
        """
        decisions_results = self._execute_query(decisions_query)
        if decisions_results:
            session.linked_decisions = [r.get("did") for r in decisions_results]

        # Get evidence files via has-evidence relationship
        evidence_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (evidence-session: $s, session-evidence: $e) isa has-evidence;
                $e has evidence-source $src;
            get $src;
        """
        evidence_results = self._execute_query(evidence_query)
        if evidence_results:
            session.evidence_files = [r.get("src") for r in evidence_results]

        # Count completed tasks
        tasks_query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (completed-task: $t, hosting-session: $s) isa completed-in;
            get $t;
        """
        tasks_results = self._execute_query(tasks_query)
        session.tasks_completed = len(tasks_results)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID with all attributes.

        Returns:
            Session object if found, None if session doesn't exist.
        """
        # First verify the session actually exists in TypeDB
        check_query = f"""
            match $s isa work-session, has session-id "{session_id}";
            get $s;
        """
        results = self._execute_query(check_query)
        if not results:
            return None  # Session doesn't exist

        return self._build_session_from_id(session_id)
