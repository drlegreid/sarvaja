"""
Gap Parser Unit Tests.

Per DATA-QUALITY: Validates gap parsing excludes Recently Resolved section.
Extended: Full coverage for Gap dataclass, GapParser, Priority, convenience functions.
"""

import pytest
from pathlib import Path
import tempfile

from governance.utils.gap_parser import (
    GapParser,
    Gap,
    Priority,
    parse_gaps,
    get_prioritized_gaps,
    get_gap_summary,
)


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


# ---------------------------------------------------------------------------
# Priority enum
# ---------------------------------------------------------------------------
class TestPriority:
    """Tests for Priority IntEnum."""

    def test_ordering(self):
        assert Priority.CRITICAL < Priority.HIGH < Priority.MEDIUM < Priority.LOW < Priority.UNKNOWN

    def test_values(self):
        assert Priority.CRITICAL == 1
        assert Priority.HIGH == 2
        assert Priority.MEDIUM == 3
        assert Priority.LOW == 4
        assert Priority.UNKNOWN == 5


# ---------------------------------------------------------------------------
# Gap dataclass extended
# ---------------------------------------------------------------------------
class TestGapExtended:
    """Extended tests for Gap dataclass."""

    def test_defaults(self):
        g = Gap(id="GAP-001", description="Desc", priority="HIGH", category="Testing")
        assert g.evidence == ""
        assert g.is_resolved is False

    def test_priority_order_with_stars(self):
        g = Gap(id="G-1", description="", priority="**HIGH**", category="")
        assert g.priority_order == 2

    def test_priority_order_case_insensitive(self):
        g = Gap(id="G-1", description="", priority="medium", category="")
        assert g.priority_order == 3

    def test_priority_order_unknown(self):
        g = Gap(id="G-1", description="", priority="CUSTOM", category="")
        assert g.priority_order == 5

    def test_to_dict_includes_priority_order(self):
        g = Gap(id="G-1", description="", priority="CRITICAL", category="")
        assert g.to_dict()["priority_order"] == 1

    def test_to_dict_all_fields(self):
        g = Gap(id="GAP-001", description="Desc", priority="HIGH", category="Testing",
                evidence="ev.md", is_resolved=True)
        d = g.to_dict()
        assert d["evidence"] == "ev.md"
        assert d["is_resolved"] is True
        assert d["category"] == "Testing"


# ---------------------------------------------------------------------------
# GapParser._parse_line unit tests
# ---------------------------------------------------------------------------
class TestParseLineUnit:
    """Tests for GapParser._parse_line()."""

    def setup_method(self):
        self.parser = GapParser(Path("/nonexistent"))

    def test_skips_non_table_lines(self):
        assert self.parser._parse_line("Regular text") is None

    def test_skips_lines_without_gap(self):
        assert self.parser._parse_line("| Some | Table | Row |") is None

    def test_skips_header_line(self):
        assert self.parser._parse_line("| ID | Description | Priority |") is None

    def test_skips_separator_line(self):
        assert self.parser._parse_line("|----|----|----| GAP-001") is None

    def test_parses_basic_row(self):
        line = "| GAP-TEST-001 | Fix the login bug | HIGH | Testing | ev.md |"
        gap = self.parser._parse_line(line)
        assert gap is not None
        assert gap.id == "GAP-TEST-001"
        assert gap.priority == "HIGH"
        assert gap.is_resolved is False

    def test_parses_strikethrough_resolved(self):
        line = "| ~~GAP-OLD-001~~ | Old bug | LOW | Legacy | ev.md |"
        gap = self.parser._parse_line(line)
        assert gap is not None
        assert gap.id == "GAP-OLD-001"
        assert gap.is_resolved is True

    def test_parses_resolved_keyword(self):
        line = "| GAP-FIX-001 | Fixed bug RESOLVED | MEDIUM | Testing | ev.md |"
        gap = self.parser._parse_line(line)
        assert gap is not None
        assert gap.is_resolved is True

    def test_parses_priority_with_stars(self):
        line = "| GAP-STAR-001 | Description here | **CRITICAL** | Testing | ev.md |"
        gap = self.parser._parse_line(line)
        assert gap is not None
        assert gap.priority == "CRITICAL"

    def test_too_few_columns(self):
        line = "| GAP-TINY-001 |"
        result = self.parser._parse_line(line)
        assert result is None

    def test_default_priority_medium(self):
        line = "| GAP-DEF-001 | Some description that is long enough | NoCategory | ev.md |"
        gap = self.parser._parse_line(line)
        assert gap is not None
        assert gap.priority == "MEDIUM"


