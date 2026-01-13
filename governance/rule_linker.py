"""
Rule-Document Linker - Link TypeDB rules to filesystem markdown documents.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per DECISION-003: TypeDB-First Strategy.
Per META-TAXON-01-v1: Rule Taxonomy & Management.
Per GAP-MCP-008: Semantic ID support.

Creates document entities in TypeDB and links them to rules via
document-references-rule relations.

Supports both:
- Legacy IDs: RULE-001, RULE-042
- Semantic IDs: SESSION-EVID-01-v1, GOV-BICAM-01-v1

Created: 2024-12-28
Updated: 2026-01-13 - Added semantic ID pattern support
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Workspace root (relative to this file)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rule ID patterns (GAP-MCP-008)
# Legacy: RULE-001, RULE-042
LEGACY_RULE_PATTERN = r'RULE-\d{3}'
# Semantic: SESSION-EVID-01-v1, GOV-BICAM-01-v1, META-TAXON-01-v1
SEMANTIC_RULE_PATTERN = r'[A-Z]+-[A-Z]+-\d{2}-v\d+'

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
    "META-TAXON-01-v1": "RULE-043",  # New META rule
    "TEST-EXEC-01-v1": "RULE-044",  # Split test execution
}

# Reverse mapping
LEGACY_TO_SEMANTIC = {v: k for k, v in SEMANTIC_TO_LEGACY.items()}

# Rule to document mapping (legacy, for fallback)
RULE_DOCUMENT_MAP = {
    "docs/rules/RULES-GOVERNANCE.md": ["RULE-001", "RULE-003", "RULE-006", "RULE-011", "RULE-013"],
    "docs/rules/RULES-TECHNICAL.md": ["RULE-002", "RULE-007", "RULE-008", "RULE-009", "RULE-010"],
    "docs/rules/RULES-OPERATIONAL.md": ["RULE-004", "RULE-005", "RULE-012", "RULE-014"],
}


@dataclass
class RuleDocument:
    """Parsed rule document from filesystem."""
    document_id: str
    title: str
    path: str
    document_type: str
    storage: str
    last_modified: Optional[datetime] = None
    rule_ids: Optional[List[str]] = None


def extract_rule_ids(content: str) -> List[str]:
    """
    Extract rule IDs from content using both legacy and semantic patterns.

    Per GAP-MCP-008: Support both RULE-XXX and DOMAIN-SUB-NN-vN formats.

    Args:
        content: Markdown file content

    Returns:
        List of unique legacy rule IDs (RULE-XXX format for TypeDB compatibility)
    """
    rule_ids = set()

    # Find legacy pattern: RULE-001, RULE-042
    legacy_matches = re.findall(LEGACY_RULE_PATTERN, content)
    rule_ids.update(legacy_matches)

    # Find semantic pattern: SESSION-EVID-01-v1, GOV-BICAM-01-v1
    semantic_matches = re.findall(SEMANTIC_RULE_PATTERN, content)
    for semantic_id in semantic_matches:
        # Convert to legacy ID for TypeDB lookup
        if semantic_id in SEMANTIC_TO_LEGACY:
            rule_ids.add(SEMANTIC_TO_LEGACY[semantic_id])
        else:
            # Unknown semantic ID - log warning but don't add
            logger.debug(f"Unknown semantic ID: {semantic_id}")

    # Sort by rule number
    sorted_ids = sorted(
        rule_ids,
        key=lambda x: int(x.split("-")[1]) if x.startswith("RULE-") else 999
    )
    return sorted_ids


def scan_rule_documents(include_subdirs: bool = True) -> List[RuleDocument]:
    """
    Scan rules/ directory for markdown files and extract rule references.

    Per GAP-MCP-008: Supports both legacy (RULE-XXX) and semantic
    (DOMAIN-SUB-NN-vN) ID patterns.

    Args:
        include_subdirs: If True, scan subdirectories (leaf/, governance/, etc.)

    Returns:
        List of RuleDocument with linked rule IDs.
    """
    documents = []
    rules_dir = os.path.join(WORKSPACE_ROOT, "docs", "rules")

    if not os.path.exists(rules_dir):
        logger.warning(f"Rules directory not found: {rules_dir}")
        return documents

    def _scan_directory(dir_path: str, rel_prefix: str) -> None:
        """Recursively scan a directory for markdown files."""
        if not os.path.exists(dir_path):
            return

        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)

            # Recurse into subdirectories
            if os.path.isdir(item_path) and include_subdirs:
                _scan_directory(item_path, f"{rel_prefix}/{item}")
                continue

            # Skip non-markdown files
            if not item.endswith(".md"):
                continue

            rel_path = f"{rel_prefix}/{item}"

            # Get last modified time
            try:
                mtime = os.path.getmtime(item_path)
                last_modified = datetime.fromtimestamp(mtime)
            except Exception:
                last_modified = None

            # Extract rule IDs from content
            rule_ids = []
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Use new extract_rule_ids that handles both patterns
                rule_ids = extract_rule_ids(content)
            except Exception as e:
                logger.warning(f"Failed to read {item_path}: {e}")
                # Use static mapping as fallback
                rule_ids = RULE_DOCUMENT_MAP.get(rel_path, [])

            # Generate document ID from path
            # e.g., docs/rules/leaf/SESSION-EVID-01-v1.md -> LEAF-SESSION-EVID-01-V1
            # e.g., docs/rules/RULES-GOVERNANCE.md -> RULES-GOVERNANCE
            if "/" in rel_prefix.replace("docs/rules", ""):
                subdir = rel_prefix.split("/")[-1].upper()
                doc_id = f"{subdir}-{item.replace('.md', '').upper()}"
            else:
                doc_id = item.replace(".md", "").upper()

            title = item.replace(".md", "").replace("-", " ").title()

            documents.append(RuleDocument(
                document_id=doc_id,
                title=title,
                path=rel_path,
                document_type="markdown",
                storage="local",
                last_modified=last_modified,
                rule_ids=rule_ids
            ))

            logger.debug(f"Scanned {rel_path}: {len(rule_ids)} rules linked")

    # Start scan from rules directory
    _scan_directory(rules_dir, "docs/rules")

    logger.info(f"Scanned {len(documents)} rule documents total")
    return documents


def link_rules_to_documents() -> Dict[str, Any]:
    """
    Sync rule documents to TypeDB and create document-references-rule relations.

    Returns dict with sync statistics.
    """
    from governance.client import TypeDBClient

    stats = {
        "documents_inserted": 0,
        "documents_existing": 0,
        "relations_created": 0,
        "relations_existing": 0,
        "errors": 0,
    }

    documents = scan_rule_documents()

    client = TypeDBClient()
    try:
        if not client.connect():
            logger.error("Failed to connect to TypeDB for link_rules_to_documents")
            return stats

        for doc in documents:
            try:
                # Check if document exists
                existing = _get_document(client, doc.document_id)

                if existing:
                    stats["documents_existing"] += 1
                else:
                    # Insert new document
                    _insert_document(client, doc)
                    stats["documents_inserted"] += 1
                    logger.debug(f"Inserted document {doc.document_id}")

                # Create document-references-rule relations
                if doc.rule_ids:
                    for rule_id in doc.rule_ids:
                        try:
                            relation_exists = _check_document_rule_relation(
                                client, doc.document_id, rule_id
                            )
                            if relation_exists:
                                stats["relations_existing"] += 1
                            else:
                                _create_document_rule_relation(
                                    client, doc.document_id, rule_id
                                )
                                stats["relations_created"] += 1
                                logger.debug(f"Linked {doc.document_id} → {rule_id}")
                        except Exception as e:
                            logger.warning(f"Failed to link {doc.document_id} → {rule_id}: {e}")
                            stats["errors"] += 1

            except Exception as e:
                logger.warning(f"Failed to sync document {doc.document_id}: {e}")
                stats["errors"] += 1

        logger.info(f"Rule-document linking complete: {stats}")
        return stats
    finally:
        client.close()


def _get_document(client, document_id: str) -> Optional[Dict]:
    """Check if document exists in TypeDB."""
    query = f"""
    match
      $d isa document, has document-id "{document_id}";
    get $d;
    """
    try:
        results = client.execute_query(query)
        return results[0] if results else None
    except Exception:
        return None


def _insert_document(client, doc: RuleDocument) -> bool:
    """Insert document entity into TypeDB."""
    last_mod = doc.last_modified.isoformat() if doc.last_modified else datetime.now().isoformat()

    query = f"""
    insert
      $d isa document,
        has document-id "{doc.document_id}",
        has document-title "{doc.title}",
        has document-path "{doc.path}",
        has document-type "{doc.document_type}",
        has document-storage "{doc.storage}",
        has last-modified {last_mod};
    """
    try:
        client.execute_write_query(query)
        return True
    except Exception as e:
        logger.error(f"Insert document failed: {e}")
        return False


def _check_document_rule_relation(client, document_id: str, rule_id: str) -> bool:
    """Check if document-references-rule relation exists."""
    query = f"""
    match
      $d isa document, has document-id "{document_id}";
      $r isa rule-entity, has rule-id "{rule_id}";
      (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
    get;
    """
    try:
        results = client.execute_query(query)
        return len(results) > 0
    except Exception:
        return False


def _create_document_rule_relation(client, document_id: str, rule_id: str) -> bool:
    """Create document-references-rule relation in TypeDB."""
    query = f"""
    match
      $d isa document, has document-id "{document_id}";
      $r isa rule-entity, has rule-id "{rule_id}";
    insert
      (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
    """
    try:
        client.execute_write_query(query)
        return True
    except Exception as e:
        logger.error(f"Create relation failed: {e}")
        return False


def get_rules_for_document(document_id: str) -> List[str]:
    """
    Query TypeDB for all rules referenced by a document.

    Args:
        document_id: Document ID (e.g., "DOC-RULES-GOVERNANCE")

    Returns:
        List of rule IDs
    """
    from governance.client import TypeDBClient

    client = TypeDBClient()
    try:
        if not client.connect():
            logger.warning("Failed to connect to TypeDB for get_rules_for_document")
            return []

        query = f"""
        match
          $d isa document, has document-id "{document_id}";
          $r isa rule-entity, has rule-id $rid;
          (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
        get $rid;
        """

        results = client.execute_query(query)
        return [r.get("rid") for r in results if r.get("rid")]
    except Exception as e:
        logger.warning(f"get_rules_for_document failed: {e}")
        return []
    finally:
        client.close()


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


def get_document_for_rule(rule_id: str) -> Optional[str]:
    """
    Query TypeDB for the document that contains a rule.

    Per GAP-MCP-008: Accepts both legacy (RULE-XXX) and semantic
    (DOMAIN-SUB-NN-vN) ID formats.

    Args:
        rule_id: Rule ID (e.g., "RULE-001" or "SESSION-EVID-01-v1")

    Returns:
        Document path or None
    """
    from governance.client import TypeDBClient

    # Normalize to legacy ID for TypeDB query
    legacy_id = normalize_rule_id(rule_id)

    client = TypeDBClient()
    try:
        if not client.connect():
            logger.warning("Failed to connect to TypeDB for get_document_for_rule")
            return None

        query = f"""
        match
          $r isa rule-entity, has rule-id "{legacy_id}";
          $d isa document, has document-path $path;
          (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
        get $path;
        """

        results = client.execute_query(query)
        if results:
            return results[0].get("path")
        return None
    except Exception as e:
        logger.warning(f"get_document_for_rule failed: {e}")
        return None
    finally:
        client.close()


# CLI for testing
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Rule-Document Linker Test")
    print("=" * 60)

    # Test scanning
    documents = scan_rule_documents()
    print(f"\nScanned {len(documents)} rule documents:")

    for doc in documents:
        print(f"\n  {doc.document_id}:")
        print(f"    Path: {doc.path}")
        print(f"    Rules: {', '.join(doc.rule_ids or [])}")

    # Test linking (if TypeDB available)
    print("\n--- Linking to TypeDB ---")
    result = link_rules_to_documents()
    print(json.dumps(result, indent=2))
