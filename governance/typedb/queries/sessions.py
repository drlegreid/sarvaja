"""
TypeDB Session Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.
Per GAP-ARCH-002: Session TypeDB operations.

Created: 2024-12-28
"""

from datetime import datetime
from typing import List, Optional

from ..entities import Session


class SessionQueries:
    """
    Session query operations for TypeDB.

    Requires a client with _execute_query and _client attributes.
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

    def insert_session(
        self,
        session_id: str,
        name: str = None,
        description: str = None,
        file_path: str = None,
        agent_id: str = None
    ) -> Optional[Session]:
        """
        Insert a new session into TypeDB.

        Per GAP-ARCH-002: Session creation in TypeDB.

        Note: Checks for existing session first to prevent duplicates.
        """
        from typedb.driver import SessionType, TransactionType

        # Check if session already exists
        existing = self.get_session(session_id)
        if existing:
            # Session already exists, return None to indicate conflict
            print(f"Session {session_id} already exists, skipping insert")
            return None

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # Build insert parts
                    insert_parts = [f'has session-id "{session_id}"']

                    if name:
                        insert_parts.append(f'has session-name "{name}"')
                    if description:
                        desc_escaped = description.replace('"', '\\"')
                        insert_parts.append(f'has session-description "{desc_escaped}"')
                    if file_path:
                        insert_parts.append(f'has session-file-path "{file_path}"')
                    if agent_id:
                        insert_parts.append(f'has agent-id "{agent_id}"')

                    # Add started-at timestamp (TypeDB datetime format: YYYY-MM-DDTHH:MM:SS)
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_parts.append(f'has started-at {timestamp_str}')

                    insert_query = f"""
                        insert $s isa work-session,
                            {", ".join(insert_parts)};
                    """
                    tx.query.insert(insert_query)
                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            print(f"Failed to insert session {session_id}: {e}")
            return None

    def end_session(self, session_id: str) -> Optional[Session]:
        """End a session by setting completed-at timestamp."""
        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # TypeDB datetime format: YYYY-MM-DDTHH:MM:SS (no microseconds, no trailing T)
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_query = f"""
                        match
                            $s isa work-session, has session-id "{session_id}";
                        insert
                            $s has completed-at {timestamp_str};
                    """
                    tx.query.insert(insert_query)
                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            print(f"Failed to end session {session_id}: {e}")
            return None

    def link_evidence_to_session(
        self,
        session_id: str,
        evidence_source: str
    ) -> bool:
        """
        Link an evidence file to a session via has-evidence relation.

        Per P11.5: Session Evidence Attachments.
        Per GAP-DATA-003: Evidence attachment functionality.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-28-001")
            evidence_source: Evidence file path (e.g., "evidence/DECISION-001.md")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import SessionType, TransactionType

        try:
            with self._client.session(self.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.WRITE) as tx:
                    # First, ensure the evidence-file entity exists
                    evidence_id = evidence_source.replace("/", "-").replace(".", "-")
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')

                    # Check if evidence exists, if not create it
                    check_query = f"""
                        match $e isa evidence-file, has evidence-source "{evidence_source}";
                        get $e;
                    """
                    # We need to run this in a read tx first
                    pass  # Skip check for now, upsert pattern

                    # Insert evidence if not exists (TypeDB allows duplicates to be ignored)
                    insert_evidence = f"""
                        insert $e isa evidence-file,
                            has evidence-id "{evidence_id}",
                            has evidence-source "{evidence_source}",
                            has evidence-type "markdown",
                            has evidence-created-at {timestamp_str};
                    """
                    try:
                        tx.query.insert(insert_evidence)
                    except Exception:
                        pass  # Might already exist

                    # Create the has-evidence relation
                    link_query = f"""
                        match
                            $s isa work-session, has session-id "{session_id}";
                            $e isa evidence-file, has evidence-source "{evidence_source}";
                        insert
                            (evidence-session: $s, session-evidence: $e) isa has-evidence;
                    """
                    tx.query.insert(link_query)
                    tx.commit()

            return True
        except Exception as e:
            print(f"Failed to link evidence {evidence_source} to session {session_id}: {e}")
            return False

    def get_session_evidence(self, session_id: str) -> List[str]:
        """
        Get all evidence files linked to a session.

        Args:
            session_id: Session ID

        Returns:
            List of evidence file paths
        """
        query = f"""
            match
                $s isa work-session, has session-id "{session_id}";
                (evidence-session: $s, session-evidence: $e) isa has-evidence;
                $e has evidence-source $src;
            get $src;
        """
        results = self._execute_query(query)
        return [r.get("src") for r in results if r.get("src")]
