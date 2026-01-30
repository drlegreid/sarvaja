"""
Evidence Scanner - Scanning and Backfill Operations.

Per BACKFILL-OPS-01-v1: Backfill Operation Standards
Per GAP-UI-AUDIT-001: Task-session linkage backfill
Per DOC-SIZE-01-v1: Extracted from evidence_scanner.py

Created: 2026-01-20
Updated: 2026-01-30 - Extracted per DOC-SIZE-01-v1
"""

import logging
from pathlib import Path
from typing import Dict, List, Set

from .extractors import (
    WORKSPACE_ROOT,
    EVIDENCE_DIR,
    BackfillResult,
    LinkageProposal,
    ScanResult,
    extract_task_refs,
    extract_rule_refs,
    extract_gap_refs,
    extract_session_id,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SCANNING
# =============================================================================

def scan_evidence_files(
    pattern: str = "SESSION-*.md",
    evidence_dir: str = EVIDENCE_DIR
) -> List[ScanResult]:
    """
    Scan evidence files and extract entity references.

    Args:
        pattern: Glob pattern for files to scan
        evidence_dir: Directory containing evidence files

    Returns:
        List of ScanResult objects
    """
    results = []
    evidence_path = Path(evidence_dir)

    if not evidence_path.exists():
        logger.warning(f"Evidence directory not found: {evidence_dir}")
        return results

    for filepath in sorted(evidence_path.glob(pattern)):
        try:
            content = filepath.read_text(encoding='utf-8')
            session_id = extract_session_id(filepath)

            result = ScanResult(
                session_id=session_id,
                file_path=str(filepath.relative_to(Path(WORKSPACE_ROOT))),
                task_refs=extract_task_refs(content),
                rule_refs=extract_rule_refs(content),
                gap_refs=extract_gap_refs(content),
            )
            results.append(result)

        except Exception as e:
            logger.error(f"Error scanning {filepath}: {e}")

    return results


def get_existing_task_ids() -> Set[str]:
    """Get all task IDs that exist in TypeDB."""
    try:
        from governance.mcp_tools.common import get_typedb_client

        client = get_typedb_client()
        if not client.connect():
            return set()

        try:
            tasks = client.get_all_tasks()
            return {t.id for t in tasks if hasattr(t, 'id') and t.id}
        finally:
            client.close()

    except Exception as e:
        logger.error(f"Failed to get existing tasks: {e}")
        return set()


# =============================================================================
# BACKFILL OPERATIONS
# =============================================================================

def scan_task_session_linkages() -> BackfillResult:
    """
    Scan evidence files for task-session linkages (dry run).

    Per UI-AUDIT-001: Backfill task-session linkages.

    Returns:
        BackfillResult with proposed linkages
    """
    result = BackfillResult()

    scan_results = scan_evidence_files()
    result.scanned = len(scan_results)

    existing_tasks = get_existing_task_ids()

    for sr in scan_results:
        for task_id in sr.task_refs:
            if task_id in existing_tasks:
                result.proposals.append(LinkageProposal(
                    source_id=task_id,
                    target_id=sr.session_id,
                    relation="completed-in",
                    evidence_file=sr.file_path,
                ))
                result.proposed += 1
            else:
                result.skipped += 1

    return result


def apply_task_session_linkages(dry_run: bool = True) -> BackfillResult:
    """
    Apply task-session linkages to TypeDB.

    Per UI-AUDIT-001: Backfill task-session linkages.
    Per BACKFILL-OPS-01-v1: Scan before execute pattern.

    Args:
        dry_run: If True, only scan; if False, create relations

    Returns:
        BackfillResult with operation statistics
    """
    result = scan_task_session_linkages()

    if dry_run:
        return result

    try:
        from governance.mcp_tools.common import get_typedb_client

        client = get_typedb_client()
        if not client.connect():
            result.errors.append("Failed to connect to TypeDB")
            return result

        try:
            for proposal in result.proposals:
                try:
                    success = client.link_task_to_session(
                        proposal.source_id,
                        proposal.target_id
                    )
                    if success:
                        result.created += 1
                    else:
                        result.errors.append(
                            f"Failed: {proposal.source_id} -> {proposal.target_id}"
                        )
                except Exception as e:
                    result.errors.append(
                        f"Error: {proposal.source_id} -> {proposal.target_id}: {e}"
                    )
        finally:
            client.close()

    except Exception as e:
        result.errors.append(f"Connection error: {e}")

    return result


# =============================================================================
# SUMMARY HELPERS
# =============================================================================

def format_scan_summary(result: BackfillResult) -> Dict:
    """Format scan result for MCP response."""
    by_session: Dict[str, List[str]] = {}
    for p in result.proposals:
        if p.target_id not in by_session:
            by_session[p.target_id] = []
        by_session[p.target_id].append(p.source_id)

    return {
        "scanned_files": result.scanned,
        "proposed_linkages": result.proposed,
        "skipped_not_in_typedb": result.skipped,
        "by_session": {
            session: {
                "task_count": len(tasks),
                "tasks": sorted(tasks)[:5],
                "more": len(tasks) - 5 if len(tasks) > 5 else 0,
            }
            for session, tasks in sorted(by_session.items())
        },
    }


def format_apply_summary(result: BackfillResult) -> Dict:
    """Format apply result for MCP response."""
    summary = format_scan_summary(result)
    summary.update({
        "created": result.created,
        "errors": result.errors[:5] if result.errors else [],
        "error_count": len(result.errors),
    })
    return summary
