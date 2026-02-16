"""
TypeDB Project CRUD Operations.

Per GOV-PROJECT-01-v1: Project hierarchy management.
Created: 2026-02-11
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ProjectCRUDOperations:
    """Project CRUD operations for TypeDB. Uses mixin pattern."""

    def insert_project(
        self,
        project_id: str,
        name: str,
        path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Insert a new project into TypeDB."""
        from typedb.driver import TransactionType

        existing = self.get_project(project_id)
        if existing:
            return None

        # BUG-TYPEQL-ESCAPE-PROJECT-001: Escape project_id for TypeQL safety
        project_id_escaped = project_id.replace('"', '\\"')

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                parts = [f'has project-id "{project_id_escaped}"']
                name_esc = name.replace('"', '\\"')
                parts.append(f'has project-name "{name_esc}"')
                if path:
                    path_esc = path.replace('"', '\\"')
                    parts.append(f'has project-path "{path_esc}"')

                query = f"""
                    insert $p isa project,
                        {", ".join(parts)};
                """
                tx.query(query).resolve()
                tx.commit()

            return self.get_project(project_id)
        except Exception as e:
            logger.error(f"Failed to insert project {project_id}: {e}")
            return None

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID from TypeDB."""
        # BUG-TYPEQL-ESCAPE-PROJECT-001: Escape project_id for TypeQL safety
        pid = project_id.replace('"', '\\"')
        try:
            # Check existence via _execute_query (handles concept→value)
            results = self._execute_query(
                f'match $p isa project, has project-id "{pid}"; select $p;'
            )
            if not results:
                return None

            project = {"project_id": project_id, "name": "", "path": None}

            for attr, field in [("project-name", "name"), ("project-path", "path")]:
                try:
                    r = self._execute_query(
                        f'match $p isa project, has project-id "{pid}", has {attr} $v; select $v;'
                    )
                    if r:
                        project[field] = r[0].get("v")
                except Exception:
                    pass

            return project
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all projects from TypeDB."""
        try:
            results = self._execute_query(
                "match $p isa project, has project-id $id; select $id;"
            )

            # BUG-API-PROJECTS-001: Deduplicate project IDs (TypeDB can have
            # multiple entities with same project-id from repeated inserts)
            project_ids = sorted(set(r.get("id", "") for r in results))
            project_ids = project_ids[offset:offset + limit]

            projects = []
            for pid in project_ids:
                proj = self.get_project(pid)
                if proj:
                    projects.append(proj)

            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def delete_project(self, project_id: str) -> bool:
        """Delete a project from TypeDB."""
        from typedb.driver import TransactionType

        existing = self.get_project(project_id)
        if not existing:
            return False

        # BUG-TYPEQL-ESCAPE-PROJECT-001: Escape project_id for TypeQL safety
        pid = project_id.replace('"', '\\"')

        try:
            # Delete relations first
            for rel_query in [
                f'match $p isa project, has project-id "{pid}"; $r (parent-project: $p) isa project-contains-plan; delete $r;',
                f'match $p isa project, has project-id "{pid}"; $r (session-project: $p) isa project-has-session; delete $r;',
            ]:
                try:
                    with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                        tx.query(rel_query).resolve()
                        tx.commit()
                except Exception:
                    pass

            # Delete entity
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                tx.query(f'match $p isa project, has project-id "{pid}"; delete $p;').resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