# ---------------------------------------------------------------------------
# GapParser.parse with file I/O
# ---------------------------------------------------------------------------
class TestGapParserFileIO:
    """Tests for GapParser.parse() with tmp_path file content."""

    def _write(self, tmp_path, content):
        p = tmp_path / "GAP-INDEX.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_file_not_found(self, tmp_path):
        parser = GapParser(tmp_path / "nonexistent.md")
        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_empty_file(self, tmp_path):
        p = self._write(tmp_path, "")
        assert GapParser(p).parse() == []

    def test_basic_parse(self, tmp_path):
        content = """\
## Open Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-001 | First gap description here | HIGH | Testing | ev1.md |
| GAP-002 | Second gap description here | CRITICAL | Data | ev2.md |
"""
        p = self._write(tmp_path, content)
        gaps = GapParser(p).parse()
        assert len(gaps) == 2
        assert gaps[0].id == "GAP-001"
        assert gaps[1].id == "GAP-002"

    def test_mixed_resolved_markers(self, tmp_path):
        content = """\
## Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-001 | Still open gap description | HIGH | Testing | ev.md |
| ~~GAP-002~~ | This gap was resolved | LOW | Testing | ev.md |
"""
        p = self._write(tmp_path, content)
        gaps = GapParser(p).parse()
        assert len(gaps) == 2
        open_gaps = [g for g in gaps if not g.is_resolved]
        assert len(open_gaps) == 1
        assert open_gaps[0].id == "GAP-001"


# ---------------------------------------------------------------------------
# GapParser convenience methods
# ---------------------------------------------------------------------------
class TestGapParserMethods:
    """Tests for GapParser higher-level methods."""

    def _setup(self, tmp_path):
        content = """\
## Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-CRIT-001 | Critical gap description here | CRITICAL | Data | ev.md |
| GAP-HIGH-001 | High prio gap description here | HIGH | Testing | ev.md |
| GAP-LOW-001 | Low priority gap description | LOW | UI | ev.md |
| ~~GAP-DONE-001~~ | Resolved gap description | HIGH | Arch | ev.md |
"""
        p = tmp_path / "GAP-INDEX.md"
        p.write_text(content, encoding="utf-8")
        return GapParser(p)

    def test_get_open_gaps(self, tmp_path):
        parser = self._setup(tmp_path)
        open_gaps = parser.get_open_gaps()
        assert len(open_gaps) == 3
        assert "GAP-DONE-001" not in [g.id for g in open_gaps]

    def test_get_by_priority(self, tmp_path):
        parser = self._setup(tmp_path)
        critical = parser.get_by_priority("CRITICAL")
        assert len(critical) == 1
        assert critical[0].id == "GAP-CRIT-001"

    def test_get_prioritized_sorted(self, tmp_path):
        parser = self._setup(tmp_path)
        gaps = parser.get_prioritized()
        assert gaps[0].id == "GAP-CRIT-001"
        assert gaps[-1].id == "GAP-LOW-001"

    def test_get_prioritized_with_limit(self, tmp_path):
        parser = self._setup(tmp_path)
        gaps = parser.get_prioritized(limit=2)
        assert len(gaps) == 2

    def test_get_summary(self, tmp_path):
        parser = self._setup(tmp_path)
        s = parser.get_summary()
        assert s["total"] == 4
        assert s["resolved"] == 1
        assert s["open"] == 3
        assert s["critical_count"] == 1
        assert s["high_count"] == 1


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------
class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_parse_gaps(self, tmp_path):
        content = """\
## Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-001 | Some open gap description here | HIGH | Testing | ev.md |
"""
        p = tmp_path / "GAP-INDEX.md"
        p.write_text(content, encoding="utf-8")
        gaps = parse_gaps(p)
        assert len(gaps) == 1

    def test_get_prioritized_gaps(self, tmp_path):
        content = """\
## Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-001 | Gap one description is here | LOW | Testing | ev.md |
| GAP-002 | Gap two description is here | HIGH | Data | ev.md |
"""
        p = tmp_path / "GAP-INDEX.md"
        p.write_text(content, encoding="utf-8")
        gaps = get_prioritized_gaps(limit=10, path=p)
        assert gaps[0].id == "GAP-002"

    def test_get_gap_summary(self, tmp_path):
        content = """\
## Gaps

| ID | Description | Priority | Category | Evidence |
|----|-------------|----------|----------|----------|
| GAP-001 | Only gap description is here | CRITICAL | Testing | ev.md |
"""
        p = tmp_path / "GAP-INDEX.md"
        p.write_text(content, encoding="utf-8")
        s = get_gap_summary(p)
        assert s["total"] == 1
        assert s["critical_count"] == 1
