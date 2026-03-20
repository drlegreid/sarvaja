"""
TypeDB Workspace CRUD Operations.

Per EPIC-GOV-TASKS-V2 Phase 3: Workspace TypeDB Promotion.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)

Created: 2026-03-20
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    """Escape backslash then quotes for TypeQL safety."""
    return value.replace('\\', '\\\\').replace('"', '\\"')


# Allowlist of valid workspace attribute names to prevent injection
_ALLOWED_WS_ATTR_NAMES = frozenset({
    "workspace-name", "workspace-type", "workspace-description", "workspace-status",
})


class WorkspaceCRUDOperations:
    """Workspace CRUD operations for TypeDB. Uses mixin pattern."""

    def insert_workspace(
        self,
        workspace_id: str,
        name: str,
        workspace_type: str,
        description: Optional[str] = None,
        status: str = "active",
    ) -> Optional[Dict[str, Any]]:
        """Insert a new workspace into TypeDB.

        Args:
            workspace_id: Unique workspace ID (e.g., "WS-ABCD1234")
            name: Workspace name
            workspace_type: Type ("governance", "gamedev", "video", etc.)
            description: Optional description
            status: Status ("active" or "archived")

        Returns:
            Created workspace dict or None if failed/duplicate
        """
        from typedb.driver import TransactionType

        existing = self.get_workspace(workspace_id)
        if existing:
            return None

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                wid = _escape(workspace_id)
                parts = [
                    f'has workspace-id "{wid}"',
                    f'has workspace-name "{_escape(name)}"',
                    f'has workspace-type "{_escape(workspace_type)}"',
                    f'has workspace-status "{_escape(status)}"',
                    f'has workspace-created-at {now}',
                ]
                if description:
                    parts.append(f'has workspace-description "{_escape(description)}"')

                query = f"""
                    insert $w isa workspace,
                        {", ".join(parts)};
                """
                tx.query(query).resolve()
                tx.commit()

            return self.get_workspace(workspace_id)
        except Exception as e:
            logger.error(
                f"Failed to insert workspace {workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return None

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get a workspace by ID from TypeDB.

        Args:
            workspace_id: Workspace ID

        Returns:
            Workspace dict or None if not found
        """
        wid = _escape(workspace_id)
        try:
            results = self._execute_query(
                f'match $w isa workspace, has workspace-id "{wid}"; select $w;'
            )
            if not results:
                return None

            ws = {
                "workspace_id": workspace_id,
                "name": "",
                "workspace_type": "",
                "description": "",
                "status": "active",
            }

            for attr, field in [
                ("workspace-name", "name"),
                ("workspace-type", "workspace_type"),
                ("workspace-description", "description"),
                ("workspace-status", "status"),
            ]:
                try:
                    r = self._execute_query(
                        f'match $w isa workspace, has workspace-id "{wid}",'
                        f' has {attr} $v; select $v;'
                    )
                    if r:
                        ws[field] = r[0].get("v")
                except Exception:
                    pass

            return ws
        except Exception as e:
            logger.error(
                f"Failed to get workspace {workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return None

    def list_workspaces(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all workspaces from TypeDB.

        Args:
            limit: Max results
            offset: Pagination offset

        Returns:
            List of workspace dicts
        """
        try:
            results = self._execute_query(
                "match $w isa workspace, has workspace-id $id; select $id;"
            )
            ws_ids = sorted(set(r.get("id", "") for r in results))
            ws_ids = ws_ids[offset:offset + limit]

            workspaces = []
            for wid in ws_ids:
                ws = self.get_workspace(wid)
                if ws:
                    workspaces.append(ws)

            return workspaces
        except Exception as e:
            logger.error(
                f"Failed to list workspaces: {type(e).__name__}", exc_info=True
            )
            return []

    def update_workspace_attrs(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Update workspace attributes in TypeDB.

        Args:
            workspace_id: Workspace ID to update
            name: New name (optional)
            description: New description (optional)
            status: New status (optional)

        Returns:
            True if update succeeded, False otherwise
        """
        current = self.get_workspace(workspace_id)
        if not current:
            return False

        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                wid = _escape(workspace_id)

                if name and name != current.get("name"):
                    _update_ws_attr(tx, wid, "workspace-name",
                                    current.get("name"), name)
                if description is not None and description != current.get("description"):
                    _update_ws_attr(tx, wid, "workspace-description",
                                    current.get("description"), description)
                if status and status != current.get("status"):
                    _update_ws_attr(tx, wid, "workspace-status",
                                    current.get("status"), status)

                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to update workspace {workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace from TypeDB.

        Cleans up relations (project-has-workspace, workspace-has-agent)
        before deleting the entity.

        Args:
            workspace_id: Workspace ID to delete

        Returns:
            True if deleted, False otherwise
        """
        from typedb.driver import TransactionType

        existing = self.get_workspace(workspace_id)
        if not existing:
            return False

        wid = _escape(workspace_id)

        try:
            # Clean up relations first (best-effort, separate transactions)
            for rel_query in [
                f'match $w isa workspace, has workspace-id "{wid}";'
                f' $r (workspace-member: $w) isa project-has-workspace; delete $r;',
                f'match $w isa workspace, has workspace-id "{wid}";'
                f' $r (agent-workspace: $w) isa workspace-has-agent; delete $r;',
            ]:
                try:
                    with self._driver.transaction(
                        self.database, TransactionType.WRITE
                    ) as tx:
                        tx.query(rel_query).resolve()
                        tx.commit()
                except Exception:
                    pass

            # Delete entity
            with self._driver.transaction(
                self.database, TransactionType.WRITE
            ) as tx:
                tx.query(
                    f'match $w isa workspace, has workspace-id "{wid}"; delete $w;'
                ).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(
                f"Failed to delete workspace {workspace_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False


def _update_ws_attr(
    tx, workspace_id_escaped: str, attr_name: str,
    old_value: Optional[str], new_value: str
):
    """Delete old attribute value and insert new one for a workspace."""
    if attr_name not in _ALLOWED_WS_ATTR_NAMES:
        raise ValueError(f"Disallowed attribute name: {attr_name!r}")

    new_escaped = _escape(new_value)

    if old_value is not None:
        old_escaped = _escape(old_value)
        tx.query(f'''
            match $w isa workspace, has workspace-id "{workspace_id_escaped}",
                has {attr_name} $v;
                $v == "{old_escaped}";
            delete has $v of $w;
        ''').resolve()

    tx.query(f'''
        match $w isa workspace, has workspace-id "{workspace_id_escaped}";
        insert $w has {attr_name} "{new_escaped}";
    ''').resolve()
