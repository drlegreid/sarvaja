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


def _relation_exists(tx, match_query: str) -> bool:
    """Check whether a TypeDB relation already exists within a transaction.

    Shared idempotency helper — DRY extraction per SRVJ-BUG-IDEMP-LINK-01.
    Used by all link_task_to_* methods to skip duplicate inserts.

    Args:
        tx: An open TypeDB transaction.
        match_query: A TypeQL match query that selects the relation.

    Returns:
        True if the relation exists, False otherwise.
    """
    result = tx.query(match_query).resolve()
    return bool(list(result or []))


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
                    # BUG-477-TLK-1: Sanitize debug/info logger
                    logger.debug(f"Evidence entity insert for {evidence_id} (expected if exists): {type(e).__name__}")

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
            # BUG-397-LNK-001: Add exc_info for stack trace preservation
            # BUG-472-TLK-001: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to link evidence {evidence_source} to task {task_id}: {type(e).__name__}", exc_info=True)
            return False

    def session_exists(self, session_id: str) -> bool:
        """Check if a session entity exists in TypeDB.

        Per EPIC-GOV-TASKS-V2 Phase 2: Pre-check before linking.

        Args:
            session_id: Session ID to check

        Returns:
            True if session exists, False otherwise
        """
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $s isa work-session, has session-id "{session_id_escaped}";
            select $s;
        """
        results = self._execute_query(query)
        if not results:
            logger.warning(
                f"[LINK-PRECHECK] Session {session_id} not found in TypeDB — "
                "link will be attempted but may fail"
            )
        return bool(results)

    def link_task_to_session(self, task_id: str, session_id: str) -> bool:
        """
        Link a task to a session via completed-in relation.

        Per P11.3: Entity Linkage - tasks completed in sessions.
        Per GAP-DATA-002: Entity linkage implementation.
        Per EPIC-GOV-TASKS-V2 Phase 2: Session existence pre-check.
        Per SRVJ-BUG-007: Auto-creates session entity if missing in TypeDB.
        Per BUG-SESSION-POISON-01: Validates session_id before auto-creating.

        Args:
            task_id: Task ID (e.g., "P10.1")
            session_id: Session ID (e.g., "SESSION-2024-12-28-001")

        Returns:
            True if link created successfully, False otherwise
        """
        # BUG-SESSION-POISON-01: Reject invalid session IDs before they get
        # auto-created as TypeDB entities (prevents path traversal poisoning)
        import re as _re
        if not session_id or not _re.match(r'^[A-Za-z0-9_\-\.\(\)]{1,200}$', session_id):
            logger.warning(
                f"[LINK-REJECT] Invalid session_id rejected: "
                f"{session_id[:50] if session_id else 'None'}..."
            )
            return False

        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # BUG-254-ESC-002: Escape backslash THEN quotes for TypeQL safety
                task_id_escaped = task_id.replace('\\', '\\\\').replace('"', '\\"')
                session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')

                # SRVJ-BUG-007: Ensure session entity exists before relation insert.
                # Sessions may be memory-only (not persisted to TypeDB).
                check_q = f'match $s isa work-session, has session-id "{session_id_escaped}"; select $s;'
                check_result = tx.query(check_q).resolve()
                if not list(check_result or []):
                    ensure_q = f'insert $s isa work-session, has session-id "{session_id_escaped}";'
                    tx.query(ensure_q).resolve()

                # SRVJ-BUG-010: Idempotency guard — skip if relation already exists
                check_rel_q = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $s isa work-session, has session-id "{session_id_escaped}";
                        (completed-task: $t, hosting-session: $s) isa completed-in;
                """
                if _relation_exists(tx, check_rel_q):
                    tx.commit()
                    return True

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
            # BUG-397-LNK-002: Add exc_info for stack trace preservation
            # BUG-472-TLK-002: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to link task {task_id} to session {session_id}: {type(e).__name__}", exc_info=True)
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

                # SRVJ-BUG-020: Idempotency guard — skip if relation already exists
                check_rel_q = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $r isa rule-entity, has rule-id "{rule_id_escaped}";
                        (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                """
                if _relation_exists(tx, check_rel_q):
                    logger.debug(f"Rule-task link already exists: {task_id} -> {rule_id}")
                    tx.commit()
                    return True

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
            # BUG-397-LNK-003: Add exc_info for stack trace preservation
            # BUG-472-TLK-003: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to link task {task_id} to rule {rule_id}: {type(e).__name__}", exc_info=True)
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
                    # BUG-477-TLK-2: Sanitize debug/info logger
                    logger.debug(f"Git commit entity insert for {commit_sha} (expected if exists): {type(e).__name__}")

                # SRVJ-BUG-IDEMP-LINK-01: Idempotency guard — skip if relation exists
                check_rel_q = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $c isa git-commit, has commit-sha "{commit_sha_escaped}";
                        (implementing-commit: $c, implemented-task: $t) isa task-commit;
                """
                if _relation_exists(tx, check_rel_q):
                    logger.debug(f"Commit-task link already exists: {task_id} -> {commit_sha}")
                    tx.commit()
                    return True

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
            # BUG-397-LNK-004: Add exc_info for stack trace preservation
            # BUG-472-TLK-004: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to link task {task_id} to commit {commit_sha}: {type(e).__name__}", exc_info=True)
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
                    # BUG-477-TLK-3: Sanitize debug/info logger
                    logger.debug(f"Document entity insert for {doc_id} (expected if exists): {type(e).__name__}")

                # FIX-DATA-005: Idempotency guard — check if relation exists before insert
                check_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $d isa document, has document-path "{document_path_escaped}";
                        (referencing-document: $d, referenced-task: $t) isa document-references-task;
                """
                if _relation_exists(tx, check_query):
                    logger.debug(f"Document-task link already exists: {task_id} -> {document_path}")
                    tx.commit()
                    return True

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
            # BUG-397-LNK-005: Add exc_info for stack trace preservation
            # BUG-472-TLK-005: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to link task {task_id} to document {document_path}: {type(e).__name__}", exc_info=True)
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
                # TypeDB 3.x: use `links` syntax — the old `$rel (role: $x) isa type`
                # causes Thing/ThingType conflict on delete (REP1 error).
                delete_query = f"""
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $d isa document, has document-path "{document_path_escaped}";
                        $rel isa document-references-task,
                            links (referencing-document: $d, referenced-task: $t);
                    delete $rel;
                """
                tx.query(delete_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            # BUG-397-LNK-006: Add exc_info for stack trace preservation
            # BUG-472-TLK-006: Sanitize logger message — exc_info=True already captures full stack
            logger.error(f"Failed to unlink document {document_path} from task {task_id}: {type(e).__name__}", exc_info=True)
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
