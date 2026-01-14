"""
Rule-Document TypeDB Operations
===============================
TypeDB operations for rule-document linking.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per DECISION-003: TypeDB-First Strategy.
Per RULE-032: File size <300 lines.

Extracted from rule_linker.py per DOC-SIZE-01-v1.

Created: 2026-01-13 (extracted from rule_linker.py)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .rule_linker_ids import normalize_rule_id
from .rule_linker_scan import RuleDocument, scan_rule_documents

logger = logging.getLogger(__name__)


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


def _insert_document(client, doc: RuleDocument) -> tuple[bool, str]:
    """Insert document entity into TypeDB.

    Returns:
        Tuple of (success, error_message). error_message is empty on success.
    """
    # TypeDB datetime format: YYYY-MM-DDTHH:MM:SS (no microseconds)
    if doc.last_modified:
        last_mod = doc.last_modified.strftime('%Y-%m-%dT%H:%M:%S')
    else:
        last_mod = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # Escape special characters in string fields
    title_escaped = doc.title.replace('\\', '\\\\').replace('"', '\\"')
    path_escaped = doc.path.replace('\\', '\\\\').replace('"', '\\"')

    query = f"""
    insert
      $d isa document,
        has document-id "{doc.document_id}",
        has document-title "{title_escaped}",
        has document-path "{path_escaped}",
        has document-type "{doc.document_type}",
        has document-storage "{doc.storage}",
        has last-modified {last_mod};
    """
    try:
        client._execute_write(query)
        return True, ""
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.error(f"Insert document failed ({doc.document_id}): {error_msg}")
        return False, error_msg


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


def _create_document_rule_relation(client, document_id: str, rule_id: str) -> tuple[bool, str]:
    """Create document-references-rule relation in TypeDB.

    Returns:
        Tuple of (success, error_message). error_message is empty on success.
    """
    query = f"""
    match
      $d isa document, has document-id "{document_id}";
      $r isa rule-entity, has rule-id "{rule_id}";
    insert
      (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
    """
    try:
        client._execute_write(query)
        return True, ""
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.error(f"Create relation failed ({document_id} -> {rule_id}): {error_msg}")
        return False, error_msg


def link_rules_to_documents() -> Dict[str, Any]:
    """
    Link TypeDB rules to their filesystem markdown documents.

    Per P10.8: TypeDB-Filesystem Rule Linking.

    Returns:
        Dictionary with linking statistics
    """
    from governance.client import TypeDBClient

    stats = {
        "scanned_documents": 0,
        "documents_inserted": 0,
        "documents_skipped": 0,
        "relations_created": 0,
        "relations_skipped": 0,
        "errors": []
    }

    client = TypeDBClient()
    try:
        if not client.connect():
            stats["errors"].append("Failed to connect to TypeDB")
            return stats

        # Scan filesystem for rule documents
        documents = scan_rule_documents()
        stats["scanned_documents"] = len(documents)

        for doc in documents:
            # Check if document exists in TypeDB
            existing = _get_document(client, doc.document_id)

            if existing:
                stats["documents_skipped"] += 1
            else:
                # Insert new document
                success, error_msg = _insert_document(client, doc)
                if success:
                    stats["documents_inserted"] += 1
                else:
                    stats["errors"].append(f"Insert document {doc.document_id}: {error_msg}")

            # Create rule relations
            for rule_id in doc.rule_ids or []:
                if _check_document_rule_relation(client, doc.document_id, rule_id):
                    stats["relations_skipped"] += 1
                else:
                    success, error_msg = _create_document_rule_relation(client, doc.document_id, rule_id)
                    if success:
                        stats["relations_created"] += 1
                    else:
                        stats["errors"].append(f"Relation {doc.document_id} -> {rule_id}: {error_msg}")

        logger.info(f"Rule-document linking complete: {stats}")
        return stats
    finally:
        client.close()


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
