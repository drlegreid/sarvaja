"""
Tests for task parsing utilities.

Per GAP-FILE-026: Tests for extracted task_parsers.py module.
Covers status normalization, markdown table parsing, and ID extraction.

Created: 2026-01-30
"""

import pytest

from governance.task_parsers import (
    normalize_status,
    parse_markdown_table,
    extract_task_id,
    extract_gap_id,
    extract_linked_rules,
)


class TestNormalizeStatus:
    """Test status normalization to TASK-LIFE-01-v1 values."""

    @pytest.mark.parametrize("input_status,expected", [
        ("DONE", "CLOSED"),
        ("CLOSED", "CLOSED"),
        ("completed", "CLOSED"),
        ("COMPLETED", "CLOSED"),
    ])
    def test_closed_statuses(self, input_status, expected):
        """Various done/completed statuses map to CLOSED."""
        assert normalize_status(input_status) == expected

    @pytest.mark.parametrize("input_status,expected", [
        ("IN PROGRESS", "IN_PROGRESS"),
        ("IN_PROGRESS", "IN_PROGRESS"),
        ("in_progress", "IN_PROGRESS"),
    ])
    def test_in_progress_statuses(self, input_status, expected):
        """Various in-progress statuses map to IN_PROGRESS."""
        assert normalize_status(input_status) == expected

    @pytest.mark.parametrize("input_status,expected", [
        ("PENDING", "OPEN"),
        ("pending", "OPEN"),
        ("TODO", "OPEN"),
        ("OPEN", "OPEN"),
        ("ON HOLD", "OPEN"),
        ("ON_HOLD", "OPEN"),
        ("DEFERRED", "OPEN"),
    ])
    def test_open_statuses(self, input_status, expected):
        """Various pending/todo/hold statuses map to OPEN."""
        assert normalize_status(input_status) == expected

    def test_unknown_defaults_to_open(self):
        """Unknown status defaults to OPEN."""
        assert normalize_status("UNKNOWN") == "OPEN"
        assert normalize_status("") == "OPEN"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        assert normalize_status("  DONE  ") == "CLOSED"
        assert normalize_status(" TODO ") == "OPEN"


class TestParseMarkdownTable:
    """Test markdown table parsing."""

    def test_simple_table(self):
        """Parse a simple 2-column table."""
        content = """\
| Task | Status |
|------|--------|
| T-001 | DONE |
| T-002 | TODO |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["task"] == "T-001"
        assert rows[0]["status"] == "DONE"
        assert rows[1]["task"] == "T-002"

    def test_three_column_table(self):
        """Parse a 3-column table with various headers."""
        content = """\
| ID | Description | Phase |
|----|------------|-------|
| P10.1 | Implement feature | development |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 1
        assert rows[0]["id"] == "P10.1"
        assert rows[0]["description"] == "Implement feature"
        assert rows[0]["phase"] == "development"

    def test_empty_table(self):
        """Empty content returns no rows."""
        rows = parse_markdown_table("")
        assert len(rows) == 0

    def test_no_table(self):
        """Non-table content returns no rows."""
        rows = parse_markdown_table("Just some text\nwithout a table")
        assert len(rows) == 0

    def test_headers_normalized(self):
        """Headers are lowercased and spaces replaced with underscores."""
        content = """\
| Task ID | Gap ID | Status |
|---------|--------|--------|
| T-001 | GAP-001 | DONE |
"""
        rows = parse_markdown_table(content)
        assert "task_id" in rows[0]
        assert "gap_id" in rows[0]

    def test_hash_header(self):
        """# header is normalized to 'num'."""
        content = """\
| # | Task | Status |
|---|------|--------|
| 1 | T-001 | DONE |
"""
        rows = parse_markdown_table(content)
        assert "num" in rows[0]

    def test_separator_row_skipped(self):
        """Separator row (dashes) is not included as data."""
        content = """\
| Task | Status |
|------|--------|
| T-001 | DONE |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 1
        assert rows[0]["task"] == "T-001"

    def test_mismatched_columns_skipped(self):
        """Rows with wrong column count are skipped."""
        content = """\
| Task | Status | Phase |
|------|--------|-------|
| T-001 | DONE | dev |
| T-002 | TODO |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 1  # Second row has wrong column count

    def test_multiple_tables(self):
        """Parse multiple tables separated by non-table text."""
        content = """\
| A | B |
|---|---|
| 1 | 2 |

Some text between tables

| X | Y |
|---|---|
| 3 | 4 |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2


class TestExtractTaskId:
    """Test task ID extraction from row data."""

    def test_from_task_column(self):
        """Extract from 'task' column."""
        assert extract_task_id({"task": "P10.1"}) == "P10.1"

    def test_from_id_column(self):
        """Extract from 'id' column."""
        assert extract_task_id({"id": "FH-001"}) == "FH-001"

    def test_from_task_id_column(self):
        """Extract from 'task_id' column."""
        assert extract_task_id({"task_id": "KAN-005"}) == "KAN-005"

    def test_extracts_from_text(self):
        """Extract ID from text containing a task ID."""
        assert extract_task_id({"task": "Implement P10.2b feature"}) == "P10.2"

    def test_no_match(self):
        """Return None when no task ID found."""
        assert extract_task_id({"description": "some text"}) is None

    def test_empty_row(self):
        """Return None for empty row."""
        assert extract_task_id({}) is None


class TestExtractGapId:
    """Test gap ID extraction from row data."""

    def test_from_gap_column(self):
        """Extract from 'gap' column."""
        assert extract_gap_id({"gap": "GAP-UI-001"}) == "GAP-UI-001"

    def test_from_gap_id_column(self):
        """Extract from 'gap_id' column."""
        assert extract_gap_id({"gap_id": "GAP-MCP-008"}) == "GAP-MCP-008"

    def test_from_evidence_column(self):
        """Extract from 'evidence' column."""
        assert extract_gap_id({"evidence": "Per GAP-FILE-026"}) == "GAP-FILE-026"

    def test_no_match(self):
        """Return None when no gap ID found."""
        assert extract_gap_id({"task": "T-001"}) is None

    def test_empty_row(self):
        """Return None for empty row."""
        assert extract_gap_id({}) is None


class TestExtractLinkedRules:
    """Test linked rule extraction from row data."""

    def test_single_rule(self):
        """Extract single RULE-NNN reference."""
        assert extract_linked_rules({"rules": "RULE-001"}) == ["RULE-001"]

    def test_multiple_rules(self):
        """Extract multiple RULE-NNN references."""
        result = extract_linked_rules({"rules": "RULE-001, RULE-012"})
        assert "RULE-001" in result
        assert "RULE-012" in result

    def test_from_linked_rules_column(self):
        """Extract from 'linked_rules' column."""
        assert extract_linked_rules({"linked_rules": "RULE-005"}) == ["RULE-005"]

    def test_no_match(self):
        """Return None when no rules found."""
        assert extract_linked_rules({"task": "T-001"}) is None

    def test_empty_row(self):
        """Return None for empty row."""
        assert extract_linked_rules({}) is None
