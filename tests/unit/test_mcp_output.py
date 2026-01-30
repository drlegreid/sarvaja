"""
Tests for MCP output formatting utilities.

Per MCP-LOGGING-01-v1: Tests for structured output formatting.
Covers array truncation, JSON formatting, and token estimation.

Created: 2026-01-30
"""

import json
import pytest

from governance.mcp_output import (
    _truncate_arrays,
    format_output,
    parse_input,
    estimate_token_savings,
    OutputFormat,
)


class TestTruncateArrays:
    """Test recursive array truncation."""

    def test_short_array_unchanged(self):
        """Arrays within limit are unchanged."""
        data = [1, 2, 3]
        assert _truncate_arrays(data, max_items=5) == [1, 2, 3]

    def test_long_array_truncated(self):
        """Arrays exceeding limit are truncated with marker."""
        data = list(range(10))
        result = _truncate_arrays(data, max_items=3)
        assert len(result) == 4  # 3 items + marker
        assert result[-1]["_truncated"] is True
        assert result[-1]["_total"] == 10
        assert result[-1]["_shown"] == 3

    def test_dict_with_known_array_keys(self):
        """Dict with known array keys gets truncation metadata."""
        data = {"rules": list(range(10)), "name": "test"}
        result = _truncate_arrays(data, max_items=3)
        assert len(result["rules"]) == 3
        assert result["_rules_truncated"] is True
        assert result["_rules_total"] == 10
        assert result["name"] == "test"

    def test_nested_dict_truncation(self):
        """Nested structures are recursively truncated."""
        data = {"outer": {"items": list(range(10))}}
        result = _truncate_arrays(data, max_items=2)
        outer = result["outer"]
        assert len(outer["items"]) == 2  # known key: truncated in-place
        assert outer["_items_truncated"] is True
        assert outer["_items_total"] == 10

    def test_scalar_unchanged(self):
        """Scalar values pass through unchanged."""
        assert _truncate_arrays("hello", max_items=5) == "hello"
        assert _truncate_arrays(42, max_items=5) == 42
        assert _truncate_arrays(None, max_items=5) is None

    def test_empty_array(self):
        """Empty arrays pass through unchanged."""
        assert _truncate_arrays([], max_items=5) == []

    def test_exact_limit(self):
        """Array at exactly the limit is unchanged."""
        data = [1, 2, 3]
        assert _truncate_arrays(data, max_items=3) == [1, 2, 3]

    def test_multiple_known_keys(self):
        """Multiple known array keys are each truncated."""
        data = {
            "tasks": list(range(10)),
            "agents": list(range(8)),
            "sessions": list(range(5)),
        }
        result = _truncate_arrays(data, max_items=3)
        assert len(result["tasks"]) == 3
        assert result["_tasks_truncated"] is True
        assert len(result["agents"]) == 3
        assert result["_agents_truncated"] is True
        assert len(result["sessions"]) == 3  # Also truncated (5 > 3)
        assert result["_sessions_truncated"] is True


class TestFormatOutput:
    """Test output formatting."""

    def test_json_dict(self):
        """Format dict as JSON."""
        data = {"key": "value"}
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_json_list(self):
        """Format list as JSON."""
        data = [1, 2, 3]
        result = format_output(data, format=OutputFormat.JSON, max_array_items=0)
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_truncation_applied(self):
        """Array truncation is applied by default."""
        data = {"rules": list(range(100))}
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        assert len(parsed["rules"]) <= 31

    def test_no_truncation_with_zero(self):
        """max_array_items=0 disables truncation."""
        data = {"rules": list(range(100))}
        result = format_output(data, format=OutputFormat.JSON, max_array_items=0)
        parsed = json.loads(result)
        assert len(parsed["rules"]) == 100

    def test_handles_datetime(self):
        """Handles non-serializable objects via default=str."""
        from datetime import datetime
        data = {"time": datetime(2026, 1, 30)}
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        assert "2026" in parsed["time"]


class TestParseInput:
    """Test input parsing."""

    def test_parse_json(self):
        """Parse JSON string."""
        result = parse_input('{"key": "value"}')
        assert result["key"] == "value"

    def test_parse_json_array(self):
        """Parse JSON array string."""
        result = parse_input('[1, 2, 3]')
        assert result == [1, 2, 3]


class TestEstimateTokenSavings:
    """Test token savings estimation."""

    def test_returns_json_chars(self):
        """Always returns json_chars count."""
        data = {"rules": 50, "tasks": 85}
        result = estimate_token_savings(data)
        assert "json_chars" in result
        assert result["json_chars"] > 0

    def test_toon_availability_flag(self):
        """Returns toon_available flag."""
        data = {"test": "data"}
        result = estimate_token_savings(data)
        assert "toon_available" in result

    def test_savings_percent_present(self):
        """Returns savings_percent field."""
        data = {"test": "data"}
        result = estimate_token_savings(data)
        assert "savings_percent" in result
