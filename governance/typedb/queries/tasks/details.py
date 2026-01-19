"""
TypeDB Task Detail Section Operations.

Per DOC-SIZE-01-v1: Files under 300 lines.
Per GAP-TASK-LINK-004: Task detail sections.
Per TASK-TECH-01-v1: Technology Solution Documentation.

Created: 2026-01-14
"""

from typing import Optional


class TaskDetailOperations:
    """
    Task detail section operations for TypeDB.

    Handles task detail sections: business, design, architecture, test.

    Requires a client with _execute_query, _driver, database, get_task attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def update_task_business(self, task_id: str, content: str) -> bool:
        """
        Update task business section (Why - User problem, business value).

        Per GAP-TASK-LINK-004: Task detail sections.

        Args:
            task_id: Task ID to update
            content: Business section content (markdown supported)

        Returns:
            True if update succeeded, False otherwise
        """
        return self._update_task_detail(task_id, "task-business", content)

    def update_task_design(self, task_id: str, content: str) -> bool:
        """
        Update task design section (What - Functional requirements).

        Per GAP-TASK-LINK-004: Task detail sections.

        Args:
            task_id: Task ID to update
            content: Design section content (markdown supported)

        Returns:
            True if update succeeded, False otherwise
        """
        return self._update_task_detail(task_id, "task-design", content)

    def update_task_architecture(self, task_id: str, content: str) -> bool:
        """
        Update task architecture section (How - Technical approach).

        Per GAP-TASK-LINK-004: Task detail sections.

        Args:
            task_id: Task ID to update
            content: Architecture section content (markdown supported)

        Returns:
            True if update succeeded, False otherwise
        """
        return self._update_task_detail(task_id, "task-architecture", content)

    def update_task_test(self, task_id: str, content: str) -> bool:
        """
        Update task test section (Verification - Test plan, evidence).

        Per GAP-TASK-LINK-004: Task detail sections.

        Args:
            task_id: Task ID to update
            content: Test section content (markdown supported)

        Returns:
            True if update succeeded, False otherwise
        """
        return self._update_task_detail(task_id, "task-test", content)

    def update_task_details(
        self,
        task_id: str,
        business: Optional[str] = None,
        design: Optional[str] = None,
        architecture: Optional[str] = None,
        test_section: Optional[str] = None
    ) -> bool:
        """
        Update multiple task detail sections at once.

        Per GAP-TASK-LINK-004: Task detail sections.
        Per TASK-TECH-01-v1: Technology Solution Documentation.

        Args:
            task_id: Task ID to update
            business: Business section content (Why)
            design: Design section content (What)
            architecture: Architecture section content (How)
            test_section: Test section content (Verification)

        Returns:
            True if all updates succeeded, False if any failed
        """
        success = True
        if business is not None:
            success = self._update_task_detail(task_id, "task-business", business) and success
        if design is not None:
            success = self._update_task_detail(task_id, "task-design", design) and success
        if architecture is not None:
            success = self._update_task_detail(task_id, "task-architecture", architecture) and success
        if test_section is not None:
            success = self._update_task_detail(task_id, "task-test", test_section) and success
        return success

    def _update_task_detail(self, task_id: str, attribute: str, content: str) -> bool:
        """
        Internal method to update a task detail attribute.

        Uses delete-then-insert pattern for TypeDB attribute updates.

        Args:
            task_id: Task ID
            attribute: Attribute name (task-business, task-design, etc.)
            content: New content value

        Returns:
            True if update succeeded, False otherwise
        """
        from typedb.driver import TransactionType

        # Verify task exists
        task = self.get_task(task_id)
        if not task:
            print(f"Task {task_id} not found")
            return False

        # Escape content for TypeQL
        content_escaped = content.replace('\\', '\\\\').replace('"', '\\"')

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete existing attribute if present (TypeDB 3.x: has $var of $entity)
                delete_query = f"""
                    match
                        $t isa task, has task-id "{task_id}", has {attribute} $old;
                    delete
                        has $old of $t;
                """
                try:
                    tx.query(delete_query).resolve()
                except Exception:
                    pass  # Attribute may not exist

                # Insert new attribute
                insert_query = f"""
                    match
                        $t isa task, has task-id "{task_id}";
                    insert
                        $t has {attribute} "{content_escaped}";
                """
                tx.query(insert_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            print(f"Failed to update {attribute} for task {task_id}: {e}")
            return False

    def get_task_details(self, task_id: str) -> Optional[dict]:
        """
        Get all detail sections for a task.

        Args:
            task_id: Task ID

        Returns:
            Dict with business, design, architecture, test_section or None if task not found
        """
        task = self.get_task(task_id)
        if not task:
            return None
        return {
            "business": task.business,
            "design": task.design,
            "architecture": task.architecture,
            "test_section": task.test_section
        }
