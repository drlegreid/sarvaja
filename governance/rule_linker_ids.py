"""
Rule ID Mappings and Patterns
=============================
Semantic and legacy rule ID mappings for TypeDB compatibility.

Per META-TAXON-01-v1: Rule Taxonomy & Management.
Per GAP-MCP-008: Semantic ID support.
Per RULE-032: File size <300 lines.

Extracted from rule_linker.py per DOC-SIZE-01-v1.

Created: 2026-01-13 (extracted from rule_linker.py)
"""

import re
import logging

logger = logging.getLogger(__name__)

# Rule ID patterns (GAP-MCP-008)
# Legacy: RULE-001, RULE-042
LEGACY_RULE_PATTERN = r'RULE-\d{3}'
# Semantic: SESSION-EVID-01-v1, GOV-BICAM-01-v1, SESSION-DSP-NOTIFY-01-v1
# Pattern allows 2+ uppercase segments before the version number
SEMANTIC_RULE_PATTERN = r'[A-Z]+(?:-[A-Z]+)+-\d{2}-v\d+'

# Semantic ID to Legacy ID mapping (for TypeDB lookups)
# Generated from docs/rules/RULE-MIGRATION.md
SEMANTIC_TO_LEGACY = {
    "SESSION-EVID-01-v1": "RULE-001",
    "ARCH-EBMSF-01-v1": "RULE-002",
    "GOV-AUDIT-01-v1": "RULE-003",
    "SESSION-DSP-01-v1": "RULE-004",
    "RECOVER-MEM-01-v1": "RULE-005",
    "GOV-TRUST-01-v1": "RULE-006",
    "ARCH-MCP-01-v1": "RULE-007",
    "TEST-GUARD-01-v1": "RULE-008",
    "ARCH-VERSION-01-v1": "RULE-009",
    "GOV-RULE-01-v1": "RULE-010",
    "GOV-BICAM-01-v1": "RULE-011",
    "SESSION-DSM-01-v1": "RULE-012",
    "GOV-PROP-01-v1": "RULE-013",
    "WORKFLOW-AUTO-01-v1": "RULE-014",
    "WORKFLOW-RD-01-v1": "RULE-015",
    "ARCH-INFRA-01-v1": "RULE-016",
    "UI-TRAME-01-v1": "RULE-017",
    "GOV-TRUST-02-v1": "RULE-018",
    "GOV-PROP-02-v1": "RULE-019",
    "TEST-COMP-01-v1": "RULE-020",
    "SAFETY-HEALTH-01-v1": "RULE-021",
    "REPORT-EXEC-01-v1": "RULE-022",
    "TEST-E2E-01-v1": "RULE-023",
    "RECOVER-AMNES-01-v1": "RULE-024",
    "GOV-PROP-03-v1": "RULE-025",
    "GOV-RULE-02-v1": "RULE-026",
    "CONTAINER-RESTART-01-v1": "RULE-027",
    "WORKFLOW-SEQ-01-v1": "RULE-028",
    "GOV-RULE-03-v1": "RULE-029",
    "WORKFLOW-DEPLOY-01-v1": "RULE-030",
    "WORKFLOW-AUTO-02-v1": "RULE-031",
    "DOC-SIZE-01-v1": "RULE-032",
    "DOC-PARTIAL-01-v1": "RULE-033",
    "DOC-LINK-01-v1": "RULE-034",
    "CONTAINER-SHELL-01-v1": "RULE-035",
    "ARCH-MCP-02-v1": "RULE-036",
    "WORKFLOW-VALID-01-v1": "RULE-037",
    "RECOVER-ENTROPY-01-v1": "RULE-038",
    "TEST-FAIL-01-v1": "RULE-039",
    "ARCH-INFRA-02-v1": "RULE-040",
    "RECOVER-CRASH-01-v1": "RULE-041",
    "SAFETY-DESTR-01-v1": "RULE-042",
    "META-TAXON-01-v1": "RULE-043",
    "TEST-EXEC-01-v1": "RULE-044",
    "INTENT-CHECK-01-v1": "RULE-045",
    "REPORT-HUMOR-01-v1": "RULE-046",
    "GOV-MODE-01-v1": "RULE-047",
    "FEEDBACK-LOGIC-01-v1": "RULE-048",
    "REPORT-ISSUE-01-v1": "RULE-049",
    "SESSION-PROMPT-01-v1": "RULE-050",
    "MCP-RESTART-AUTO-01-v1": "RULE-051",
    "TEST-UI-VERIFY-01-v1": "RULE-052",
    "WORKFLOW-SHELL-01-v1": "RULE-053",
    "CONTAINER-MGMT-01-v1": "RULE-054",
    # Rules created with semantic ID only (no legacy mapping)
    "CONTAINER-TYPEDB-01-v1": "CONTAINER-TYPEDB-01-v1",
    "PKG-LATEST-01-v1": "PKG-LATEST-01-v1",
    "DOC-GAP-ARCHIVE-01-v1": "DOC-GAP-ARCHIVE-01-v1",
    "TASK-TECH-01-v1": "TASK-TECH-01-v1",
    "TASK-LIFE-01-v1": "TASK-LIFE-01-v1",
    "UI-LOADER-01-v1": "UI-LOADER-01-v1",
    "UI-TRACE-01-v1": "UI-TRACE-01-v1",
    "TEST-BDD-01-v1": "TEST-BDD-01-v1",
    "GAP-DOC-01-v1": "GAP-DOC-01-v1",
    "TASK-VALID-01-v1": "TASK-VALID-01-v1",
}

# Reverse mapping
LEGACY_TO_SEMANTIC = {v: k for k, v in SEMANTIC_TO_LEGACY.items()}

# Rule to document mapping (legacy, for fallback)
RULE_DOCUMENT_MAP = {
    "docs/rules/RULES-GOVERNANCE.md": ["RULE-001", "RULE-003", "RULE-006", "RULE-011", "RULE-013"],
    "docs/rules/RULES-TECHNICAL.md": ["RULE-002", "RULE-007", "RULE-008", "RULE-009", "RULE-010"],
    "docs/rules/RULES-OPERATIONAL.md": ["RULE-004", "RULE-005", "RULE-012", "RULE-014"],
}


def normalize_rule_id(rule_id: str) -> str:
    """
    Normalize rule ID to legacy format for TypeDB queries.

    Per GAP-MCP-008: Accepts both legacy and semantic IDs.

    Args:
        rule_id: Rule ID in either format (e.g., "RULE-001" or "SESSION-EVID-01-v1")

    Returns:
        Legacy format rule ID (RULE-XXX) for TypeDB compatibility
    """
    # Already in legacy format
    if re.match(LEGACY_RULE_PATTERN, rule_id):
        return rule_id

    # Semantic format - convert to legacy
    if rule_id in SEMANTIC_TO_LEGACY:
        return SEMANTIC_TO_LEGACY[rule_id]

    # Unknown format - return as-is and let TypeDB handle it
    logger.warning(f"Unknown rule ID format: {rule_id}")
    return rule_id
