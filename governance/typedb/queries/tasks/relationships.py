"""
TypeDB Task Relationship Operations.

Per DOC-SIZE-01-v1: Files under 300 lines.
Per GAP-TASK-LINK-003: Task relationship management.

Created: 2026-01-14
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class TaskRelationshipOperations:
    """
    Task relationship operations for TypeDB.

    Handles task-to-task relationships: parent/child, blocking, related.

    Requires a client with _execute_query and _driver attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def link_parent_task(self, child_task_id: str, parent_task_id: str) -> bool:
        """
        Link a child task to its parent task.

        Per GAP-TASK-LINK-003: Task hierarchy relationships.

        Args:
            child_task_id: Child task ID
            parent_task_id: Parent task ID

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                link_query = f"""
                    match
                        $child isa task, has task-id "{child_task_id}";
                        $parent isa task, has task-id "{parent_task_id}";
                    insert
                        (parent-task: $parent, child-task: $child) isa task-hierarchy;
                """
                tx.query(link_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link parent {parent_task_id} to child {child_task_id}: {e}")
            return False

    def link_blocking_task(self, blocking_task_id: str, blocked_task_id: str) -> bool:
        """
        Link a blocking task to the task it blocks.

        Per GAP-TASK-LINK-003: Task blocking relationships.

        Args:
            blocking_task_id: The task that blocks
            blocked_task_id: The task being blocked

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                link_query = f"""
                    match
                        $blocker isa task, has task-id "{blocking_task_id}";
                        $blocked isa task, has task-id "{blocked_task_id}";
                    insert
                        (blocking-task: $blocker, blocked-dep-task: $blocked) isa task-blocks-task;
                """
                tx.query(link_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link blocking task {blocking_task_id}: {e}")
            return False

    def link_related_tasks(self, task_id_a: str, task_id_b: str) -> bool:
        """
        Link two related tasks (soft association).

        Per GAP-TASK-LINK-003: Task related relationships.

        Args:
            task_id_a: First task ID
            task_id_b: Second task ID

        Returns:
            True if link created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                link_query = f"""
                    match
                        $a isa task, has task-id "{task_id_a}";
                        $b isa task, has task-id "{task_id_b}";
                    insert
                        (related-task-a: $a, related-task-b: $b) isa task-related;
                """
                tx.query(link_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link related tasks {task_id_a} and {task_id_b}: {e}")
            return False

    def get_task_children(self, task_id: str) -> List[str]:
        """Get child tasks of a parent task."""
        query = f"""
            match
                $parent isa task, has task-id "{task_id}";
                (parent-task: $parent, child-task: $child) isa task-hierarchy;
                $child has task-id $cid;
            select $cid;
        """
        results = self._execute_query(query)
        return [r.get("cid") for r in results if r.get("cid")]

    def get_task_parent(self, task_id: str) -> Optional[str]:
        """Get parent task of a child task."""
        query = f"""
            match
                $child isa task, has task-id "{task_id}";
                (parent-task: $parent, child-task: $child) isa task-hierarchy;
                $parent has task-id $pid;
            select $pid;
        """
        results = self._execute_query(query)
        return results[0].get("pid") if results else None

    def get_tasks_blocking(self, task_id: str) -> List[str]:
        """Get tasks that block this task."""
        query = f"""
            match
                $blocked isa task, has task-id "{task_id}";
                (blocking-task: $blocker, blocked-dep-task: $blocked) isa task-blocks-task;
                $blocker has task-id $bid;
            select $bid;
        """
        results = self._execute_query(query)
        return [r.get("bid") for r in results if r.get("bid")]

    def get_tasks_blocked_by(self, task_id: str) -> List[str]:
        """Get tasks that this task blocks."""
        query = f"""
            match
                $blocker isa task, has task-id "{task_id}";
                (blocking-task: $blocker, blocked-dep-task: $blocked) isa task-blocks-task;
                $blocked has task-id $bid;
            select $bid;
        """
        results = self._execute_query(query)
        return [r.get("bid") for r in results if r.get("bid")]

    def get_related_tasks(self, task_id: str) -> List[str]:
        """Get tasks related to this task."""
        query = f"""
            match
                $t isa task, has task-id "{task_id}";
                {{
                    (related-task-a: $t, related-task-b: $other) isa task-related;
                }} or {{
                    (related-task-a: $other, related-task-b: $t) isa task-related;
                }};
                $other has task-id $oid;
            select $oid;
        """
        results = self._execute_query(query)
        return [r.get("oid") for r in results if r.get("oid")]
