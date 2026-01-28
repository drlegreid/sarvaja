"""
Gap Parser Unit Tests.

Per DATA-QUALITY: Validates gap parsing excludes Recently Resolved section.
"""

import pytest
from pathlib import Path
import tempfile

from governance.utils.gap_parser import GapParser, Gap


class TestGapParserSectionHandling:
    """Tests for section-aware parsing (DATA-QUALITY fix)."""

    def test_excludes_recently_resolved_section(self):
        """Parser should exclude gaps from 'Recently Resolved' section."""
        # Create a temp file simulating GAP-INDEX.md structure
        content = """# Gap Index

## Active Gaps

| ID | Priority | Status | Category |
|----|----------|--------|----------|
| GAP-ACTIVE-001 | HIGH | OPEN | testing |

## Recently Resolved (2026-01-20)

| ID | Resolution |
|----|------------|
| GAP-RESOLVED-001 | Fixed in PR #123 |
| GAP-RESOLVED-002 | Implemented feature |

## Quick Commands

Some other content here
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            parser = GapParser(temp_path)
            gaps = parser.get_open_gaps()

            # Should only have the active gap, not resolved ones
            gap_ids = [g.id for g in gaps]
            assert "GAP-ACTIVE-001" in gap_ids
            assert "GAP-RESOLVED-001" not in gap_ids
            assert "GAP-RESOLVED-002" not in gap_ids
        finally:
            temp_path.unlink()

    def test_handles_multiple_sections(self):
        """Parser should track section transitions correctly."""
        content = """# Gap Index

## Active Gaps

| ID | Priority |
|----|----------|
| GAP-OPEN-001 | HIGH |

## Recently Resolved

| ID | Resolution |
|----|------------|
| GAP-OLD-001 | Fixed |

## Data Architecture

Some text about architecture.

## Active Issues

| ID | Priority |
|----|----------|
| GAP-ISSUE-001 | MEDIUM |
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            parser = GapParser(temp_path)
            gaps = parser.get_open_gaps()
            gap_ids = [g.id for g in gaps]

            # Should have both active sections
            assert "GAP-OPEN-001" in gap_ids
            assert "GAP-ISSUE-001" in gap_ids
            # Should not have resolved
            assert "GAP-OLD-001" not in gap_ids
        finally:
            temp_path.unlink()


class TestGapParserBasic:
    """Basic parsing tests."""

    def test_gap_priority_order(self):
        """Test priority ordering for sorting."""
        critical = Gap("GAP-001", "desc", "CRITICAL", "cat")
        high = Gap("GAP-002", "desc", "HIGH", "cat")
        medium = Gap("GAP-003", "desc", "MEDIUM", "cat")
        low = Gap("GAP-004", "desc", "LOW", "cat")

        assert critical.priority_order < high.priority_order
        assert high.priority_order < medium.priority_order
        assert medium.priority_order < low.priority_order

    def test_gap_to_todo_format(self):
        """Test todo format output."""
        gap = Gap("GAP-TEST-001", "Fix the bug", "HIGH", "testing")
        todo = gap.to_todo_format()
        assert "[HIGH]" in todo
        assert "GAP-TEST-001" in todo
        assert "Fix the bug" in todo

    def test_gap_to_dict(self):
        """Test dictionary serialization."""
        gap = Gap("GAP-TEST-001", "Fix the bug", "HIGH", "testing", is_resolved=True)
        d = gap.to_dict()

        assert d["id"] == "GAP-TEST-001"
        assert d["description"] == "Fix the bug"
        assert d["priority"] == "HIGH"
        assert d["is_resolved"] is True
