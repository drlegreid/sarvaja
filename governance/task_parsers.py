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
    """Normalize status symbols to standard values."""
    status = status.strip()
    status_map = {
        "✅": "DONE",
        "✅ DONE": "DONE",
        "DONE": "DONE",
        "🚧": "IN_PROGRESS",
        "IN PROGRESS": "IN_PROGRESS",
        "IN_PROGRESS": "IN_PROGRESS",
        "⏳": "PENDING",
        "⏳ Pending": "PENDING",
        "PENDING": "PENDING",
        "📋": "TODO",
        "📋 TODO": "TODO",
        "TODO": "TODO",
        "⏸️": "ON_HOLD",
        "⏸️ Hold": "ON_HOLD",
        "⏸️ N/A": "ON_HOLD",
        "ON HOLD": "ON_HOLD",
        "ON_HOLD": "ON_HOLD",
    }
    return status_map.get(status, "TODO")


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
