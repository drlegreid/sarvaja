"""
TypeDB Story Linking Operations.

FIX-HIER-002: Story entity + epic-contains-story, story-contains-task relations.
Hierarchy: Project → Workspace → Epic → Story → Task → Bug

Created: 2026-03-22
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    """Escape backslash then quotes for TypeQL safety."""
    return value.replace('\\', '\\\\').replace('"', '\\"')


class StoryLinkingOperations:
    """
    Story linking operations for TypeDB.

    Handles epic→story and story→task relationships.
    Uses mixin pattern for TypeDBClient composition.
    """

    def link_story_to_epic(self, story_id: str, epic_id: str) -> bool:
        """
        Link a story to an epic via epic-contains-story relation.

        Args:
            story_id: Story ID (e.g., "SARVAJA-STORY-001")
            epic_id: Epic ID (e.g., "EPIC-TASK-QUALITY-V1")

        Returns:
            True if link created, False otherwise
        """
        from typedb.driver import TransactionType

        sid = _escape(story_id)
        eid = _escape(epic_id)

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = (
                    f'match $e isa epic, has epic-id "{eid}"; '
                    f'$s isa story, has story-id "{sid}"; '
                    f'insert (parent-epic: $e, child-story: $s) '
                    f'isa epic-contains-story;'
                )
                tx.query(query).resolve()
                tx.commit()
            logger.info("Linked story %s to epic %s", story_id, epic_id)
            return True
        except Exception as e:
            logger.error(
                "Failed to link story %s to epic %s: %s",
                story_id, epic_id, type(e).__name__,
                exc_info=True,
            )
            return False

    def link_task_to_story(self, task_id: str, story_id: str) -> bool:
        """
        Link a task to a story via story-contains-task relation.

        Args:
            task_id: Task ID (e.g., "SARVAJA-BUG-001")
            story_id: Story ID (e.g., "SARVAJA-STORY-001")

        Returns:
            True if link created, False otherwise
        """
        from typedb.driver import TransactionType

        tid = _escape(task_id)
        sid = _escape(story_id)

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = (
                    f'match $s isa story, has story-id "{sid}"; '
                    f'$t isa task, has task-id "{tid}"; '
                    f'insert (parent-story: $s, story-task: $t) '
                    f'isa story-contains-task;'
                )
                tx.query(query).resolve()
                tx.commit()
            logger.info("Linked task %s to story %s", task_id, story_id)
            return True
        except Exception as e:
            logger.error(
                "Failed to link task %s to story %s: %s",
                task_id, story_id, type(e).__name__,
                exc_info=True,
            )
            return False

    def get_stories_for_epic(self, epic_id: str) -> List[str]:
        """Get all story IDs linked to an epic."""
        eid = _escape(epic_id)
        results = self._execute_query(
            f'match $e isa epic, has epic-id "{eid}"; '
            f'(parent-epic: $e, child-story: $s) isa epic-contains-story; '
            f'$s has story-id $sid; select $sid;'
        )
        return [r.get("sid", "") for r in results]

    def get_tasks_for_story(self, story_id: str) -> List[str]:
        """Get all task IDs linked to a story."""
        sid = _escape(story_id)
        results = self._execute_query(
            f'match $s isa story, has story-id "{sid}"; '
            f'(parent-story: $s, story-task: $t) isa story-contains-task; '
            f'$t has task-id $tid; select $tid;'
        )
        return [r.get("tid", "") for r in results]

    def get_story_for_task(self, task_id: str) -> str:
        """Get the story ID a task belongs to, or empty string."""
        tid = _escape(task_id)
        results = self._execute_query(
            f'match $t isa task, has task-id "{tid}"; '
            f'(parent-story: $s, story-task: $t) isa story-contains-task; '
            f'$s has story-id $sid; select $sid;'
        )
        return results[0].get("sid", "") if results else ""
