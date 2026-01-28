# governance/utils/gap_parser.py
"""
Gap Parser Utility - Parses GAP-INDEX.md for backlog synchronization.

Per TASK 1.3: Ensures real backlog (GAP-INDEX.md) syncs with Claude tasks.
Prevents the anti-pattern of creating self-referential todo lists that
ignore the actual project backlog.

Usage:
    from governance.utils import get_prioritized_gaps
    gaps = get_prioritized_gaps(limit=20)
    for gap in gaps:
        print(f"[{gap.priority}] {gap.id}: {gap.description}")
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict
from enum import IntEnum

# Priority ordering (lower number = higher priority)
class Priority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    UNKNOWN = 5


@dataclass
class Gap:
    """Represents a single gap entry from GAP-INDEX.md."""
    id: str
    description: str
    priority: str
    category: str
    evidence: str = ""
    is_resolved: bool = False

    @property
    def priority_order(self) -> int:
        """Get numeric priority for sorting."""
        priority_upper = self.priority.upper().strip("*")
        try:
            return Priority[priority_upper].value
        except KeyError:
            return Priority.UNKNOWN.value

    def to_todo_format(self) -> str:
        """Format gap as todo item."""
        return f"[{self.priority.upper()}] {self.id}: {self.description}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "evidence": self.evidence,
            "is_resolved": self.is_resolved,
            "priority_order": self.priority_order
        }

    def to_work_item(self) -> "WorkItem":
        """Convert to unified WorkItem abstraction."""
        from governance.utils.work_item import WorkItem
        return WorkItem.from_gap(self)


class GapParser:
    """Parser for GAP-INDEX.md file."""

    # Simple pattern to find GAP-XXX in any format
    GAP_ID_PATTERN = re.compile(r'(~~)?(GAP-[\w-]+)(~~)?')

    # Known priority values
    PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

    def __init__(self, gap_index_path: Optional[Path] = None):
        """Initialize parser with path to GAP-INDEX.md."""
        if gap_index_path is None:
            # Default to project root
            self.gap_index_path = Path(__file__).parent.parent.parent / "docs" / "gaps" / "GAP-INDEX.md"
        else:
            self.gap_index_path = Path(gap_index_path)

    def parse(self) -> List[Gap]:
        """Parse GAP-INDEX.md and return all gaps."""
        if not self.gap_index_path.exists():
            raise FileNotFoundError(f"GAP-INDEX.md not found at {self.gap_index_path}")

        gaps = []
        content = self.gap_index_path.read_text(encoding="utf-8")

        # Track which section we're in to exclude "Recently Resolved"
        in_resolved_section = False

        for line in content.split("\n"):
            # Detect section headers (## headings)
            if line.startswith("## "):
                section_title = line[3:].strip().lower()
                # Check if entering/leaving resolved section
                in_resolved_section = "resolved" in section_title
                continue

            # Skip parsing gaps in the "Recently Resolved" section
            if in_resolved_section:
                continue

            gap = self._parse_line(line)
            if gap:
                gaps.append(gap)

        return gaps

    def _parse_line(self, line: str) -> Optional[Gap]:
        """Parse a single line and return Gap if it matches pattern."""
        # Skip non-table lines
        if not line.strip().startswith("|"):
            return None

        # Skip if no GAP- pattern
        if "GAP-" not in line:
            return None

        # Skip table headers
        if "| ID |" in line or "|----" in line:
            return None

        # Check for strikethrough (resolved) marker
        is_resolved = "~~GAP-" in line or "RESOLVED" in line.upper()

        # Find GAP ID
        match = self.GAP_ID_PATTERN.search(line)
        if not match:
            return None

        gap_id = match.group(2)  # GAP-XXX without ~~
        has_strikethrough = bool(match.group(1) or match.group(3))
        if has_strikethrough:
            is_resolved = True

        # Split by | and clean up
        columns = [c.strip().strip("~").strip("*").strip() for c in line.split("|")]
        columns = [c for c in columns if c]  # Remove empty strings

        if len(columns) < 2:
            return None

        # Find description (usually column after ID)
        description = ""
        priority = "MEDIUM"  # Default priority
        category = ""
        evidence = ""

        # Try to find columns by position and content
        for i, col in enumerate(columns):
            col_upper = col.upper()

            # Skip the ID column
            if col_upper.startswith("GAP-"):
                continue

            # Check if this is a priority column
            if col_upper in self.PRIORITIES:
                priority = col_upper
                continue

            # Check for priority with ** markers
            clean_col = col_upper.strip("*").strip()
            if clean_col in self.PRIORITIES:
                priority = clean_col
                continue

            # First non-ID, non-priority column is likely description
            if not description and len(col) > 5:
                description = col

            # Check for category keywords
            if any(cat in col_upper for cat in ["FUNCTIONALITY", "DATA", "UI", "TESTING",
                                                   "ARCHITECTURE", "WORKFLOW", "INFRASTRUCTURE",
                                                   "TOOLING", "DOCS", "SECURITY", "PERFORMANCE"]):
                category = col

        # Last column is often evidence
        if columns:
            evidence = columns[-1]

        return Gap(
            id=gap_id,
            description=description,
            priority=priority,
            category=category,
            evidence=evidence,
            is_resolved=is_resolved
        )

    def get_open_gaps(self) -> List[Gap]:
        """Get only open (non-resolved) gaps."""
        return [g for g in self.parse() if not g.is_resolved]

    def get_by_priority(self, priority: str) -> List[Gap]:
        """Get gaps filtered by priority."""
        return [g for g in self.get_open_gaps()
                if g.priority.upper().strip("*") == priority.upper()]

    def get_prioritized(self, limit: Optional[int] = None) -> List[Gap]:
        """Get open gaps sorted by priority (CRITICAL first)."""
        gaps = sorted(self.get_open_gaps(), key=lambda g: g.priority_order)
        if limit:
            return gaps[:limit]
        return gaps

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        all_gaps = self.parse()
        open_gaps = [g for g in all_gaps if not g.is_resolved]

        by_priority = {}
        for gap in open_gaps:
            p = gap.priority.upper().strip("*")
            by_priority[p] = by_priority.get(p, 0) + 1

        return {
            "total": len(all_gaps),
            "resolved": len(all_gaps) - len(open_gaps),
            "open": len(open_gaps),
            "by_priority": by_priority,
            "critical_count": by_priority.get("CRITICAL", 0),
            "high_count": by_priority.get("HIGH", 0),
        }


# Convenience functions for direct import
def parse_gaps(path: Optional[Path] = None) -> List[Gap]:
    """Parse all gaps from GAP-INDEX.md."""
    return GapParser(path).parse()


def get_prioritized_gaps(limit: int = 20, path: Optional[Path] = None) -> List[Gap]:
    """Get top N prioritized open gaps."""
    return GapParser(path).get_prioritized(limit)


def get_gap_summary(path: Optional[Path] = None) -> Dict:
    """Get gap statistics summary."""
    return GapParser(path).get_summary()


# CLI interface for testing
if __name__ == "__main__":
    parser = GapParser()
    summary = parser.get_summary()
    print(f"Gap Summary: {summary['open']} open, {summary['resolved']} resolved")
    print(f"  CRITICAL: {summary['critical_count']}")
    print(f"  HIGH: {summary['high_count']}")
    print()
    print("Top 10 prioritized gaps:")
    for gap in parser.get_prioritized(10):
        print(f"  {gap.to_todo_format()}")
