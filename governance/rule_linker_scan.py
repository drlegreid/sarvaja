"""
Rule Document Scanning
======================
Scan filesystem for rule documents and extract rule references.

Per P10.8: TypeDB-Filesystem Rule Linking.
Per GAP-MCP-008: Semantic ID support.
Per RULE-032: File size <300 lines.

Extracted from rule_linker.py per DOC-SIZE-01-v1.

Created: 2026-01-13 (extracted from rule_linker.py)
"""

import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from .rule_linker_ids import (
    LEGACY_RULE_PATTERN,
    SEMANTIC_RULE_PATTERN,
    SEMANTIC_TO_LEGACY,
)

logger = logging.getLogger(__name__)

# Workspace root (relative to this file)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

            # Skip hidden files and directories
            if item.startswith("."):
                continue

            # Recursively scan subdirectories
            if os.path.isdir(item_path) and include_subdirs:
                subdir_prefix = f"{rel_prefix}/{item}" if rel_prefix else item
                _scan_directory(item_path, subdir_prefix)
                continue

            # Only process markdown files
            if not item.endswith(".md"):
                continue

            # Read file content
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read {item_path}: {e}")
                continue

            # Generate document ID from filename
            base_name = os.path.splitext(item)[0]
            if rel_prefix:
                doc_id = f"DOC-{rel_prefix.upper().replace('/', '-')}-{base_name.upper()}"
            else:
                doc_id = f"DOC-{base_name.upper()}"

            # Clean up document ID (remove special chars except hyphens)
            doc_id = re.sub(r'[^A-Z0-9-]', '', doc_id)

            # Extract title from first heading or filename
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else base_name

            # Get file modification time
            stat = os.stat(item_path)
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            # Determine relative path from workspace root
            rel_path = os.path.relpath(item_path, WORKSPACE_ROOT)

            # Extract rule IDs
            rule_ids = extract_rule_ids(content)

            doc = RuleDocument(
                document_id=doc_id,
                title=title,
                path=rel_path,
                document_type="rule-document",
                storage="filesystem",
                last_modified=last_modified,
                rule_ids=rule_ids
            )
            documents.append(doc)

    # Start scanning from rules directory
    _scan_directory(rules_dir, "")

    logger.info(f"Scanned {len(documents)} rule documents")
    return documents
