"""
Evidence Scanner Package.

Per BACKFILL-OPS-01-v1: Backfill Operation Standards
Per DOC-SIZE-01-v1: Split from single 479-line file into submodules

Re-exports all public API for backward compatibility.
"""

from .extractors import (
    WORKSPACE_ROOT,
    EVIDENCE_DIR,
    EVIDENCE_PATTERNS,
    TASK_PATTERNS,
    RULE_PATTERNS,
    GAP_PATTERNS,
    LinkageProposal,
    ScanResult,
    BackfillResult,
    EvidenceLinkResult,
    extract_task_refs,
    extract_rule_refs,
    extract_gap_refs,
    extract_session_id,
)

from .backfill import (
    scan_evidence_files,
    get_existing_task_ids,
    scan_task_session_linkages,
    apply_task_session_linkages,
    format_scan_summary,
    format_apply_summary,
)

from .linking import (
    scan_all_evidence_files,
    scan_evidence_session_links,
    apply_evidence_session_links,
    format_evidence_link_summary,
)

__all__ = [
    # Models
    "LinkageProposal",
    "ScanResult",
    "BackfillResult",
    "EvidenceLinkResult",
    # Constants
    "WORKSPACE_ROOT",
    "EVIDENCE_DIR",
    "EVIDENCE_PATTERNS",
    "TASK_PATTERNS",
    "RULE_PATTERNS",
    "GAP_PATTERNS",
    # Extractors
    "extract_task_refs",
    "extract_rule_refs",
    "extract_gap_refs",
    "extract_session_id",
    # Scanning & Backfill
    "scan_evidence_files",
    "get_existing_task_ids",
    "scan_task_session_linkages",
    "apply_task_session_linkages",
    "format_scan_summary",
    "format_apply_summary",
    # Evidence Linking
    "scan_all_evidence_files",
    "scan_evidence_session_links",
    "apply_evidence_session_links",
    "format_evidence_link_summary",
]
