"""TypeDB queries for task comments — EPIC-ISSUE-EVIDENCE P19.

Provides insert, list, and delete operations for task-comment entities
linked to tasks via task-has-comment relation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskCommentQueries:
    """TypeDB query mixin for task comments."""

    def insert_comment(
        self,
        task_id: str,
        comment_id: str,
        body: str,
        author: str,
        created_at: str,
    ) -> bool:
        """Insert a comment and link to task via task-has-comment relation."""
        from typedb.driver import TransactionType

        body_escaped = body.replace('\\', '\\\\').replace('"', '\\"')
        author_escaped = author.replace('\\', '\\\\').replace('"', '\\"')

        try:
            # Parse ISO datetime for TypeDB datetime attribute
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = (
                    f'match $t isa task, has task-id "{task_id}"; '
                    f'insert $c isa task-comment, '
                    f'has comment-id "{comment_id}", '
                    f'has comment-body "{body_escaped}", '
                    f'has comment-author "{author_escaped}", '
                    f'has comment-created-at {dt_str}; '
                    f'(commented-task: $t, posted-comment: $c) isa task-has-comment;'
                )
                tx.query(query)
                tx.commit()
                logger.info("Inserted comment %s on task %s", comment_id, task_id)
                return True
        except Exception as e:
            logger.warning(
                "Failed to insert comment %s: %s", comment_id, type(e).__name__,
                exc_info=True,
            )
            return False

    def get_comments_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a task, ordered by created_at asc."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                query = (
                    f'match $t isa task, has task-id "{task_id}"; '
                    f'(commented-task: $t, posted-comment: $c) isa task-has-comment; '
                    f'$c has comment-id $cid, has comment-body $body, '
                    f'has comment-author $author, has comment-created-at $cat; '
                    f'select $cid, $body, $author, $cat;'
                )
                results = self._execute_query(query, tx=tx)
                comments = []
                for r in results:
                    comments.append({
                        "comment_id": r.get("cid"),
                        "task_id": task_id,
                        "body": r.get("body"),
                        "author": r.get("author"),
                        "created_at": str(r.get("cat", "")),
                    })
                # Sort by created_at ascending
                comments.sort(key=lambda c: c.get("created_at") or "")
                return comments
        except Exception as e:
            logger.debug("Failed to get comments for %s: %s", task_id, e)
            return []

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment by ID."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = (
                    f'match $c isa task-comment, has comment-id "{comment_id}"; '
                    f'delete $c;'
                )
                tx.query(query)
                tx.commit()
                logger.info("Deleted comment %s from TypeDB", comment_id)
                return True
        except Exception as e:
            logger.debug("Failed to delete comment %s: %s", comment_id, e)
            return False
