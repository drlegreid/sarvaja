"""
Task Evidence MCP Tools
=======================
Task listing and dependency tracking operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py

Tools:
- governance_list_tasks: List R&D and backlog tasks
- governance_get_task_deps: Get task dependencies

Created: 2024-12-28
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

from governance.mcp_tools.common import format_mcp_result
from .common import BACKLOG_DIR


def register_task_tools(mcp) -> None:
    """Register task-related MCP tools."""

    @mcp.tool()
    def governance_list_tasks(
        phase: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        List R&D and backlog tasks.

        Args:
            phase: Filter by phase (e.g., "P7", "P9", "FH", "RD")
            status: Filter by status (e.g., "TODO", "DONE", "IN_PROGRESS")

        Returns:
            JSON array of tasks with ID, name, status, and priority
        """
        # Try TypeDB first (DECISION-003: TypeDB-First Strategy)
        try:
            from governance.client import TypeDBClient
            from dataclasses import asdict

            client = TypeDBClient()
            if client.connect():
                try:
                    tasks_from_db = client.get_all_tasks()
                    tasks = []
                    for t in tasks_from_db:
                        task_dict = asdict(t) if hasattr(t, '__dataclass_fields__') else t
                        task_status = task_dict.get('status', '')
                        task_phase = task_dict.get('phase', '')

                        # Apply filters
                        if phase and task_phase != phase:
                            continue
                        if status and task_status.upper() != status.upper():
                            continue

                        tasks.append({
                            "task_id": task_dict.get('id'),
                            "name": task_dict.get('name', ''),
                            "status": task_status,
                            "phase": task_phase,
                            "description": task_dict.get('body', '') or '',
                            "agent_id": task_dict.get('agent_id'),
                            "gap_id": task_dict.get('gap_id')
                        })

                    return format_mcp_result({
                        "tasks": tasks,
                        "count": len(tasks),
                        "phases": list(set(t["phase"] for t in tasks)),
                        "source": "typedb"
                    })
                finally:
                    client.close()
        except Exception as e:
            # BUG-477-ETK-1: Sanitize debug/info logger
            logger.debug(f"TypeDB task list failed, falling back to markdown: {type(e).__name__}")

        # Fallback: Parse R&D-BACKLOG.md (backward compatibility)
        tasks = []
        backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
        if backlog_file.exists():
            content = backlog_file.read_text(encoding="utf-8")

            # Parse task tables
            table_pattern = r"\|\s*([\w.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

            for match in re.finditer(table_pattern, content):
                task_id, name_or_status, status_or_desc, priority_or_notes = match.groups()

                # Clean up
                task_id = task_id.strip()
                name_or_status = name_or_status.strip()
                status_or_desc = status_or_desc.strip()

                # Skip headers and separators
                if task_id in ("ID", "Task", "Pillar", "Factor") or task_id.startswith("-"):
                    continue
                if not re.match(r'^(P\d+\.\d+|RD-\d+|FH-\d+)', task_id):
                    continue

                # Normalize status
                if "✅" in status_or_desc or "DONE" in status_or_desc:
                    task_status = "DONE"
                elif "📋" in status_or_desc or "TODO" in status_or_desc:
                    task_status = "TODO"
                elif "⏸️" in status_or_desc or "BLOCKED" in status_or_desc:
                    task_status = "BLOCKED"
                elif "🔄" in status_or_desc or "IN_PROGRESS" in status_or_desc:
                    task_status = "IN_PROGRESS"
                else:
                    task_status = "TODO"

                # Determine phase from ID
                task_phase = "UNKNOWN"
                if task_id.startswith("P"):
                    task_phase = task_id.split(".")[0]
                elif task_id.startswith("RD-"):
                    task_phase = "RD"
                elif task_id.startswith("FH-"):
                    task_phase = "FH"

                # Apply filters
                if phase and task_phase != phase:
                    continue
                if status and task_status != status:
                    continue

                tasks.append({
                    "task_id": task_id,
                    "name": name_or_status[:100],
                    "status": task_status,
                    "phase": task_phase,
                    "description": status_or_desc[:200] if len(status_or_desc) > 10 else ""
                })

        return format_mcp_result({
            "tasks": tasks,
            "count": len(tasks),
            "phases": list(set(t["phase"] for t in tasks)),
            "source": "markdown"
        })

    @mcp.tool()
    def governance_get_task_deps(task_id: str) -> str:
        """
        Get task dependencies (what blocks this task, what this task blocks).

        Args:
            task_id: Task ID (e.g., "P7.1", "P9.1")

        Returns:
            JSON object with blocked_by and blocks arrays
        """
        # Parse R&D backlog for dependency hints
        backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"

        result = {
            "task_id": task_id,
            "blocked_by": [],
            "blocks": []
        }

        if backlog_file.exists():
            content = backlog_file.read_text(encoding="utf-8")

            # Look for Dependencies: section
            deps_pattern = r"Dependencies:\s*\n((?:[-*]\s*.+\n)+)"
            for match in re.finditer(deps_pattern, content):
                deps_text = match.group(1)
                # Check if our task is mentioned
                if task_id in deps_text:
                    # Extract dependency relationships
                    for line in deps_text.split("\n"):
                        if task_id in line:
                            # Parse "Phase X: Y required" patterns
                            phase_match = re.search(r"Phase\s*(\d+)", line)
                            if phase_match:
                                result["blocked_by"].append(f"P{phase_match.group(1)}")

            # Infer dependencies from phase ordering
            if task_id.startswith("P"):
                phase_num = float(task_id[1:].replace("-", "."))
                # Tasks in earlier phases block later ones
                if phase_num > 7:
                    result["blocked_by"].append("P7 (TypeDB-First)")
                if phase_num > 3:
                    result["blocked_by"].append("P3 (Stabilization)")

        return format_mcp_result(result)
