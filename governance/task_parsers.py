"""
Task Parsing Utilities.

Per GAP-FILE-026: Extracted from workspace_scanner.py
Per DOC-SIZE-01-v1: Files under 400 lines

Provides utilities for parsing markdown task tables.

Created: 2026-01-14
"""

import re
from typing import List, Dict, Optional


def normalize_status(status: str) -> str:
    """
    Normalize status symbols to TASK-LIFE-01-v1 compliant values.

    Per TASK-LIFE-01-v1: Valid statuses are OPEN, IN_PROGRESS, CLOSED.
    Per GAP-TASK-DATA-QUALITY-001: Map old values to compliant ones.
    """
    status = status.strip()
    # Map to TASK-LIFE-01-v1 compliant values: OPEN, IN_PROGRESS, CLOSED
    status_map = {
        # CLOSED mappings (completed work)
        "✅": "CLOSED",
        "✅ DONE": "CLOSED",
        "DONE": "CLOSED",
        "CLOSED": "CLOSED",
        "completed": "CLOSED",
        "COMPLETED": "CLOSED",
        # IN_PROGRESS mappings (active work)
        "🚧": "IN_PROGRESS",
        "IN PROGRESS": "IN_PROGRESS",
        "IN_PROGRESS": "IN_PROGRESS",
        "in_progress": "IN_PROGRESS",
        # OPEN mappings (not yet started)
        "⏳": "OPEN",
        "⏳ Pending": "OPEN",
        "PENDING": "OPEN",
        "pending": "OPEN",
        "📋": "OPEN",
        "📋 TODO": "OPEN",
        "TODO": "OPEN",
        "OPEN": "OPEN",
        # Hold/deferred → OPEN (per TASK-LIFE-01-v1, use resolution field for deferred)
        "⏸️": "OPEN",
        "⏸️ Hold": "OPEN",
        "⏸️ N/A": "OPEN",
        "ON HOLD": "OPEN",
        "ON_HOLD": "OPEN",
        "DEFERRED": "OPEN",
    }
    return status_map.get(status, "OPEN")


def parse_markdown_table(content: str) -> List[Dict[str, str]]:
    """Parse markdown table rows into list of dicts."""
    rows = []
    lines = content.split("\n")
    headers = []
    in_table = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            headers = []
            continue

        # Split cells
        cells = [c.strip() for c in line.split("|")[1:-1]]

        if not in_table:
            # First row is headers
            headers = [h.lower().replace(" ", "_").replace("#", "num") for h in cells]
            in_table = True
            continue

        # Skip separator row
        if all(c.replace("-", "").replace(":", "") == "" for c in cells):
            continue

        # Data row
        if len(cells) == len(headers):
            row = dict(zip(headers, cells))
            rows.append(row)

    return rows


def extract_task_id(row: Dict[str, str]) -> Optional[str]:
    """Extract task ID from row data."""
    # Try various column names
    for key in ["task", "id", "task_id", "num", "#"]:
        if key in row:
            val = row[key]
            # Check if it looks like a task ID
            if re.match(r'^[A-Z0-9\-\.]+$', val):
                return val
            # Extract from text like "P10.1" or "TODO-6"
            match = re.search(r'([A-Z]+[\-\.]?\d+[\.\d]*)', val)
            if match:
                return match.group(1)
    return None


def extract_gap_id(row: Dict[str, str]) -> Optional[str]:
    """Extract GAP ID from row data."""
    for key in ["gap", "gap_id", "evidence"]:
        if key in row:
            val = row[key]
            match = re.search(r'(GAP-[A-Z\-]+-\d+|GAP-\d+)', val)
            if match:
                return match.group(1)
    return None


def extract_linked_rules(row: Dict[str, str]) -> Optional[List[str]]:
    """Extract linked rule IDs from row data."""
    rules = []
    for key in ["rule", "rules", "linked_rules", "related_rules"]:
        if key in row:
            matches = re.findall(r'(RULE-\d+)', row[key])
            rules.extend(matches)
    return rules if rules else None


__all__ = [
    "normalize_status",
    "parse_markdown_table",
    "extract_task_id",
    "extract_gap_id",
    "extract_linked_rules",
]
