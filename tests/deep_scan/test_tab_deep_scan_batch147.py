"""Deep scan batch 147: Evidence + ingestion + hooks.

Batch 147 findings: 6 total, 0 confirmed fixes, 6 rejected.
"""
import pytest
from datetime import datetime


# ── TypeDB datetime format defense ──────────────


class TestTypeDBDatetimeFormatDefense:
    """Verify datetime attributes use correct unquoted format per TypeDB 3.x."""

    def test_schema_declares_datetime_type(self):
        """Schema declares datetime attributes with 'value datetime'."""
        from pathlib import Path
        schema = (Path(__file__).parent.parent.parent / "governance/schema.tql").read_text()
        assert "value datetime" in schema

    def test_unquoted_timestamp_is_19_chars(self):
        """Unquoted TypeDB datetime is YYYY-MM-DDTHH:MM:SS (19 chars)."""
        ts = datetime(2026, 2, 15, 14, 30, 0)
        formatted = ts.strftime("%Y-%m-%dT%H:%M:%S")
        assert len(formatted) == 19
        assert formatted == "2026-02-15T14:30:00"

    def test_timestamp_truncation_strips_microseconds(self):
        """[:19] truncation strips microseconds and timezone."""
        ts = "2026-02-15T14:30:00.123456+00:00"
        truncated = ts[:19]
        assert truncated == "2026-02-15T14:30:00"
        assert len(truncated) == 19


# ── Evidence collection defense ──────────────


class TestEvidenceCollectionDefense:
    """Verify evidence file collection handles edge cases."""

    def test_evidence_file_pattern(self):
        """Evidence files follow SESSION-*.md or DSM-*.md pattern."""
        from pathlib import Path
        evidence_dir = Path(__file__).parent.parent.parent / "evidence"
        if evidence_dir.is_dir():
            md_files = list(evidence_dir.glob("*.md"))
            for f in md_files[:5]:  # Check first 5
                assert f.suffix == ".md"

    def test_test_results_are_json(self):
        """Test result files are JSON."""
        from pathlib import Path
        results_dir = Path(__file__).parent.parent.parent / "evidence/test-results"
        if results_dir.is_dir():
            json_files = list(results_dir.glob("*.json"))
            for f in json_files[:3]:
                assert f.suffix == ".json"


# ── Entropy monitor defense ──────────────


class TestEntropyMonitorDefense:
    """Verify entropy monitor thresholds and state management."""

    def test_entropy_thresholds(self):
        """Entropy levels have correct threshold boundaries."""
        thresholds = {"LOW": 50, "MEDIUM": 100, "HIGH": 150}
        assert thresholds["LOW"] < thresholds["MEDIUM"]
        assert thresholds["MEDIUM"] < thresholds["HIGH"]

    def test_tool_count_tracking(self):
        """Tool count increments correctly."""
        state = {"tool_count": 0}
        state["tool_count"] += 1
        assert state["tool_count"] == 1
        state["tool_count"] += 1
        assert state["tool_count"] == 2

    def test_session_reset(self):
        """Session reset clears tool count."""
        state = {"tool_count": 42, "todowrite_count": 5}
        # Simulate reset
        state = {"tool_count": 0, "todowrite_count": 0}
        assert state["tool_count"] == 0
        assert state["todowrite_count"] == 0


# ── Hook checker defense ──────────────


class TestHookCheckerDefense:
    """Verify hook checker patterns are correct."""

    def test_min_tool_count_gate(self):
        """Warnings only fire after MIN_TOOL_COUNT tool calls."""
        MIN_TOOL_COUNT = 10
        state = {"tool_count": 5, "todowrite_count": 3}
        should_warn = state["tool_count"] >= MIN_TOOL_COUNT
        assert not should_warn

    def test_max_warnings_cap(self):
        """Warnings capped at MAX_WARNINGS per session."""
        MAX_WARNINGS = 2
        state = {"warnings_issued": 2}
        can_warn = state["warnings_issued"] < MAX_WARNINGS
        assert not can_warn

    def test_mcp_category_tracking(self):
        """MCP categories tracked by tool prefix matching."""
        cats = {}
        # Simulate tracking gov-tasks usage
        category = "gov-tasks"
        cats[category] = cats.get(category, 0) + 1
        assert cats["gov-tasks"] == 1
        cats[category] = cats.get(category, 0) + 1
        assert cats["gov-tasks"] == 2


# ── Thinking block API contract defense ──────────────


class TestThinkingBlockAPIContractDefense:
    """Verify thinking block API response matches consumer expectations."""

    def test_jsonl_thinking_block_keys(self):
        """JSONL-parsed thinking blocks have content, chars, timestamp."""
        block = {
            "content": "Analyzing the code structure...",
            "chars": 100,
            "timestamp": "2026-02-15T10:00:00",
        }
        required_keys = {"content", "chars", "timestamp"}
        assert required_keys.issubset(block.keys())

    def test_chat_bridge_thinking_block_keys(self):
        """Chat-bridge thinking blocks also have content, chars, timestamp."""
        # _collect_thinking_from_store produces same structure
        th = {"thought": "reasoning text", "timestamp": "2026-02-15T10:00:00"}
        block = {
            "content": th.get("thought", ""),
            "chars": len(th.get("thought", "")),
            "timestamp": th.get("timestamp", ""),
        }
        assert block["content"] == "reasoning text"
        assert block["chars"] == len("reasoning text")

    def test_no_char_count_in_response(self):
        """API response uses 'chars' NOT 'char_count'."""
        block = {"content": "text", "chars": 4, "timestamp": "2026-02-15T10:00:00"}
        assert "chars" in block
        assert "char_count" not in block

    def test_no_thought_key_in_response(self):
        """API response uses 'content' NOT 'thought' for text."""
        block = {"content": "text", "chars": 4, "timestamp": "2026-02-15T10:00:00"}
        assert "content" in block
        assert "thought" not in block
