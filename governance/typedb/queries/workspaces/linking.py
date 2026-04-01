"""
TypeDB Workspace Linking Operations.

Per EPIC-GOV-TASKS-V2 Phase 3: Workspace TypeDB Promotion.
Per EPIC-GOV-TASKS-V2 Phase 4: Task-Workspace Bidirectional Linking.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)

Handles:
- project-has-workspace relation
- workspace-has-agent relation
- workspace-has-task relation (Phase 4)

Created: 2026-03-20
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    """Escape backslash then quotes for TypeQL safety."""
    return value.replace('\\', '\\\\').replace('"', '\\"')


class WorkspaceLinkingOperations:
    """Workspace linking operations for TypeDB. Uses mixin pattern."""

    def link_workspace_to_project(
        self, workspace_id: str, project_id: str
    ) -> bool:
        """Link a workspace to a project via project-has-workspace relation.

        Args:
            workspace_id: Workspace ID
            project_id: Project ID

        Returns:
            True if link created, False otherwise
        """
        from typedb.driver import TransactionType

        wid = _escape(workspace_id)
        pid = _escape(project_id)

        try:
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{pid}";
                        $w isa workspace, has workspace-id "{wid}";
                    insert
                        (owning-project: $p, workspace-member: $w)
                            isa project-has-workspace;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to link workspace {workspace_id} to project "
                f"{project_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def link_workspace_to_agent(
        self, workspace_id: str, agent_id: str
    ) -> bool:
        """Link a workspace to an agent via workspace-has-agent relation.

        Args:
            workspace_id: Workspace ID
            agent_id: Agent ID

        Returns:
            True if link created, False otherwise
        """
        from typedb.driver import TransactionType

        wid = _escape(workspace_id)
        aid = _escape(agent_id)

        try:
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                query = f"""
                    match
                        $w isa workspace, has workspace-id "{wid}";
                        $a isa agent, has agent-id "{aid}";
                    insert
                        (agent-workspace: $w, assigned-agent: $a)
                            isa workspace-has-agent;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to link workspace {workspace_id} to agent "
                f"{agent_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def unlink_agent_from_workspace(
        self, workspace_id: str, agent_id: str
    ) -> bool:
        """Remove agent from workspace (delete workspace-has-agent relation).

        Args:
            workspace_id: Workspace ID
            agent_id: Agent ID

        Returns:
            True if unlinked, False otherwise
        """
        from typedb.driver import TransactionType

        wid = _escape(workspace_id)
        aid = _escape(agent_id)

        try:
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                query = f"""
                    match
                        $w isa workspace, has workspace-id "{wid}";
                        $a isa agent, has agent-id "{aid}";
                        $rel (agent-workspace: $w, assigned-agent: $a)
                            isa workspace-has-agent;
                    delete $rel;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to unlink agent {agent_id} from workspace "
                f"{workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def get_workspaces_for_project(self, project_id: str) -> List[str]:
        """Get all workspace IDs linked to a project.

        Args:
            project_id: Project ID

        Returns:
            List of workspace IDs
        """
        pid = _escape(project_id)
        try:
            results = self._execute_query(
                f'match $p isa project, has project-id "{pid}";'
                f' (owning-project: $p, workspace-member: $w)'
                f' isa project-has-workspace;'
                f' $w has workspace-id $wid; select $wid;'
            )
            return [r.get("wid", "") for r in results]
        except Exception as e:
            logger.error(
                f"Failed to get workspaces for project {project_id}: "
                f"{type(e).__name__}",
                exc_info=True,
            )
            return []

    def get_agents_for_workspace(self, workspace_id: str) -> List[str]:
        """Get all agent IDs linked to a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of agent IDs
        """
        wid = _escape(workspace_id)
        try:
            results = self._execute_query(
                f'match $w isa workspace, has workspace-id "{wid}";'
                f' (agent-workspace: $w, assigned-agent: $a)'
                f' isa workspace-has-agent;'
                f' $a has agent-id $aid; select $aid;'
            )
            return [r.get("aid", "") for r in results]
        except Exception as e:
            logger.error(
                f"Failed to get agents for workspace {workspace_id}: "
                f"{type(e).__name__}",
                exc_info=True,
            )
            return []

    # ── Task-Workspace Linking (EPIC-GOV-TASKS-V2 Phase 4) ──────

    def link_task_to_workspace(
        self, workspace_id: str, task_id: str
    ) -> bool:
        """Link a task to a workspace via workspace-has-task relation.

        Args:
            workspace_id: Workspace ID
            task_id: Task ID

        Returns:
            True if link created, False otherwise
        """
        from typedb.driver import TransactionType
        from governance.typedb.queries.tasks.linking import _relation_exists

        wid = _escape(workspace_id)
        tid = _escape(task_id)

        try:
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                # SRVJ-BUG-IDEMP-LINK-01: Idempotency guard
                check_q = f"""
                    match
                        $w isa workspace, has workspace-id "{wid}";
                        $t isa task, has task-id "{tid}";
                        (task-workspace: $w, assigned-task: $t)
                            isa workspace-has-task;
                """
                if _relation_exists(tx, check_q):
                    logger.debug(
                        f"Workspace-task link already exists: "
                        f"{task_id} -> {workspace_id}"
                    )
                    tx.commit()
                    return True

                query = f"""
                    match
                        $w isa workspace, has workspace-id "{wid}";
                        $t isa task, has task-id "{tid}";
                    insert
                        (task-workspace: $w, assigned-task: $t)
                            isa workspace-has-task;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to link task {task_id} to workspace "
                f"{workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def unlink_task_from_workspace(
        self, workspace_id: str, task_id: str
    ) -> bool:
        """Remove task from workspace (delete workspace-has-task relation).

        Args:
            workspace_id: Workspace ID
            task_id: Task ID

        Returns:
            True if unlinked, False otherwise
        """
        from typedb.driver import TransactionType

        wid = _escape(workspace_id)
        tid = _escape(task_id)

        try:
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                query = f"""
                    match
                        $w isa workspace, has workspace-id "{wid}";
                        $t isa task, has task-id "{tid}";
                        $rel (task-workspace: $w, assigned-task: $t)
                            isa workspace-has-task;
                    delete $rel;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to unlink task {task_id} from workspace "
                f"{workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def get_tasks_for_workspace(self, workspace_id: str) -> List[str]:
        """Get all task IDs linked to a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of task IDs
        """
        wid = _escape(workspace_id)
        try:
            results = self._execute_query(
                f'match $w isa workspace, has workspace-id "{wid}";'
                f' (task-workspace: $w, assigned-task: $t)'
                f' isa workspace-has-task;'
                f' $t has task-id $tid; select $tid;'
            )
            return [r.get("tid", "") for r in results]
        except Exception as e:
            logger.error(
                f"Failed to get tasks for workspace {workspace_id}: "
                f"{type(e).__name__}",
                exc_info=True,
            )
            return []

    def get_workspace_for_task(self, task_id: str) -> Optional[str]:
        """Get workspace ID for a task (reverse lookup).

        Args:
            task_id: Task ID

        Returns:
            Workspace ID or None if task has no workspace
        """
        tid = _escape(task_id)
        try:
            results = self._execute_query(
                f'match $t isa task, has task-id "{tid}";'
                f' (task-workspace: $w, assigned-task: $t)'
                f' isa workspace-has-task;'
                f' $w has workspace-id $wid; select $wid;'
            )
            if results:
                return results[0].get("wid")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get workspace for task {task_id}: "
                f"{type(e).__name__}",
                exc_info=True,
            )
            return None
