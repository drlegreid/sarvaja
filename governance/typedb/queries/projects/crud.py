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

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                parts = [f'has project-id "{project_id}"']
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
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                query = f"""
                    match
                        $p isa project, has project-id "{project_id}";
                    fetch
                        $p: project-id, project-name, project-path;
                """
                results = list(tx.query(query).resolve())
                if not results:
                    return None

                row = results[0]
                p = row.get("p", {})
                return {
                    "project_id": _extract_attr(p, "project-id"),
                    "name": _extract_attr(p, "project-name"),
                    "path": _extract_attr(p, "project-path"),
                }
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all projects from TypeDB."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                query = """
                    match
                        $p isa project;
                    fetch
                        $p: project-id, project-name, project-path;
                """
                results = list(tx.query(query).resolve())

                projects = []
                for row in results:
                    p = row.get("p", {})
                    projects.append({
                        "project_id": _extract_attr(p, "project-id"),
                        "name": _extract_attr(p, "project-name"),
                        "path": _extract_attr(p, "project-path"),
                    })

                # Sort by project_id, apply pagination
                projects.sort(key=lambda x: x.get("project_id", ""))
                return projects[offset:offset + limit]
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def delete_project(self, project_id: str) -> bool:
        """Delete a project from TypeDB."""
        from typedb.driver import TransactionType

        existing = self.get_project(project_id)
        if not existing:
            return False

        try:
            # Delete relations first
            for rel_query in [
                f'match $p isa project, has project-id "{project_id}"; $r (parent-project: $p) isa project-contains-plan; delete $r;',
                f'match $p isa project, has project-id "{project_id}"; $r (session-project: $p) isa project-has-session; delete $r;',
            ]:
                try:
                    with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                        tx.query(rel_query).resolve()
                        tx.commit()
                except Exception:
                    pass

            # Delete entity
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                tx.query(f'match $p isa project, has project-id "{project_id}"; delete $p;').resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False


def _extract_attr(entity_data: dict, attr_name: str) -> Optional[str]:
    """Extract a single attribute value from TypeDB fetch result."""
    attr = entity_data.get(attr_name)
    if attr is None:
        return None
    if isinstance(attr, list):
        return attr[0].get("value") if attr else None
    if isinstance(attr, dict):
        return attr.get("value")
    return str(attr)
