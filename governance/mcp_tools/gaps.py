"""
Gap Backlog MCP Tools
=====================
Gap parsing and backlog synchronization operations.

Per TASK 1.3: Ensures real backlog (GAP-INDEX.md) syncs with Claude tasks.
Per TASK 5: Uses unified WorkItem abstraction for gaps/tasks/r&d items.

Prevents the anti-pattern of creating self-referential todo lists that
ignore the actual project backlog.
"""

import logging
from typing import List
from governance.utils.gap_parser import GapParser, get_gap_summary
from governance.utils.work_item import WorkItem, WorkItemType, sort_by_priority
from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_gap_tools(mcp) -> None:
    """Register gap-related MCP tools."""

    @mcp.tool()
    def backlog_get(limit: int = 20) -> str:
        """
        Get prioritized open gaps from GAP-INDEX.md for session backlog.

        Use this at session start to sync real backlog with Claude tasks.
        Returns gaps sorted by priority: CRITICAL > HIGH > MEDIUM > LOW.

        Args:
            limit: Maximum number of gaps to return (default: 20)

        Returns:
            JSON object with summary and prioritized gap list
        """
        try:
            parser = GapParser()
            summary = parser.get_summary()
            gaps = parser.get_prioritized(limit)

            result = {
                "summary": {
                    "total": summary["total"],
                    "open": summary["open"],
                    "resolved": summary["resolved"],
                    "critical_count": summary["critical_count"],
                    "high_count": summary["high_count"],
                },
                "gaps": [g.to_dict() for g in gaps],
                "todo_format": [g.to_todo_format() for g in gaps],
            }
            return format_mcp_result(result)

        # BUG-370-GAP-001: Log full error but return only type name
        except FileNotFoundError as e:
            logger.error(f"backlog_get file not found: {e}", exc_info=True)
            return format_mcp_result({"error": f"backlog_get failed: FileNotFoundError"})
        except Exception as e:
            logger.error(f"backlog_get failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"backlog_get failed: {type(e).__name__}"})

    @mcp.tool()
    def gaps_summary() -> str:
        """
        Get summary statistics for all gaps.

        Returns:
            JSON object with gap counts by priority and resolution status
        """
        try:
            summary = get_gap_summary()
            return format_mcp_result(summary)
        # BUG-370-GAP-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"gaps_summary failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"gaps_summary failed: {type(e).__name__}"})

    @mcp.tool()
    def gaps_critical() -> str:
        """
        Get all CRITICAL priority gaps.

        Returns:
            JSON array of critical gaps
        """
        try:
            parser = GapParser()
            critical = parser.get_by_priority("CRITICAL")
            return format_mcp_result({
                "count": len(critical),
                "gaps": [g.to_dict() for g in critical],
            })
        # BUG-370-GAP-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"gaps_critical failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"gaps_critical failed: {type(e).__name__}"})

    @mcp.tool()
    def backlog_unified(limit: int = 30, include_tasks: bool = True) -> str:
        """
        Get unified backlog combining gaps and tasks as WorkItems.

        Per TASK 5: Unified WorkItem abstraction for gaps/tasks/r&d items.
        Returns all work items sorted by priority (CRITICAL first).

        Args:
            limit: Maximum total items to return (default: 30)
            include_tasks: Whether to include TypeDB tasks (default: True)

        Returns:
            JSON object with unified backlog as WorkItems
        """
        from governance.mcp_tools.common import get_typedb_client, format_mcp_result

        work_items: List[WorkItem] = []

        # 1. Get gaps from GAP-INDEX.md
        try:
            parser = GapParser()
            gaps = parser.get_open_gaps()
            for gap in gaps:
                work_items.append(gap.to_work_item())
        except Exception as e:
            logger.debug(f"Gap parsing failed, continuing: {e}")

        # 2. Get tasks from TypeDB (if requested)
        if include_tasks:
            try:
                client = get_typedb_client()
                if client.connect():
                    tasks = client.get_all_tasks()
                    for task in tasks:
                        item = WorkItem.from_task(task, source="TypeDB")
                        # Only include open tasks
                        if item.is_open:
                            work_items.append(item)
                    client.close()
            except Exception as e:
                logger.debug(f"TypeDB task fetch failed, continuing: {e}")

        # 3. Sort by priority and limit
        sorted_items = sort_by_priority(work_items)[:limit]

        # 4. Group by type for summary
        by_type = {
            "gap": [i for i in sorted_items if i.item_type == WorkItemType.GAP],
            "task": [i for i in sorted_items if i.item_type == WorkItemType.TASK],
            "rd": [i for i in sorted_items if i.item_type == WorkItemType.RD],
        }

        result = {
            "summary": {
                "total": len(sorted_items),
                "gaps": len(by_type["gap"]),
                "tasks": len(by_type["task"]),
                "rd_items": len(by_type["rd"]),
            },
            "items": [item.to_dict() for item in sorted_items],
            "todo_format": [item.to_todo_format() for item in sorted_items],
        }
        return format_mcp_result(result)
