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

import json
import logging
import os

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
                    logger.warning(f"Could not get TypeDB rules: {e}")

                # Get rules from markdown files
                file_rules = set()
                try:
                    docs = scan_rule_documents()
                    for doc in docs:
                        if doc.rule_ids:
                            file_rules.update(doc.rule_ids)
                    result["rules"]["files_count"] = len(file_rules)
                except Exception as e:
                    logger.warning(f"Could not scan rule documents: {e}")

                # Find divergence
                missing_in_typedb = file_rules - typedb_rules
                missing_in_files = typedb_rules - file_rules

                result["rules"]["missing_in_typedb"] = sorted(list(missing_in_typedb))
                result["rules"]["missing_in_files"] = sorted(list(missing_in_files))
                result["rules"]["synced"] = (
                    len(missing_in_typedb) == 0 and len(missing_in_files) == 0
                )

            except Exception as e:
                logger.error(f"Rules sync check failed: {e}")
                result["rules"]["error"] = str(e)

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
                    logger.warning(f"Could not get TypeDB tasks: {e}")

                # Get tasks from workspace files
                file_tasks = {}
                try:
                    scanned = scan_workspace()
                    for t in scanned:
                        file_tasks[t.task_id] = t.status
                    result["tasks"]["files_count"] = len(file_tasks)
                except Exception as e:
                    logger.warning(f"Could not scan workspace tasks: {e}")

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

            except Exception as e:
                logger.error(f"Tasks sync check failed: {e}")
                result["tasks"]["error"] = str(e)

            # 3. Count Sessions and Evidence files
            try:
                # Get sessions from TypeDB
                try:
                    all_sessions = client.get_all_sessions()
                    result["sessions"]["typedb_count"] = len(all_sessions)
                except Exception as e:
                    logger.warning(f"Could not get TypeDB sessions: {e}")

                # Count evidence files
                evidence_dir = os.path.join(WORKSPACE_ROOT, "evidence")
                if os.path.exists(evidence_dir):
                    evidence_files = [
                        f for f in os.listdir(evidence_dir)
                        if f.endswith(".md") and f.startswith("SESSION-")
                    ]
                    result["sessions"]["evidence_files"] = len(evidence_files)

            except Exception as e:
                logger.error(f"Sessions sync check failed: {e}")
                result["sessions"]["error"] = str(e)

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

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"governance_sync_status failed: {e}")
            return json.dumps({"error": str(e)})

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
            from governance.mcp_tools.common import get_typedb_client

            parser = GapParser()
            all_gaps = parser.parse()  # Returns both open and resolved gaps

            result = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run,
                "total_gaps": len(all_gaps),
                "to_insert": [],
                "to_update": [],
                "skipped": [],
                "errors": [],
            }

            # Get existing tasks from TypeDB
            client = get_typedb_client()
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            try:
                existing_tasks = {t.id: t for t in client.get_all_tasks()}

                for gap in all_gaps:
                    gap_id = gap.id
                    # Map gap status to task status (per GAP-UI-046)
                    # Gaps: "open"/"resolved" -> Tasks: "OPEN"/"CLOSED"
                    task_status = "CLOSED" if gap.is_resolved else "OPEN"

                    if gap_id in existing_tasks:
                        # Check if status update needed
                        existing = existing_tasks[gap_id]
                        existing_status = getattr(existing, 'status', None)
                        needs_update = existing_status != task_status

                        if needs_update:
                            result["to_update"].append({
                                "gap_id": gap_id,
                                "old_status": existing_status,
                                "new_status": task_status,
                            })
                            if not dry_run:
                                try:
                                    # GAP-GAPS-TASKS-001: Update with unified work item attributes
                                    document_path = f"docs/gaps/evidence/{gap_id}.md"
                                    client.update_task(
                                        gap_id,
                                        status=task_status,
                                        item_type="gap",
                                        document_path=document_path
                                    )
                                except Exception as e:
                                    result["errors"].append({
                                        "gap_id": gap_id,
                                        "action": "update",
                                        "error": str(e)
                                    })
                        else:
                            result["skipped"].append(gap_id)
                    else:
                        # New gap - insert as task
                        gap_name = gap.description[:100] if gap.description else gap_id
                        result["to_insert"].append({
                            "gap_id": gap_id,
                            "name": gap_name,
                            "status": task_status,
                            "priority": gap.priority.upper(),
                        })
                        if not dry_run:
                            try:
                                # GAP-GAPS-TASKS-001: Full work item sync with unified attributes
                                document_path = f"docs/gaps/evidence/{gap_id}.md"
                                client.insert_task(
                                    task_id=gap_id,
                                    name=gap_name,
                                    status=task_status,
                                    phase="GAP",
                                    body=f"Priority: {gap.priority.upper()}. {gap.description}",
                                    gap_id=gap_id,  # Self-reference for traceability
                                    item_type="gap",  # Unified work item type
                                    document_path=document_path,  # Source doc reference
                                )
                            except Exception as e:
                                result["errors"].append({
                                    "gap_id": gap_id,
                                    "action": "insert",
                                    "error": str(e)
                                })

                result["summary"] = {
                    "inserts": len(result["to_insert"]),
                    "updates": len(result["to_update"]),
                    "skipped": len(result["skipped"]),
                    "errors": len(result["errors"]),
                }

                return json.dumps(result, indent=2)

            finally:
                client.close()

        except Exception as e:
            logger.error(f"workspace_sync_gaps_to_typedb failed: {e}")
            return json.dumps({"error": str(e)})

    logger.info("Registered workspace sync status tools (3 tools)")
