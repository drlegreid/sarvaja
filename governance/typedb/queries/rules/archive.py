"""
TypeDB Rule Archive Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

import os
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...entities import Rule

# Archive configuration
ARCHIVE_DIR = Path(os.getenv(
    "RULE_ARCHIVE_DIR",
    Path(__file__).parent.parent.parent.parent.parent / "evidence" / "archive" / "rules"
))


class RuleArchiveOperations:
    """
    Rule archive operations for TypeDB.

    Requires a client with get_rule_by_id, get_rule_dependencies, get_rules_depending_on,
    and create_rule methods.
    Uses mixin pattern for TypeDBClient composition.
    """

    def archive_rule(self, rule_id: str, reason: str = "archived") -> Optional[Dict[str, Any]]:
        """
        Archive a rule to JSON file for later retrieval.

        Args:
            rule_id: Rule ID to archive
            reason: Reason for archiving (deleted, deprecated, replaced, etc.)

        Returns:
            Archive record dict or None if rule not found
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return None

        # Ensure archive directory exists
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Create archive record
        archive_record = {
            "rule": asdict(rule),
            "archived_at": datetime.now().isoformat(),
            "reason": reason,
            "archived_from_db": self.database
        }

        # Get dependencies before archiving (for potential restore)
        try:
            deps = self.get_rule_dependencies(rule_id)
            archive_record["dependencies"] = deps
        except Exception:
            archive_record["dependencies"] = []

        try:
            dependents = self.get_rules_depending_on(rule_id)
            archive_record["dependents"] = dependents
        except Exception:
            archive_record["dependents"] = []

        # Save to archive file
        archive_file = ARCHIVE_DIR / f"{rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_record, f, indent=2, default=str)

        return archive_record

    def get_archived_rules(self) -> List[Dict[str, Any]]:
        """
        Get all archived rules.

        Returns:
            List of archive records
        """
        archives = []

        if not ARCHIVE_DIR.exists():
            return archives

        for archive_file in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    record["archive_file"] = str(archive_file)
                    archives.append(record)
            except Exception:
                continue

        return archives

    def get_archived_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent archive of a specific rule.

        Args:
            rule_id: Rule ID to find in archive

        Returns:
            Most recent archive record or None
        """
        archives = self.get_archived_rules()

        for record in archives:
            if record.get("rule", {}).get("id") == rule_id:
                return record

        return None

    def restore_rule(self, rule_id: str) -> Optional[Rule]:
        """
        Restore a rule from archive.

        Args:
            rule_id: Rule ID to restore

        Returns:
            Restored Rule object or None if not in archive
        """
        archive = self.get_archived_rule(rule_id)
        if not archive:
            return None

        rule_data = archive.get("rule", {})

        # Check if rule already exists (don't overwrite)
        existing = self.get_rule_by_id(rule_id)
        if existing:
            raise ValueError(f"Rule {rule_id} already exists. Delete or rename before restore.")

        # Recreate the rule
        return self.create_rule(
            rule_id=rule_data.get("id"),
            name=rule_data.get("name"),
            category=rule_data.get("category"),
            priority=rule_data.get("priority"),
            directive=rule_data.get("directive"),
            status="DRAFT"  # Restored rules start as DRAFT
        )
