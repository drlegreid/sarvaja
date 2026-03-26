"""
TypeDB-Document Sync Verification Service.

Per EPIC-GOV-RULES-V3 P8: Compares 3 sources of rule truth:
  1. TypeDB rules (live database)
  2. Leaf markdown files (docs/rules/leaf/*.md)
  3. RULES-*.md index files (docs/rules/RULES-*.md)

Exposes SyncVerifier class (OOP/SRP) and verify_sync() convenience function.

Created: 2026-03-26
"""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from governance.services.rules import list_rules

logger = logging.getLogger(__name__)

# Semantic rule ID pattern: DOMAIN-SUB-NN-vN (e.g. SESSION-EVID-01-v1)
_SEMANTIC_PATTERN = re.compile(r"[A-Z][A-Z0-9]+-[A-Z][A-Z0-9]+-\d{2}-v\d+")

# Index table pattern: | **RULE-ID** | ... (bold in markdown tables)
_INDEX_RULE_PATTERN = re.compile(r"\|\s*\*\*(" + _SEMANTIC_PATTERN.pattern + r")\*\*\s*\|")

# Default workspace root (parent of governance/)
_DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class SyncReport:
    """Result of 3-source sync verification."""

    typedb_only: List[str] = field(default_factory=list)
    leaf_only: List[str] = field(default_factory=list)
    index_gaps: List[str] = field(default_factory=list)
    all_synced_count: int = 0
    typedb_count: int = 0
    leaf_count: int = 0
    index_count: int = 0
    error: Optional[str] = None

    @property
    def synced(self) -> bool:
        """True when all 3 sources are fully aligned."""
        return (
            not self.typedb_only
            and not self.leaf_only
            and not self.index_gaps
            and self.error is None
        )

    def to_dict(self) -> dict:
        return {
            "typedb_only": sorted(self.typedb_only),
            "leaf_only": sorted(self.leaf_only),
            "index_gaps": sorted(self.index_gaps),
            "all_synced_count": self.all_synced_count,
            "typedb_count": self.typedb_count,
            "leaf_count": self.leaf_count,
            "index_count": self.index_count,
            "synced": self.synced,
            "error": self.error,
        }


class SyncVerifier:
    """Compares TypeDB rules, leaf markdown, and RULES-*.md indexes.

    OOP/SRP: Each source has its own getter method.
    DRY: Leaf scanning reuses the glob pattern from rule_linker_scan.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._root = workspace_root or _DEFAULT_ROOT

    # ------------------------------------------------------------------
    # Source getters
    # ------------------------------------------------------------------

    def get_typedb_rules(self) -> set:
        """Fetch rule IDs from TypeDB via service layer."""
        result = list_rules(limit=500, source="sync-verify")
        items = result.get("items", [])
        # rule_to_response_dict uses "id" key (TypeDB rule ID)
        return {item["id"] for item in items if item.get("id")}

    def get_leaf_rules(self) -> set:
        """List rule IDs from docs/rules/leaf/*.md filenames."""
        leaf_dir = os.path.join(self._root, "docs", "rules", "leaf")
        if not os.path.isdir(leaf_dir):
            logger.warning("Leaf directory not found: %s", leaf_dir)
            return set()

        ids = set()
        for fname in os.listdir(leaf_dir):
            if fname.endswith(".md"):
                rule_id = fname[:-3]  # strip .md
                ids.add(rule_id)
        return ids

    def get_index_rules(self) -> set:
        """Parse RULES-*.md files for bold-table rule references."""
        rules_dir = os.path.join(self._root, "docs", "rules")
        if not os.path.isdir(rules_dir):
            return set()

        ids = set()
        for fname in os.listdir(rules_dir):
            if fname.startswith("RULES-") and fname.endswith(".md"):
                fpath = os.path.join(rules_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = _INDEX_RULE_PATTERN.findall(content)
                    ids.update(matches)
                except OSError:
                    logger.warning("Failed to read index file: %s", fpath)
        return ids

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self) -> SyncReport:
        """Run 3-source comparison and return SyncReport."""
        report = SyncReport()

        # Source 1: TypeDB
        try:
            typedb_ids = self.get_typedb_rules()
        except Exception as e:
            report.error = f"TypeDB: {e}"
            typedb_ids = set()

        # Source 2: Leaf files
        leaf_ids = self.get_leaf_rules()

        # Source 3: Index files
        index_ids = self.get_index_rules()

        report.typedb_count = len(typedb_ids)
        report.leaf_count = len(leaf_ids)
        report.index_count = len(index_ids)

        # Discrepancies
        report.typedb_only = sorted(typedb_ids - leaf_ids)
        report.leaf_only = sorted(leaf_ids - typedb_ids)

        # Index gaps: rules known (in TypeDB OR leaf) but not in any index
        known_rules = typedb_ids | leaf_ids
        report.index_gaps = sorted(known_rules - index_ids)

        # All synced: rules present in ALL 3 sources
        all_three = typedb_ids & leaf_ids & index_ids
        report.all_synced_count = len(all_three)

        return report


def verify_sync(workspace_root: Optional[str] = None) -> SyncReport:
    """Convenience function wrapping SyncVerifier."""
    return SyncVerifier(workspace_root=workspace_root).verify()
