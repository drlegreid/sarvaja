"""
TypeDB Project Linking Operations.

Per GOV-PROJECT-01-v1: Project hierarchy relations.
Created: 2026-02-11
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ProjectLinkingOperations:
    """Project hierarchy linking for TypeDB. Uses mixin pattern."""

    def link_project_to_plan(self, project_id: str, plan_id: str) -> bool:
        """Link a project to a plan via project-contains-plan relation."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{project_id}";
                        $pl isa plan, has plan-id "{plan_id}";
                    insert
                        (parent-project: $p, child-plan: $pl) isa project-contains-plan;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link project {project_id} to plan {plan_id}: {e}")
            return False

    def link_plan_to_epic(self, plan_id: str, epic_id: str) -> bool:
        """Link a plan to an epic via plan-contains-epic relation."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $pl isa plan, has plan-id "{plan_id}";
                        $e isa epic, has epic-id "{epic_id}";
                    insert
                        (parent-plan: $pl, child-epic: $e) isa plan-contains-epic;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link plan {plan_id} to epic {epic_id}: {e}")
            return False

    def link_epic_to_task(self, epic_id: str, task_id: str) -> bool:
        """Link an epic to a task via epic-contains-task relation."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $e isa epic, has epic-id "{epic_id}";
                        $t isa task, has task-id "{task_id}";
                    insert
                        (parent-epic: $e, epic-task: $t) isa epic-contains-task;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link epic {epic_id} to task {task_id}: {e}")
            return False

    def link_project_to_session(self, project_id: str, session_id: str) -> bool:
        """Link a project to a session via project-has-session relation."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{project_id}";
                        $s isa work-session, has session-id "{session_id}";
                    insert
                        (session-project: $p, project-session: $s) isa project-has-session;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to link project {project_id} to session {session_id}: {e}")
            return False

    def get_project_sessions(self, project_id: str) -> list:
        """Get all session IDs linked to a project."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{project_id}";
                        (session-project: $p, project-session: $s) isa project-has-session;
                        $s has session-id $sid;
                    fetch
                        $sid;
                """
                results = list(tx.query(query).resolve())
                return [r.get("sid", {}).get("value", "") for r in results]
        except Exception as e:
            logger.error(f"Failed to get sessions for project {project_id}: {e}")
            return []

    def get_project_plans(self, project_id: str) -> list:
        """Get all plan IDs linked to a project."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{project_id}";
                        (parent-project: $p, child-plan: $pl) isa project-contains-plan;
                        $pl has plan-id $pid;
                    fetch
                        $pid;
                """
                results = list(tx.query(query).resolve())
                return [r.get("pid", {}).get("value", "") for r in results]
        except Exception as e:
            logger.error(f"Failed to get plans for project {project_id}: {e}")
            return []
