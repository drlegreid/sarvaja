"""
Evidence Backfill MCP Tools.

Per BACKFILL-OPS-01-v1: Backfill Operation Standards
Per UI-AUDIT-001: Task-session linkage backfill

Tools:
- backfill_scan_task_sessions: Scan evidence for task-session linkages (dry run)
- backfill_execute_task_sessions: Create task-session linkages in TypeDB

Created: 2026-01-20
"""

import logging

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


def register_evidence_backfill_tools(mcp) -> None:
    """Register evidence backfill MCP tools."""

    @mcp.tool()
    def backfill_scan_task_sessions() -> str:
        """
        Scan evidence files for task-session linkages (dry run).

        Per UI-AUDIT-001: Backfill task↔session linkages.
        Per BACKFILL-OPS-01-v1: Always scan before execute.

        Scans evidence/SESSION-*.md files for task ID references
        and proposes completed-in relations.

        Returns:
            JSON summary of proposed linkages by session
        """
        try:
            from governance.evidence_scanner import (
                scan_task_session_linkages,
                format_scan_summary,
            )

            result = scan_task_session_linkages()
            return format_mcp_result(format_scan_summary(result))

        # BUG-471-EBF-001: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"backfill_scan_task_sessions failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"backfill_scan_task_sessions failed: {type(e).__name__}"})

    @mcp.tool()
    def backfill_execute_task_sessions(dry_run: bool = True) -> str:
        """
        Create task-session linkages in TypeDB from evidence files.

        Per UI-AUDIT-001: Backfill task↔session linkages.
        Per BACKFILL-OPS-01-v1: Scan/execute pattern.

        Args:
            dry_run: If True (default), only show what would be done.
                     If False, actually create the relations.

        Returns:
            JSON with operation results (scanned, created, errors)
        """
        try:
            from governance.evidence_scanner import (
                apply_task_session_linkages,
                format_apply_summary,
            )

            result = apply_task_session_linkages(dry_run=dry_run)
            summary = format_apply_summary(result)
            summary["mode"] = "DRY_RUN" if dry_run else "EXECUTED"

            return format_mcp_result(summary)

        # BUG-471-EBF-002: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"backfill_execute_task_sessions failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"backfill_execute_task_sessions failed: {type(e).__name__}"})

    @mcp.tool()
    def backfill_scan_evidence_sessions() -> str:
        """
        Scan all evidence files and propose has-evidence links to sessions.

        Per A4: Evidence backfill for session→evidence linking.
        Scans evidence/*.md files across all patterns (SESSION, DSM, TEST-RUN, etc.)

        Returns:
            JSON summary of evidence files and proposed session links.
        """
        try:
            from governance.evidence_scanner import (
                scan_evidence_session_links,
                format_evidence_link_summary,
            )

            result = scan_evidence_session_links()
            return format_mcp_result(format_evidence_link_summary(result))

        # BUG-471-EBF-003: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"backfill_scan_evidence_sessions failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"backfill_scan_evidence_sessions failed: {type(e).__name__}"})

    @mcp.tool()
    def backfill_execute_evidence_sessions(dry_run: bool = True) -> str:
        """
        Create evidence-to-session links (has-evidence) in TypeDB.

        Per A4: Evidence backfill for session→evidence linking.
        Links evidence files to their corresponding session entities.

        Args:
            dry_run: If True (default), only show what would be done.
                     If False, actually create the relations.

        Returns:
            JSON with operation results (scanned, linked, errors).
        """
        try:
            from governance.evidence_scanner import (
                apply_evidence_session_links,
                format_evidence_link_summary,
            )

            result = apply_evidence_session_links(dry_run=dry_run)
            summary = format_evidence_link_summary(result)
            summary["mode"] = "DRY_RUN" if dry_run else "EXECUTED"

            return format_mcp_result(summary)

        # BUG-471-EBF-004: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"backfill_execute_evidence_sessions failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"backfill_execute_evidence_sessions failed: {type(e).__name__}"})

    @mcp.tool()
    def backfill_scan_all_evidence() -> str:
        """
        Comprehensive scan of all evidence files with entity references.

        Per A4: Full evidence audit across all patterns.
        Returns task, rule, and gap references found in each evidence file.

        Returns:
            JSON summary with per-file entity reference counts.
        """
        try:
            from governance.evidence_scanner import scan_all_evidence_files

            results = scan_all_evidence_files()

            summary = {
                "total_files": len(results),
                "files": [
                    {
                        "session_id": sr.session_id,
                        "file_path": sr.file_path,
                        "task_refs": len(sr.task_refs),
                        "rule_refs": len(sr.rule_refs),
                        "gap_refs": len(sr.gap_refs),
                        "tasks": sorted(sr.task_refs)[:5],
                        "rules": sorted(sr.rule_refs)[:5],
                        "gaps": sorted(sr.gap_refs)[:3],
                    }
                    for sr in results
                ],
                "totals": {
                    "task_refs": sum(len(sr.task_refs) for sr in results),
                    "rule_refs": sum(len(sr.rule_refs) for sr in results),
                    "gap_refs": sum(len(sr.gap_refs) for sr in results),
                },
            }

            return format_mcp_result(summary)

        # BUG-471-EBF-005: Sanitize logger message — exc_info=True already captures full stack
        except Exception as e:
            logger.error(f"backfill_scan_all_evidence failed: {type(e).__name__}", exc_info=True)
            return format_mcp_result({"error": f"backfill_scan_all_evidence failed: {type(e).__name__}"})

    logger.info("Registered evidence backfill tools (5 tools)")
