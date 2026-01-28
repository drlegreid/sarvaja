"""
Evidence Scanner Service.

Per BACKFILL-OPS-01-v1: Backfill Operation Standards
Per GAP-UI-AUDIT-001: Task-session linkage backfill

Provides reusable functions for scanning evidence files and extracting
entity references for backfill operations.

Created: 2026-01-20
"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

# Workspace root
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(WORKSPACE_ROOT, "evidence")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LinkageProposal:
    """Proposed linkage between entities."""
    source_id: str      # e.g., task_id
    target_id: str      # e.g., session_id
    relation: str       # e.g., "completed-in"
    evidence_file: str  # Source file where reference was found


@dataclass
class ScanResult:
    """Result of evidence file scan."""
    session_id: str
    file_path: str
    task_refs: Set[str] = field(default_factory=set)
    rule_refs: Set[str] = field(default_factory=set)
    gap_refs: Set[str] = field(default_factory=set)


@dataclass
class BackfillResult:
    """Result of backfill operation."""
    scanned: int = 0
    proposed: int = 0
    created: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    proposals: List[LinkageProposal] = field(default_factory=list)


# =============================================================================
# PATTERNS
# =============================================================================

# Task ID patterns found in evidence files
TASK_PATTERNS = [
    r'\b(FH-\d{3})\b',           # Frankel Hash: FH-001
    r'\b(KAN-\d{3})\b',          # Kanren: KAN-001
    r'\b(DOCVIEW-\d{3})\b',      # Document viewer: DOCVIEW-001
    r'\b(ATEST-\d{3})\b',        # Agent tests: ATEST-001
    r'\b(RD-\d{3})\b',           # R&D: RD-001
    r'\b(P\d+\.\d+[a-z]?)\b',    # Phase tasks: P4.1, P4.2b
    r'\b(FIX-\w+-\d{3})\b',      # Fix tasks: FIX-INFRA-001
    r'\b(UI-AUDIT-\d{3})\b',     # UI Audit tasks: UI-AUDIT-001
    r'\b(MULTI-\d{3})\b',        # Multi-agent tasks: MULTI-007
]

RULE_PATTERNS = [
    r'\b(RULE-\d{3})\b',                    # Legacy: RULE-001
    r'\b([A-Z]+-[A-Z]+-\d{2}-v\d)\b',       # Semantic: SESSION-EVID-01-v1
]

GAP_PATTERNS = [
    r'\b(GAP-[A-Z]+-\d{3})\b',              # Gap: GAP-UI-001
]


# =============================================================================
# EXTRACTORS
# =============================================================================

def extract_task_refs(content: str) -> Set[str]:
    """Extract task ID references from content."""
    refs = set()
    for pattern in TASK_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        refs.update(m.upper() if isinstance(m, str) else m[0].upper() for m in matches)
    return refs


def extract_rule_refs(content: str) -> Set[str]:
    """Extract rule ID references from content."""
    refs = set()
    for pattern in RULE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        refs.update(m.upper() if isinstance(m, str) else m[0].upper() for m in matches)
    return refs


def extract_gap_refs(content: str) -> Set[str]:
    """Extract gap ID references from content."""
    refs = set()
    for pattern in GAP_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        refs.update(m.upper() if isinstance(m, str) else m[0].upper() for m in matches)
    return refs


def extract_session_id(filepath: Path) -> str:
    """Extract session ID from filename."""
    return filepath.stem


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

    Per UI-AUDIT-001: Backfill task↔session linkages.

    Returns:
        BackfillResult with proposed linkages
    """
    result = BackfillResult()

    # Scan evidence files
    scan_results = scan_evidence_files()
    result.scanned = len(scan_results)

    # Get existing tasks for validation
    existing_tasks = get_existing_task_ids()

    for sr in scan_results:
        for task_id in sr.task_refs:
            # Only propose linkages for tasks that exist
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

    Per UI-AUDIT-001: Backfill task↔session linkages.
    Per BACKFILL-OPS-01-v1: Scan before execute pattern.

    Args:
        dry_run: If True, only scan; if False, create relations

    Returns:
        BackfillResult with operation statistics
    """
    # Always scan first
    result = scan_task_session_linkages()

    if dry_run:
        return result

    # Execute linkages
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
                            f"Failed: {proposal.source_id} → {proposal.target_id}"
                        )
                except Exception as e:
                    result.errors.append(
                        f"Error: {proposal.source_id} → {proposal.target_id}: {e}"
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
    # Group proposals by session
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
                "tasks": sorted(tasks)[:5],  # Show first 5
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


# =============================================================================
# EVIDENCE-TO-SESSION LINKING (A4)
# =============================================================================

# All evidence file patterns with their entity type
EVIDENCE_PATTERNS = {
    "SESSION-*.md": "session",
    "DSM-*.md": "dsm",
    "TEST-RUN-*.md": "test-run",
    "DECISION-*.md": "decision",
    "QUALITY-*.md": "quality",
    "EPIC-*.md": "epic",
    "HANDOFF-*.md": "handoff",
}


@dataclass
class EvidenceLinkResult:
    """Result of evidence-to-session linking."""
    scanned: int = 0
    linked: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    details: List[Dict] = field(default_factory=list)


def _extract_session_id_from_evidence(filepath: Path) -> str:
    """Extract a session ID from evidence filename.

    Maps evidence files to session IDs:
    - SESSION-2026-01-28-TOPIC.md → SESSION-2026-01-28-TOPIC
    - DSM-2026-01-25-015206.md → DSM-2026-01-25-015206
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
                logger.error(f"Error scanning {filepath}: {e}")

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
        evidence_path = sr.file_path
        session_id = sr.session_id

        result.details.append({
            "evidence_path": evidence_path,
            "session_id": session_id,
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
