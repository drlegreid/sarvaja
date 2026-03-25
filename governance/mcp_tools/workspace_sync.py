"""
Workspace Sync Status MCP Tools.

Per GAP-SYNC-002: Divergence Validation Workflow.
Per DOC-SIZE-01-v1: Modularized from workspace.py.

Tools:
- governance_sync_status: Report divergence between TypeDB and workspace files
- workspace_sync_status: Alias for governance_sync_status

Created: 2026-01-17 (extracted from workspace.py)
Refactored: 2026-01-19 (removed deprecated functions, inlined aliases)
"""

import logging
import os

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_workspace_sync_tools(mcp) -> None:
    """Register workspace sync status MCP tools."""

    @mcp.tool()
    def governance_sync_status() -> str:
        """
        Report divergence between TypeDB and workspace files.

        Per GAP-SYNC-002: Divergence Validation Workflow.

        Compares:
        - TypeDB rules vs docs/rules/*.md
        - TypeDB tasks vs TODO.md
        - TypeDB sessions vs evidence/*.md

        Returns:
            JSON divergence report with:
            - rules: {typedb_count, files_count, missing_in_typedb, missing_in_files}
            - tasks: {typedb_count, files_count, status_mismatches}
            - sessions: {typedb_count, evidence_files}
            - sync_needed: boolean
        """
        result = {
            "rules": {
                "typedb_count": 0,
                "files_count": 0,
                "missing_in_typedb": [],
                "missing_in_files": [],
                "synced": True,
            },
            "tasks": {
                "typedb_count": 0,
                "files_count": 0,
                "status_mismatches": [],
                "missing_in_typedb": [],
                "synced": True,
            },
            "sessions": {
                "typedb_count": 0,
                "evidence_files": 0,
                "synced": True,
            },
            "sync_needed": False,
            "timestamp": None,
        }

        try:
            from datetime import datetime
            from governance.workspace_scanner import WORKSPACE_ROOT

            result["timestamp"] = datetime.now().isoformat()

            # 1. Compare Rules: TypeDB vs docs/rules/*.md
            client = None
            try:
                from governance.client import TypeDBClient
                from governance.rule_linker import scan_rule_documents

                # Get rules from TypeDB
                client = TypeDBClient()
                client.connect()
                typedb_rules = set()
                try:
                    all_rules = client.get_all_rules()
                    typedb_rules = {r.id for r in all_rules}
                    result["rules"]["typedb_count"] = len(typedb_rules)
                except Exception as e:
                    # BUG-471-WSY-001: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Could not get TypeDB rules: {type(e).__name__}", exc_info=True)

                # Get rules from markdown files
                file_rules = set()
                try:
                    docs = scan_rule_documents()
                    for doc in docs:
                        if doc.rule_ids:
                            file_rules.update(doc.rule_ids)
                    result["rules"]["files_count"] = len(file_rules)
                except Exception as e:
                    # BUG-471-WSY-002: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Could not scan rule documents: {type(e).__name__}", exc_info=True)

                # Find divergence
                missing_in_typedb = file_rules - typedb_rules
                missing_in_files = typedb_rules - file_rules

                result["rules"]["missing_in_typedb"] = sorted(list(missing_in_typedb))
                result["rules"]["missing_in_files"] = sorted(list(missing_in_files))
                result["rules"]["synced"] = (
                    len(missing_in_typedb) == 0 and len(missing_in_files) == 0
                )

            # BUG-471-WSY-003: Sanitize logger message — exc_info=True already captures full stack
            except Exception as e:
                logger.error(f"Rules sync check failed: {type(e).__name__}", exc_info=True)
                result["rules"]["error"] = type(e).__name__

            # 2. Compare Tasks: TypeDB vs TODO.md
            try:
                from governance.workspace_scanner import scan_workspace

                # Get tasks from TypeDB
                typedb_tasks = {}
                try:
                    all_tasks = client.get_all_tasks()
                    for t in all_tasks:
                        typedb_tasks[t.id] = t.status
                    result["tasks"]["typedb_count"] = len(typedb_tasks)
                except Exception as e:
                    # BUG-471-WSY-004: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Could not get TypeDB tasks: {type(e).__name__}", exc_info=True)

                # Get tasks from workspace files
                file_tasks = {}
                try:
                    scanned = scan_workspace()
                    for t in scanned:
                        file_tasks[t.task_id] = t.status
                    result["tasks"]["files_count"] = len(file_tasks)
                except Exception as e:
                    # BUG-471-WSY-005: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Could not scan workspace tasks: {type(e).__name__}", exc_info=True)

                # Find status mismatches and missing tasks
                mismatches = []
                missing_in_typedb = []

                for task_id, file_status in file_tasks.items():
                    if task_id not in typedb_tasks:
                        missing_in_typedb.append(task_id)
                    elif typedb_tasks[task_id] != file_status:
                        mismatches.append({
                            "task_id": task_id,
                            "typedb_status": typedb_tasks[task_id],
                            "file_status": file_status,
                        })

                result["tasks"]["status_mismatches"] = mismatches[:10]
                result["tasks"]["missing_in_typedb"] = missing_in_typedb[:10]
                result["tasks"]["synced"] = (
                    len(mismatches) == 0 and len(missing_in_typedb) == 0
                )

            # BUG-471-WSY-006: Sanitize logger message — exc_info=True already captures full stack
            except Exception as e:
                logger.error(f"Tasks sync check failed: {type(e).__name__}", exc_info=True)
                result["tasks"]["error"] = type(e).__name__

            # 3. Count Sessions and Evidence files
            try:
                # Get sessions from TypeDB
                try:
                    all_sessions = client.get_all_sessions()
                    result["sessions"]["typedb_count"] = len(all_sessions)
                except Exception as e:
                    # BUG-471-WSY-007: Sanitize logger message + add exc_info for stack trace preservation
                    logger.warning(f"Could not get TypeDB sessions: {type(e).__name__}", exc_info=True)

                # Count evidence files
                evidence_dir = os.path.join(WORKSPACE_ROOT, "evidence")
                if os.path.exists(evidence_dir):
                    evidence_files = [
                        f for f in os.listdir(evidence_dir)
                        if f.endswith(".md") and f.startswith("SESSION-")
                    ]
                    result["sessions"]["evidence_files"] = len(evidence_files)

            # BUG-471-WSY-008: Sanitize logger message — exc_info=True already captures full stack
            except Exception as e:
                logger.error(f"Sessions sync check failed: {type(e).__name__}", exc_info=True)
                result["sessions"]["error"] = type(e).__name__

            # Determine if sync is needed
            result["sync_needed"] = (
                not result["rules"]["synced"] or
                not result["tasks"]["synced"] or
                not result["sessions"]["synced"]
            )

            # Cleanup client connection
            if client:
                try:
                    client.close()
                except Exception:
                    pass

            return format_mcp_result(result)

        # BUG-471-WSY-009: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"governance_sync_status failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"governance_sync_status failed: {type(e).__name__}"})

    @mcp.tool()
    def workspace_sync_status() -> str:
        """Get sync status. Alias for governance_sync_status."""
        return governance_sync_status()

    @mcp.tool()
    def workspace_sync_gaps_to_typedb(dry_run: bool = True) -> str:
        """
        Sync gaps from GAP-INDEX.md to TypeDB as tasks.

        Per GAP-GAPS-TASKS-001: Unified work items architecture.

        Creates task entities for each gap with:
        - task_id = gap.id (e.g., "GAP-001")
        - item_type = "gap"
        - document_path = "docs/gaps/evidence/{id}.md"
        - status = "open" or "resolved"

        Args:
            dry_run: If True, only report what would be synced (default: True)

        Returns:
            JSON with sync statistics
        """
        try:
            from datetime import datetime
            from governance.utils.gap_parser import GapParser
            from governance.mcp_tools.common import typedb_client

            parser = GapParser()
            all_gaps = parser.parse()

            result = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run, "total_gaps": len(all_gaps),
                "to_insert": [], "to_update": [], "skipped": [], "errors": [],
            }

            with typedb_client() as client:
                existing_tasks = {t.id: t for t in client.get_all_tasks()}

                for gap in all_gaps:
                    gap_id = gap.id
                    task_status = "DONE" if gap.is_resolved else "OPEN"
                    document_path = f"docs/gaps/evidence/{gap_id}.md"

                    if gap_id in existing_tasks:
                        existing_status = getattr(existing_tasks[gap_id], 'status', None)
                        if existing_status != task_status:
                            result["to_update"].append({
                                "gap_id": gap_id, "old_status": existing_status,
                                "new_status": task_status,
                            })
                            if not dry_run:
                                try:
                                    client.update_task(gap_id, status=task_status,
                                                       item_type="gap", document_path=document_path)
                                # BUG-471-WSY-010: Sanitize logger message — exc_info=True already captures full stack
                                except Exception as e:
                                    logger.error(f"Gap sync update {gap_id} failed: {type(e).__name__}", exc_info=True)
                                    result["errors"].append({"gap_id": gap_id, "action": "update", "error": type(e).__name__})
                        else:
                            result["skipped"].append(gap_id)
                    else:
                        gap_name = gap.description[:100] if gap.description else gap_id
                        result["to_insert"].append({
                            "gap_id": gap_id, "name": gap_name,
                            "status": task_status, "priority": gap.priority.upper(),
                        })
                        if not dry_run:
                            try:
                                client.insert_task(
                                    task_id=gap_id, name=gap_name, status=task_status,
                                    phase="GAP", body=f"Priority: {gap.priority.upper()}. {gap.description}",
                                    gap_id=gap_id, item_type="gap", document_path=document_path,
                                )
                            # BUG-471-WSY-011: Sanitize logger message — exc_info=True already captures full stack
                            except Exception as e:
                                logger.error(f"Gap sync insert {gap_id} failed: {type(e).__name__}", exc_info=True)
                                result["errors"].append({"gap_id": gap_id, "action": "insert", "error": type(e).__name__})

                result["summary"] = {
                    "inserts": len(result["to_insert"]), "updates": len(result["to_update"]),
                    "skipped": len(result["skipped"]), "errors": len(result["errors"]),
                }
                return format_mcp_result(result)

        # BUG-471-WSY-012: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"workspace_sync_gaps_to_typedb failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"workspace_sync_gaps_to_typedb failed: {type(e).__name__}"})

    logger.info("Registered workspace sync status tools (3 tools)")
