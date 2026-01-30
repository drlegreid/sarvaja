"""
Evidence Scanner - Models, Patterns, and Extractors.

Per BACKFILL-OPS-01-v1: Backfill Operation Standards
Per GAP-FILE-021, DOC-SIZE-01-v1: Extracted from evidence_scanner.py

Created: 2026-01-20
Updated: 2026-01-30 - Extracted per DOC-SIZE-01-v1
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


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


@dataclass
class EvidenceLinkResult:
    """Result of evidence-to-session linking."""
    scanned: int = 0
    linked: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    details: List[Dict] = field(default_factory=list)


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
