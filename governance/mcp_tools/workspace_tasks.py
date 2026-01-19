"""
from governance.mcp_tools.common import format_mcp_result
Workspace Task Scanning MCP Tools.

Per P10.10: Workspace Task Capture.
Per DOC-SIZE-01-v1: Modularized from workspace.py.

Tools:
- workspace_scan_tasks: Scan workspace files for tasks (dry run)
- workspace_capture_tasks: Sync tasks to TypeDB
- workspace_list_sources: List files that will be scanned

Created: 2026-01-17 (extracted from workspace.py)
"""

import json
import logging
import os

logger = logging.getLogger(__name__)


def register_workspace_task_tools(mcp) -> None:
    """Register workspace task scanning MCP tools."""

    @mcp.tool()
    def workspace_scan_tasks() -> str:
        """
        Scan workspace files for tasks (dry run - no TypeDB sync).

        Scans:
        - TODO.md: Current sprint tasks
        - docs/backlog/phases/PHASE-*.md: Phase task lists
        - docs/backlog/rd/RD-*.md: R&D task lists

        Returns:
            JSON summary of scanned tasks by source file
        """
        try:
            from governance.workspace_scanner import scan_workspace

            tasks = scan_workspace()

            # Group by source
            by_source = {}
            for t in tasks:
                src = t.source_file or "unknown"
                if src not in by_source:
                    by_source[src] = {"count": 0, "statuses": {}, "sample": []}
                by_source[src]["count"] += 1
                by_source[src]["statuses"][t.status] = (
                    by_source[src]["statuses"].get(t.status, 0) + 1
                )
                if len(by_source[src]["sample"]) < 3:
                    by_source[src]["sample"].append({
                        "task_id": t.task_id,
                        "name": t.name[:80] if t.name else None,
                        "status": t.status,
                    })

            return format_mcp_result({
                "total_tasks": len(tasks),
                "sources": len(by_source),
                "by_source": by_source,
            })
        except Exception as e:
            logger.error(f"workspace_scan_tasks failed: {e}")
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def workspace_capture_tasks() -> str:
        """
        Scan workspace files and sync all tasks to TypeDB.

        Per P10.10: Workspace Task Capture.

        Scans workspace markdown files for tasks and syncs to TypeDB.
        - New tasks are inserted
        - Existing tasks with status changes are updated
        - Tasks with same status are skipped

        Returns:
            JSON with sync statistics (scanned, inserted, updated, skipped, errors)
        """
        try:
            from governance.workspace_scanner import capture_workspace_tasks

            result = capture_workspace_tasks()
            return format_mcp_result(result)
        except Exception as e:
            logger.error(f"workspace_capture_tasks failed: {e}")
            return format_mcp_result({"error": str(e)})

    @mcp.tool()
    def workspace_list_sources() -> str:
        """
        List workspace files that will be scanned for tasks.

        Returns:
            JSON array of source file paths
        """
        from governance.workspace_scanner import WORKSPACE_ROOT

        sources = []

        # TODO.md
        todo_path = os.path.join(WORKSPACE_ROOT, "TODO.md")
        if os.path.exists(todo_path):
            sources.append("TODO.md")

        # Phase docs
        phases_dir = os.path.join(WORKSPACE_ROOT, "docs", "backlog", "phases")
        if os.path.exists(phases_dir):
            for f in os.listdir(phases_dir):
                if f.startswith("PHASE-") and f.endswith(".md"):
                    sources.append(f"docs/backlog/phases/{f}")

        # R&D docs
        rd_dir = os.path.join(WORKSPACE_ROOT, "docs", "backlog", "rd")
        if os.path.exists(rd_dir):
            for f in os.listdir(rd_dir):
                if f.startswith("RD-") and f.endswith(".md"):
                    sources.append(f"docs/backlog/rd/{f}")

        return format_mcp_result({
            "source_count": len(sources),
            "sources": sources,
        })

    logger.info("Registered workspace task scanning tools (3 tools)")
