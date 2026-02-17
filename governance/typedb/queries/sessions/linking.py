"""
TypeDB Session Linking Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/sessions.py

Created: 2026-01-04
"""

import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


class SessionLinkingOperations:
    """
    Session linking operations for TypeDB.

    Handles session-to-rule, session-to-decision, and session-to-evidence relationships.

    Requires a client with _execute_query and _driver attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

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
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # First, ensure the evidence-file entity exists
                evidence_id = evidence_source.replace("/", "-").replace(".", "-")
                now = datetime.now()
                timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')

                # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
                evidence_source_escaped = evidence_source.replace('\\', '\\\\').replace('"', '\\"')
                evidence_id_escaped = evidence_id.replace('\\', '\\\\').replace('"', '\\"')

                # Insert evidence if not exists (TypeDB allows duplicates to be ignored)
                insert_evidence = f"""
                    insert $e isa evidence-file,
                        has evidence-id "{evidence_id_escaped}",
                        has evidence-source "{evidence_source_escaped}",
                        has evidence-type "markdown",
                        has evidence-created-at {timestamp_str};
                """
                try:
                    tx.query(insert_evidence).resolve()
                except Exception:
                    pass  # Might already exist

                # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
                session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')

                # Create the has-evidence relation
                link_query = f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $e isa evidence-file, has evidence-source "{evidence_source_escaped}";
                    insert
                        (evidence-session: $s, session-evidence: $e) isa has-evidence;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link evidence {evidence_source} to session {session_id}: {e}")
            return False

    def get_session_evidence(self, session_id: str) -> List[str]:
        """
        Get all evidence files linked to a session.

        Args:
            session_id: Session ID

        Returns:
            List of evidence file paths
        """
        # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $s isa work-session, has session-id "{session_id_escaped}";
                (evidence-session: $s, session-evidence: $e) isa has-evidence;
                $e has evidence-source $src;
            select $src;
        """
        results = self._execute_query(query)
        return [r.get("src") for r in results if r.get("src")]

    def link_rule_to_session(self, session_id: str, rule_id: str) -> bool:
        """
        Link a rule to a session via session-applied-rule relation.

        Per P11.3: Entity Linkage - sessions track which rules were applied.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-28-001")
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
                session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
                rule_id_escaped = rule_id.replace('\\', '\\\\').replace('"', '\\"')
                # Create the session-applied-rule relation
                link_query = f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $r isa rule-entity, has rule-id "{rule_id_escaped}";
                    insert
                        (applying-session: $s, applied-rule: $r) isa session-applied-rule;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link rule {rule_id} to session {session_id}: {e}")
            return False

    def link_decision_to_session(self, session_id: str, decision_id: str) -> bool:
        """
        Link a decision to a session via session-decision relation.

        Per P11.3: Entity Linkage - sessions track which decisions were made.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-28-001")
            decision_id: Decision ID (e.g., "DECISION-001")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
                session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
                decision_id_escaped = decision_id.replace('\\', '\\\\').replace('"', '\\"')
                # Create the session-decision relation
                link_query = f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $d isa decision, has decision-id "{decision_id_escaped}";
                    insert
                        (deciding-session: $s, session-made-decision: $d) isa session-decision;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link decision {decision_id} to session {session_id}: {e}")
            return False

    def get_session_rules(self, session_id: str) -> List[str]:
        """
        Get all rules applied during a session.

        Args:
            session_id: Session ID

        Returns:
            List of rule IDs
        """
        # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $s isa work-session, has session-id "{session_id_escaped}";
                (applying-session: $s, applied-rule: $r) isa session-applied-rule;
                $r has rule-id $rid;
            select $rid;
        """
        results = self._execute_query(query)
        return [r.get("rid") for r in results if r.get("rid")]

    def get_session_decisions(self, session_id: str) -> List[str]:
        """
        Get all decisions made during a session.

        Args:
            session_id: Session ID

        Returns:
            List of decision IDs
        """
        # BUG-310-LINK-001: Backslash-first escape order (was quote-only)
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $s isa work-session, has session-id "{session_id_escaped}";
                (deciding-session: $s, session-made-decision: $d) isa session-decision;
                $d has decision-id $did;
            select $did;
        """
        results = self._execute_query(query)
        return [r.get("did") for r in results if r.get("did")]
