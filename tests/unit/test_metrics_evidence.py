"""
Unit tests for Session Metrics Evidence Generation.

Per SESSION-METRICS-01-v1: Tests for generate_evidence_markdown
and write_evidence_file.
"""

import pytest
from pathlib import Path

from governance.session_metrics.evidence import (
    generate_evidence_markdown,
    write_evidence_file,
)


# ---------------------------------------------------------------------------
# generate_evidence_markdown
# ---------------------------------------------------------------------------
class TestGenerateEvidenceMarkdown:
    """Tests for generate_evidence_markdown()."""

    def test_title_present(self):
        md = generate_evidence_markdown({})
        assert "# Session Metrics Evidence" in md

    def test_rule_reference(self):
        md = generate_evidence_markdown({})
        assert "SESSION-METRICS-01-v1" in md

    def test_totals_table(self):
        metrics = {"totals": {"active_minutes": 100, "session_count": 5}}
        md = generate_evidence_markdown(metrics)
        assert "## Totals" in md
        assert "| Active Minutes | 100 |" in md
        assert "| Session Count | 5 |" in md

    def test_defaults_for_missing_totals(self):
        md = generate_evidence_markdown({})
        assert "| Active Minutes | 0 |" in md
        assert "| Session Count | 0 |" in md

    def test_all_total_fields(self):
        metrics = {"totals": {
            "active_minutes": 10, "session_count": 2,
            "message_count": 30, "tool_calls": 15,
            "mcp_calls": 5, "thinking_chars": 1000,
            "days_covered": 3, "api_errors": 1, "error_rate": 0.05,
        }}
        md = generate_evidence_markdown(metrics)
        assert "| Message Count | 30 |" in md
        assert "| Tool Calls | 15 |" in md
        assert "| MCP Calls | 5 |" in md
        assert "| Thinking Chars | 1000 |" in md
        assert "| Days Covered | 3 |" in md
        assert "| API Errors | 1 |" in md
        assert "| Error Rate | 0.05 |" in md

    def test_per_day_breakdown(self):
        metrics = {"days": [
            {"date": "2026-02-10", "active_minutes": 60, "session_count": 2,
             "message_count": 10, "tool_calls": 5, "mcp_calls": 3, "api_errors": 0},
            {"date": "2026-02-11", "active_minutes": 90, "session_count": 3,
             "message_count": 20, "tool_calls": 8, "mcp_calls": 4, "api_errors": 1},
        ]}
        md = generate_evidence_markdown(metrics)
        assert "## Per-Day Breakdown" in md
        assert "2026-02-10" in md
        assert "2026-02-11" in md

    def test_no_days_skips_section(self):
        md = generate_evidence_markdown({"days": []})
        assert "## Per-Day Breakdown" not in md

    def test_tool_breakdown_sorted_descending(self):
        metrics = {"tool_breakdown": {"Read": 10, "Write": 5, "Edit": 20}}
        md = generate_evidence_markdown(metrics)
        assert "## Tool Breakdown" in md
        lines = md.split("\n")
        tool_lines = [l for l in lines if l.startswith("| ") and "Edit" in l or "Read" in l or "Write" in l]
        # Edit (20) should come before Read (10) which should come before Write (5)
        edit_idx = md.index("Edit")
        read_idx = md.index("Read")
        write_idx = md.index("Write")
        assert edit_idx < read_idx < write_idx

    def test_no_tool_breakdown_skips_section(self):
        md = generate_evidence_markdown({"tool_breakdown": {}})
        assert "## Tool Breakdown" not in md

    def test_footer(self):
        md = generate_evidence_markdown({})
        assert "Auto-generated evidence" in md


# ---------------------------------------------------------------------------
# write_evidence_file
# ---------------------------------------------------------------------------
class TestWriteEvidenceFile:
    """Tests for write_evidence_file()."""

    def test_creates_file(self, tmp_path):
        metrics = {"totals": {"active_minutes": 10}}
        filepath = write_evidence_file(metrics, output_dir=tmp_path, date_str="2026-02-11")
        assert filepath.exists()
        assert filepath.name == "SESSION-2026-02-11-METRICS.md"

    def test_file_content(self, tmp_path):
        metrics = {"totals": {"session_count": 3}}
        filepath = write_evidence_file(metrics, output_dir=tmp_path, date_str="2026-02-11")
        content = filepath.read_text(encoding="utf-8")
        assert "Session Metrics Evidence" in content
        assert "| Session Count | 3 |" in content

    def test_creates_directory(self, tmp_path):
        sub = tmp_path / "nested" / "dir"
        metrics = {}
        filepath = write_evidence_file(metrics, output_dir=sub, date_str="2026-02-11")
        assert sub.exists()
        assert filepath.exists()

    def test_default_date(self, tmp_path):
        filepath = write_evidence_file({}, output_dir=tmp_path)
        assert filepath.name.startswith("SESSION-")
        assert filepath.name.endswith("-METRICS.md")

    def test_returns_path(self, tmp_path):
        result = write_evidence_file({}, output_dir=tmp_path, date_str="2026-01-01")
        assert isinstance(result, Path)
