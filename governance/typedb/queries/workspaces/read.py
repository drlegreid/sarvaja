"""
TypeDB Workspace Read Queries.

Per EPIC-GOV-TASKS-V2 Phase 3: Workspace TypeDB Promotion.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines)

Created: 2026-03-20
"""

import logging
from typing import List, Optional

from ...entities import Workspace

logger = logging.getLogger(__name__)


class WorkspaceReadQueries:
    """Workspace read query operations for TypeDB. Mixin pattern."""

    def get_all_workspaces(
        self,
        status: Optional[str] = None,
        workspace_type: Optional[str] = None,
    ) -> List[Workspace]:
        """Get all workspaces with optional filters.

        Args:
            status: Filter by status ("active", "archived")
            workspace_type: Filter by workspace type

        Returns:
            List of Workspace entities
        """
        try:
            filters = []
            if status:
                status_esc = status.replace('\\', '\\\\').replace('"', '\\"')
                filters.append(f'has workspace-status "{status_esc}"')
            if workspace_type:
                wt_esc = workspace_type.replace('\\', '\\\\').replace('"', '\\"')
                filters.append(f'has workspace-type "{wt_esc}"')

            filter_clause = ", ".join(filters) if filters else ""
            query = f"""
                match $w isa workspace,
                    has workspace-id $id,
                    has workspace-name $name,
                    has workspace-type $wtype,
                    has workspace-status $wstatus
                    {", " + filter_clause if filter_clause else ""};
                select $id, $name, $wtype, $wstatus;
            """
            results = self._execute_query(query)

            workspaces = []
            for r in results:
                ws = Workspace(
                    id=r.get("id"),
                    name=r.get("name"),
                    workspace_type=r.get("wtype"),
                    status=r.get("wstatus", "active"),
                )
                workspaces.append(ws)

            return workspaces
        except Exception as e:
            logger.error(
                f"Failed to get all workspaces: {type(e).__name__}",
                exc_info=True,
            )
            return []
