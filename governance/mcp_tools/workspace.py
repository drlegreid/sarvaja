"""
MCP Tools for Workspace Operations.

Per P10.10: Workspace Task Capture.
Per P10.8: TypeDB-Filesystem Rule Linking.
Per DECISION-003: TypeDB-First Strategy.

Provides tools to:
- Scan workspace files and sync tasks to TypeDB
- Link rules to their filesystem markdown documents
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_workspace_tools(mcp) -> None:
    """Register workspace-related MCP tools."""

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

            return json.dumps({
                "total_tasks": len(tasks),
                "sources": len(by_source),
                "by_source": by_source,
            }, indent=2)
        except Exception as e:
            logger.error(f"workspace_scan_tasks failed: {e}")
            return json.dumps({"error": str(e)})

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
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"workspace_capture_tasks failed: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def workspace_list_sources() -> str:
        """
        List workspace files that will be scanned for tasks.

        Returns:
            JSON array of source file paths
        """
        import os
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

        return json.dumps({
            "source_count": len(sources),
            "sources": sources,
        }, indent=2)

    # Rule-Document Linking Tools (P10.8)

    @mcp.tool()
    def workspace_scan_rule_documents() -> str:
        """
        Scan rule markdown documents and extract rule references (dry run).

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Scans docs/rules/*.md files and extracts RULE-XXX references.

        Returns:
            JSON summary of documents and their linked rules
        """
        try:
            from governance.rule_linker import scan_rule_documents

            documents = scan_rule_documents()

            result = []
            for doc in documents:
                result.append({
                    "document_id": doc.document_id,
                    "path": doc.path,
                    "rule_count": len(doc.rule_ids) if doc.rule_ids else 0,
                    "rule_ids": doc.rule_ids or [],
                })

            return json.dumps({
                "total_documents": len(documents),
                "documents": result,
            }, indent=2)
        except Exception as e:
            logger.error(f"workspace_scan_rule_documents failed: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def workspace_link_rules_to_documents() -> str:
        """
        Link rules to their filesystem markdown documents in TypeDB.

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Creates document entities and document-references-rule relations
        in TypeDB to link rules with their source markdown files.

        Returns:
            JSON with sync statistics (documents_inserted, relations_created, etc.)
        """
        try:
            from governance.rule_linker import link_rules_to_documents

            result = link_rules_to_documents()
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"workspace_link_rules_to_documents failed: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def workspace_get_document_for_rule(rule_id: str) -> str:
        """
        Get the markdown document path for a rule.

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Args:
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            JSON with document path or null if not found
        """
        try:
            from governance.rule_linker import get_document_for_rule

            path = get_document_for_rule(rule_id)
            return json.dumps({
                "rule_id": rule_id,
                "document_path": path,
            }, indent=2)
        except Exception as e:
            logger.error(f"workspace_get_document_for_rule failed: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def workspace_get_rules_for_document(document_id: str) -> str:
        """
        Get all rules documented in a specific markdown file.

        Per P10.8: TypeDB-Filesystem Rule Linking.

        Args:
            document_id: Document ID (e.g., "RULES-GOVERNANCE")

        Returns:
            JSON with list of rule IDs
        """
        try:
            from governance.rule_linker import get_rules_for_document

            rule_ids = get_rules_for_document(document_id)
            return json.dumps({
                "document_id": document_id,
                "rule_count": len(rule_ids),
                "rule_ids": rule_ids,
            }, indent=2)
        except Exception as e:
            logger.error(f"workspace_get_rules_for_document failed: {e}")
            return json.dumps({"error": str(e)})

    # Sync Status Tool (GAP-SYNC-002)

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
        import os
        import re

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
            try:
                from governance.client import TypeDBClient
                from governance.rule_linker import scan_rule_documents

                # Get rules from TypeDB
                client = TypeDBClient()
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
                result["rules"]["synced"] = len(missing_in_typedb) == 0 and len(missing_in_files) == 0

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

                result["tasks"]["status_mismatches"] = mismatches[:10]  # Limit output
                result["tasks"]["missing_in_typedb"] = missing_in_typedb[:10]
                result["tasks"]["synced"] = len(mismatches) == 0 and len(missing_in_typedb) == 0

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
                    evidence_files = [f for f in os.listdir(evidence_dir)
                                      if f.endswith(".md") and f.startswith("SESSION-")]
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

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"governance_sync_status failed: {e}")
            return json.dumps({"error": str(e)})

    logger.info("Registered workspace MCP tools (8 tools)")
