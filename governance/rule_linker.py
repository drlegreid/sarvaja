"""
Rule-Document Linker - Link TypeDB rules to filesystem markdown documents.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per DECISION-003: TypeDB-First Strategy.
Per RULE-013: Rules Applicability Convention.

Creates document entities in TypeDB and links them to rules via
document-references-rule relations.

Sources (from CLAUDE.md Cross-Reference Index):
- RULE-001,003,006,011,013 → docs/rules/RULES-GOVERNANCE.md
- RULE-002,007,008,009,010 → docs/rules/RULES-TECHNICAL.md
- RULE-004,005,012,014     → docs/rules/RULES-OPERATIONAL.md

Created: 2024-12-28
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

# Rule to document mapping (from CLAUDE.md)
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


def scan_rule_documents() -> List[RuleDocument]:
    """
    Scan rules/ directory for markdown files and extract rule references.

    Returns list of RuleDocument with linked rule IDs.
    """
    documents = []
    rules_dir = os.path.join(WORKSPACE_ROOT, "docs", "rules")

    if not os.path.exists(rules_dir):
        logger.warning(f"Rules directory not found: {rules_dir}")
        return documents

    for filename in os.listdir(rules_dir):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(rules_dir, filename)
        rel_path = f"docs/rules/{filename}"

        # Get last modified time
        try:
            mtime = os.path.getmtime(filepath)
            last_modified = datetime.fromtimestamp(mtime)
        except Exception:
            last_modified = None

        # Extract rule IDs from content
        rule_ids = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Find all RULE-XXX patterns
            rule_ids = list(set(re.findall(r'RULE-\d+', content)))
            rule_ids.sort(key=lambda x: int(x.split("-")[1]))
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            # Use static mapping as fallback
            rule_ids = RULE_DOCUMENT_MAP.get(rel_path, [])

        # Generate document ID from filename
        doc_id = filename.replace(".md", "").upper()
        title = filename.replace(".md", "").replace("-", " ").title()

        documents.append(RuleDocument(
            document_id=doc_id,
            title=title,
            path=rel_path,
            document_type="markdown",
            storage="local",
            last_modified=last_modified,
            rule_ids=rule_ids
        ))

        logger.info(f"Scanned {filename}: {len(rule_ids)} rules linked")

    return documents


def link_rules_to_documents() -> Dict[str, Any]:
    """
    Sync rule documents to TypeDB and create document-references-rule relations.

    Returns dict with sync statistics.
    """
    from governance.client import get_client

    stats = {
        "documents_inserted": 0,
        "documents_existing": 0,
        "relations_created": 0,
        "relations_existing": 0,
        "errors": 0,
    }

    documents = scan_rule_documents()

    try:
        client = get_client()
        if not client or not client.is_connected():
            logger.error("TypeDB client not available")
            return stats
    except Exception as e:
        logger.error(f"Failed to connect to TypeDB: {e}")
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
        document_id: Document ID (e.g., "RULES-GOVERNANCE")

    Returns:
        List of rule IDs
    """
    from governance.client import get_client

    try:
        client = get_client()
        if not client or not client.is_connected():
            return []
    except Exception:
        return []

    query = f"""
    match
      $d isa document, has document-id "{document_id}";
      $r isa rule-entity, has rule-id $rid;
      (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
    get $rid;
    """

    try:
        results = client.execute_query(query)
        return [r.get("rid", {}).get("value", "") for r in results if r.get("rid")]
    except Exception:
        return []


def get_document_for_rule(rule_id: str) -> Optional[str]:
    """
    Query TypeDB for the document that contains a rule.

    Args:
        rule_id: Rule ID (e.g., "RULE-001")

    Returns:
        Document path or None
    """
    from governance.client import get_client

    try:
        client = get_client()
        if not client or not client.is_connected():
            return None
    except Exception:
        return None

    query = f"""
    match
      $r isa rule-entity, has rule-id "{rule_id}";
      $d isa document, has document-path $path;
      (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
    get $path;
    """

    try:
        results = client.execute_query(query)
        if results:
            return results[0].get("path", {}).get("value")
        return None
    except Exception:
        return None


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
