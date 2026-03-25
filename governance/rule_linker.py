"""
Rule-Document Linker - Link TypeDB rules to filesystem markdown documents.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per DECISION-003: TypeDB-First Strategy.
Per META-TAXON-01-v1: Rule Taxonomy & Management.
Per GAP-MCP-008: Semantic ID support.
Per RULE-032: File size <300 lines (modularized).

Creates document entities in TypeDB and links them to rules via
document-references-rule relations.

Supports both:
- Legacy IDs: RULE-001, RULE-042
- Semantic IDs: SESSION-EVID-01-v1, GOV-BICAM-01-v1

Sub-modules:
- rule_linker_ids: ID mappings and patterns
- rule_linker_scan: Document scanning
- rule_linker_db: TypeDB operations

Created: 2024-12-28
Updated: 2026-01-13 - Modularized into sub-modules per DOC-SIZE-01-v1
"""

import logging

logger = logging.getLogger(__name__)

# Re-export from sub-modules for backwards compatibility
from .rule_linker_ids import (
    LEGACY_RULE_PATTERN,
    SEMANTIC_RULE_PATTERN,
    SEMANTIC_TO_LEGACY,
    SEMANTIC_ONLY_RULES,
    LEGACY_TO_SEMANTIC,
    RULE_DOCUMENT_MAP,
    normalize_rule_id,
)

from .rule_linker_scan import (
    WORKSPACE_ROOT,
    RuleDocument,
    extract_rule_ids,
    scan_rule_documents,
)

from .rule_linker_db import (
    link_rules_to_documents,
    get_rules_for_document,
    get_document_for_rule,
)

# All public exports
__all__ = [
    # ID patterns and mappings
    "LEGACY_RULE_PATTERN",
    "SEMANTIC_RULE_PATTERN",
    "SEMANTIC_TO_LEGACY",
    "SEMANTIC_ONLY_RULES",
    "LEGACY_TO_SEMANTIC",
    "RULE_DOCUMENT_MAP",
    "normalize_rule_id",
    # Scanning
    "WORKSPACE_ROOT",
    "RuleDocument",
    "extract_rule_ids",
    "scan_rule_documents",
    # TypeDB operations
    "link_rules_to_documents",
    "get_rules_for_document",
    "get_document_for_rule",
]

# CLI for testing
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    logger.info("Rule-Document Linker Test")

    # Test scanning
    documents = scan_rule_documents()
    logger.info(f"Scanned {len(documents)} rule documents:")

    for doc in documents:
        logger.info(f"  {doc.document_id}:")
        logger.info(f"    Path: {doc.path}")
        logger.info(f"    Rules: {', '.join(doc.rule_ids or [])}")

    # Test linking (if TypeDB available)
    logger.info("Linking to TypeDB")
    result = link_rules_to_documents()
    logger.info(json.dumps(result, indent=2))
