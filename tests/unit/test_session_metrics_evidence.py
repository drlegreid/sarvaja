"""
Unit tests for Session Metrics Evidence Generation.

Per DOC-SIZE-01-v1: Tests for governance/session_metrics/evidence.py.
Tests: generate_evidence_markdown, write_evidence_file.
"""

from pathlib import Path

from governance.session_metrics.evidence import (
    generate_evidence_markdown,
    write_evidence_file,
)


def _sample_metrics():
    return {
        "totals": {
            "active_minutes": 120,
            "session_count": 5,
            "message_count": 42,
            "tool_calls": 100,
            "mcp_calls": 20,
            "thinking_chars": 5000,
            "days_covered": 3,
            "api_errors": 2,
            "error_rate": 0.02,
        },
        "days": [
            {
                "date": "2026-02-10",
                "active_minutes": 60,
                "session_count": 3,
                "message_count": 20,
                "tool_calls": 50,
                "mcp_calls": 10,
                "api_errors": 1,
            },
            {
                "date": "2026-02-11",
                "active_minutes": 60,
                "session_count": 2,
                "message_count": 22,
                "tool_calls": 50,
                "mcp_calls": 10,
                "api_errors": 1,
            },
        ],
        "tool_breakdown": {
            "Read": 40,
            "Write": 30,
            "Bash": 20,
            "Grep": 10,
        },
    }


# ── generate_evidence_markdown ─────────────────────────


class TestGenerateEvidenceMarkdown:
    def test_contains_title(self):
        result = generate_evidence_markdown(_sample_metrics())
        assert "# Session Metrics Evidence" in result

    def test_contains_rule_reference(self):
        result = generate_evidence_markdown(_sample_metrics())
        assert "SESSION-METRICS-01-v1" in result

    def test_contains_totals_table(self):
        result = generate_evidence_markdown(_sample_metrics())
        assert "| Active Minutes | 120 |" in result
        assert "| Session Count | 5 |" in result
        assert "| Tool Calls | 100 |" in result

    def test_contains_per_day_breakdown(self):
        result = generate_evidence_markdown(_sample_metrics())
        assert "## Per-Day Breakdown" in result
        assert "2026-02-10" in result
        assert "2026-02-11" in result

    def test_contains_tool_breakdown(self):
        result = generate_evidence_markdown(_sample_metrics())
        assert "## Tool Breakdown" in result
        assert "| Read | 40 |" in result
        assert "| Grep | 10 |" in result

    def test_tool_breakdown_sorted_descending(self):
        result = generate_evidence_markdown(_sample_metrics())
        read_pos = result.index("| Read |")
        grep_pos = result.index("| Grep |")
        assert read_pos < grep_pos

    def test_empty_metrics(self):
        result = generate_evidence_markdown({})
        assert "# Session Metrics Evidence" in result
        assert "| Active Minutes | 0 |" in result

    def test_no_days(self):
        metrics = {"totals": {"active_minutes": 10}, "days": [], "tool_breakdown": {}}
        result = generate_evidence_markdown(metrics)
        assert "## Per-Day Breakdown" not in result

    def test_no_tools(self):
        metrics = {"totals": {}, "days": [], "tool_breakdown": {}}
        result = generate_evidence_markdown(metrics)
        assert "## Tool Breakdown" not in result

    def test_footer(self):
        result = generate_evidence_markdown({})
        assert "Auto-generated evidence" in result


# ── write_evidence_file ────────────────────────────────


class TestWriteEvidenceFile:
    def test_writes_file(self, tmp_path):
        path = write_evidence_file(
            _sample_metrics(), output_dir=tmp_path, date_str="2026-02-11")

        assert path.exists()
        assert path.name == "SESSION-2026-02-11-METRICS.md"
        content = path.read_text()
        assert "# Session Metrics Evidence" in content

    def test_creates_output_dir(self, tmp_path):
        output = tmp_path / "new_dir"
        path = write_evidence_file(
            _sample_metrics(), output_dir=output, date_str="2026-02-11")

        assert output.exists()
        assert path.exists()

    def test_default_date(self, tmp_path):
        path = write_evidence_file(_sample_metrics(), output_dir=tmp_path)

        assert path.name.startswith("SESSION-")
        assert path.name.endswith("-METRICS.md")

    def test_content_has_totals(self, tmp_path):
        path = write_evidence_file(
            _sample_metrics(), output_dir=tmp_path, date_str="2026-02-11")

        content = path.read_text()
        assert "| Session Count | 5 |" in content
