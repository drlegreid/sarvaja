"""
TypeDB Task Linking Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/tasks.py

Created: 2026-01-04
"""

import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


class TaskLinkingOperations:
    """
    Task linking operations for TypeDB.

    Handles task-to-rule, task-to-session, and task-to-evidence relationships.

    Requires a client with _execute_query, _driver, and database attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def link_evidence_to_task(self, task_id: str, evidence_source: str) -> bool:
        """
        Link an evidence file to a task via evidence-supports relation.

        Per P11.3: Entity Linkage - evidence supports task completion.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            evidence_source: Evidence file path (e.g., "evidence/SESSION-2024-12-28.md")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # First ensure evidence-file entity exists
                evidence_id = evidence_source.replace("/", "-").replace(".", "-").replace("\\", "-")
                now = datetime.now()
                timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')

                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                evidence_id_escaped = evidence_id.replace('\\', '\\\\').replace('"', '\\"')
                evidence_source_escaped = evidence_source.replace('\\', '\\\\').replace('"', '\\"')
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')

                # Insert evidence if not exists
                insert_evidence = f"""
                    insert $e isa evidence-file,
                        has evidence-id "{evidence_id_escaped}",
                        has evidence-source "{evidence_source_escaped}",
                        has evidence-type "markdown",
                        has evidence-created-at {timestamp_str};
                """
                try:
                    tx.query(insert_evidence).resolve()
                # BUG-364-LINK-001: Log instead of silently swallowing
                except Exception as e:
                    logger.debug(f"Evidence entity insert for {evidence_id} (expected if exists): {e}")

                # Create the evidence-supports relation
                link_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $e isa evidence-file, has evidence-source "{evidence_source_escaped}";
                    insert
                        (supporting-evidence: $e, supported-task: $t) isa evidence-supports;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link evidence {evidence_source} to task {task_id}: {e}")
            return False

    def link_task_to_session(self, task_id: str, session_id: str) -> bool:
        """
        Link a task to a session via completed-in relation.

        Per P11.3: Entity Linkage - tasks completed in sessions.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            session_id: Session ID (e.g., "SESSION-2024-12-28-001")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
                # Create the completed-in relation
                link_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $s isa work-session, has session-id "{session_id_escaped}";
                    insert
                        (completed-task: $t, hosting-session: $s) isa completed-in;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link task {task_id} to session {session_id}: {e}")
            return False

    def link_task_to_rule(self, task_id: str, rule_id: str) -> bool:
        """
        Link a task to a rule via implements-rule relation.

        Per P11.3: Entity Linkage - tasks implement rules.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                rule_id_escaped = rule_id.replace('\\', '\\\\').replace('"', '\\"')
                # Create the implements-rule relation
                link_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $r isa rule-entity, has rule-id "{rule_id_escaped}";
                    insert
                        (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link task {task_id} to rule {rule_id}: {e}")
            return False

    def get_task_evidence(self, task_id: str) -> List[str]:
        """
        Get all evidence files linked to a task.

        Args:
            task_id: Task ID

        Returns:
            List of evidence file paths
        """
        # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
        task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $t isa task, has task-id "{task_id_escaped}";
                (supporting-evidence: $e, supported-task: $t) isa evidence-supports;
                $e has evidence-source $src;
            select $src;
        """
        results = self._execute_query(query)
        return [r.get("src") for r in results if r.get("src")]

    def link_task_to_commit(self, task_id: str, commit_sha: str, commit_message: str = None) -> bool:
        """
        Link a task to a git commit via task-commit relation.

        Per GAP-TASK-LINK-002: Task-to-commit traceability.

        Args:
            task_id: Task ID (e.g., "P10.1")
            commit_sha: Git commit SHA (short or full)
            commit_message: Optional commit message

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Insert git-commit entity
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                commit_sha_escaped = commit_sha.replace('\\', '\\\\').replace('"', '\\"')
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                msg_escaped = commit_message.replace('\\', '\\\\').replace('"', '\\"') if commit_message else ""
                commit_parts = [f'has commit-sha "{commit_sha_escaped}"']
                if commit_message:
                    commit_parts.append(f'has commit-message "{msg_escaped}"')

                insert_commit = f"""
                    insert $c isa git-commit,
                        {", ".join(commit_parts)};
                """
                try:
                    tx.query(insert_commit).resolve()
                # BUG-364-LINK-001: Log instead of silently swallowing
                except Exception as e:
                    logger.debug(f"Git commit entity insert for {commit_sha} (expected if exists): {e}")

                # Create the task-commit relation
                link_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $c isa git-commit, has commit-sha "{commit_sha_escaped}";
                    insert
                        (implementing-commit: $c, implemented-task: $t) isa task-commit;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link task {task_id} to commit {commit_sha}: {e}")
            return False

    def get_task_commits(self, task_id: str) -> List[str]:
        """
        Get all commit SHAs linked to a task.

        Per GAP-TASK-LINK-002: Task-to-commit traceability.

        Args:
            task_id: Task ID

        Returns:
            List of commit SHAs
        """
        # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
        task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $t isa task, has task-id "{task_id_escaped}";
                (implementing-commit: $c, implemented-task: $t) isa task-commit;
                $c has commit-sha $sha;
            select $sha;
        """
        results = self._execute_query(query)
        return [r.get("sha") for r in results if r.get("sha")]

    def link_task_to_document(self, task_id: str, document_path: str) -> bool:
        """Link a task to a document via document-references-task relation.

        Args:
            task_id: Task ID
            document_path: Document path (e.g., "docs/rules/leaf/TEST-E2E-01-v1.md")

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Ensure document entity exists
                doc_id = document_path.replace("/", "-").replace(".", "-").replace("\\", "-").upper()
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                doc_id_escaped = doc_id.replace('\\', '\\\\').replace('"', '\\"')
                document_path_escaped = document_path.replace('\\', '\\\\').replace('"', '\\"')
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                insert_doc = f"""
                    insert $d isa document,
                        has document-id "{doc_id_escaped}",
                        has document-path "{document_path_escaped}",
                        has document-type "markdown",
                        has document-storage "filesystem";
                """
                try:
                    tx.query(insert_doc).resolve()
                # BUG-364-LINK-001: Log instead of silently swallowing
                except Exception as e:
                    logger.debug(f"Document entity insert for {doc_id} (expected if exists): {e}")

                # Create document-references-task relation
                link_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $d isa document, has document-path "{document_path_escaped}";
                    insert
                        (referencing-document: $d, referenced-task: $t) isa document-references-task;
                """
                tx.query(link_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to link task {task_id} to document {document_path}: {e}")
            return False

    def unlink_task_from_document(self, task_id: str, document_path: str) -> bool:
        """Unlink a document from a task.

        Args:
            task_id: Task ID
            document_path: Document path to unlink

        Returns:
            True if unlinked successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                document_path_escaped = document_path.replace('\\', '\\\\').replace('"', '\\"')
                delete_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $d isa document, has document-path "{document_path_escaped}";
                        $rel (referencing-document: $d, referenced-task: $t) isa document-references-task;
                    delete $rel;
                """
                tx.query(delete_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to unlink document {document_path} from task {task_id}: {e}")
            return False

    def get_task_documents(self, task_id: str) -> List[str]:
        """Get all document paths linked to a task.

        Args:
            task_id: Task ID

        Returns:
            List of document paths
        """
        # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
        task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $t isa task, has task-id "{task_id_escaped}";
                (referencing-document: $d, referenced-task: $t) isa document-references-task;
                $d has document-path $dpath;
            select $dpath;
        """
        results = self._execute_query(query)
        return [r.get("dpath") for r in results if r.get("dpath")]

    # Task relationship operations moved to relationships.py per DOC-SIZE-01-v1
