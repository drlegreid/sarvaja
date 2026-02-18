"""
Evidence Scanner - Evidence-to-Session Linking.

Per GAP-UI-AUDIT-001: Evidence file linkage
Per DOC-SIZE-01-v1: Extracted from evidence_scanner.py

Created: 2026-01-20
Updated: 2026-01-30 - Extracted per DOC-SIZE-01-v1
"""

import logging
from pathlib import Path
from typing import Dict, List

from .extractors import (
    WORKSPACE_ROOT,
    EVIDENCE_DIR,
    EVIDENCE_PATTERNS,
    EvidenceLinkResult,
    ScanResult,
    extract_task_refs,
    extract_rule_refs,
    extract_gap_refs,
)

logger = logging.getLogger(__name__)


def _extract_session_id_from_evidence(filepath: Path) -> str:
    """Extract a session ID from evidence filename.

    Maps evidence files to session IDs:
    - SESSION-2026-01-28-TOPIC.md -> SESSION-2026-01-28-TOPIC
    - DSM-2026-01-25-015206.md -> DSM-2026-01-25-015206
    """
    return filepath.stem


def scan_all_evidence_files(evidence_dir: str = EVIDENCE_DIR) -> List[ScanResult]:
    """Scan all evidence files across all patterns.

    Returns:
        List of ScanResult objects for every evidence file found.
    """
    results = []
    evidence_path = Path(evidence_dir)

    if not evidence_path.exists():
        return results

    seen = set()
    for pattern in EVIDENCE_PATTERNS:
        for filepath in sorted(evidence_path.glob(pattern)):
            if filepath.name in seen:
                continue
            seen.add(filepath.name)

            try:
                content = filepath.read_text(encoding='utf-8')
                result = ScanResult(
                    session_id=_extract_session_id_from_evidence(filepath),
                    file_path=str(filepath.relative_to(Path(WORKSPACE_ROOT))),
                    task_refs=extract_task_refs(content),
                    rule_refs=extract_rule_refs(content),
                    gap_refs=extract_gap_refs(content),
                )
                results.append(result)
            except Exception as e:
                # BUG-474-ELK-1: Sanitize logger message + add exc_info for stack trace preservation
                logger.error(f"Error scanning {filepath}: {type(e).__name__}", exc_info=True)

    return results


def scan_evidence_session_links(evidence_dir: str = EVIDENCE_DIR) -> EvidenceLinkResult:
    """Scan evidence files and propose has-evidence links to sessions.

    For each evidence file, finds matching session entity in TypeDB
    and proposes a has-evidence relation.

    Returns:
        EvidenceLinkResult with proposed links.
    """
    result = EvidenceLinkResult()
    all_evidence = scan_all_evidence_files(evidence_dir)
    result.scanned = len(all_evidence)

    for sr in all_evidence:
        result.details.append({
            "evidence_path": sr.file_path,
            "session_id": sr.session_id,
            "task_refs": len(sr.task_refs),
            "rule_refs": len(sr.rule_refs),
            "gap_refs": len(sr.gap_refs),
        })

    return result


def apply_evidence_session_links(dry_run: bool = True) -> EvidenceLinkResult:
    """Link evidence files to their session entities in TypeDB.

    Creates has-evidence relations between work-session entities
    and evidence entities.

    Args:
        dry_run: If True, only scan; if False, create relations.

    Returns:
        EvidenceLinkResult with operation statistics.
    """
    result = scan_evidence_session_links()

    if dry_run:
        return result

    try:
        from governance.mcp_tools.common import get_typedb_client

        client = get_typedb_client()
        if not client.connect():
            result.errors.append("Failed to connect to TypeDB")
            return result

        try:
            for detail in result.details:
                try:
                    success = client.link_evidence_to_session(
                        detail["session_id"],
                        detail["evidence_path"]
                    )
                    if success:
                        result.linked += 1
                    else:
                        result.skipped += 1
                except Exception as e:
                    result.errors.append(
                        f"Error linking {detail['evidence_path']}: {e}"
                    )
        finally:
            client.close()

    except Exception as e:
        result.errors.append(f"Connection error: {e}")

    return result


def format_evidence_link_summary(result: EvidenceLinkResult) -> Dict:
    """Format evidence link result for MCP response."""
    return {
        "scanned_files": result.scanned,
        "linked": result.linked,
        "skipped": result.skipped,
        "errors": result.errors[:5] if result.errors else [],
        "error_count": len(result.errors),
        "evidence_files": result.details[:10],
        "more": max(0, len(result.details) - 10),
    }
