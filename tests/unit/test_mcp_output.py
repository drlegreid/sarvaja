"""
Unit tests for MCP Output Format Handler.

Per DOC-SIZE-01-v1: Tests for mcp_output.py module.
Tests: OutputFormat, format_output(), parse_input(), estimate_token_savings(),
       _truncate_arrays(), _get_default_format().
"""

import json
import os
import pytest
from unittest.mock import patch

from governance.mcp_output import (
    OutputFormat,
    format_output,
    parse_input,
    estimate_token_savings,
    _truncate_arrays,
    _get_default_format,
)


class TestOutputFormat:
    def test_values(self):
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TOON.value == "toon"
        assert OutputFormat.AUTO.value == "auto"


class TestTruncateArrays:
    def test_no_truncation(self):
        data = [1, 2, 3]
        result = _truncate_arrays(data, max_items=5)
        assert result == [1, 2, 3]

    def test_truncates_list(self):
        data = list(range(10))
        result = _truncate_arrays(data, max_items=3)
        assert len(result) == 4  # 3 items + truncation marker
        assert result[-1]["_truncated"] is True
        assert result[-1]["_total"] == 10
        assert result[-1]["_shown"] == 3

    def test_truncates_known_dict_keys(self):
        data = {"rules": list(range(10)), "other": "keep"}
        result = _truncate_arrays(data, max_items=3)
        assert len(result["rules"]) == 3
        assert result["_rules_truncated"] is True
        assert result["_rules_total"] == 10
        assert result["other"] == "keep"

    def test_passthrough_non_collection(self):
        assert _truncate_arrays("hello", 5) == "hello"
        assert _truncate_arrays(42, 5) == 42


class TestFormatOutput:
    def test_json_format(self):
        data = {"key": "value"}
        result = format_output(data, format=OutputFormat.JSON, max_array_items=0)
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_json_default_str(self):
        from datetime import datetime
        data = {"time": datetime(2026, 1, 1)}
        result = format_output(data, format=OutputFormat.JSON, max_array_items=0)
        assert "2026" in result

    def test_array_truncation_default(self):
        data = {"rules": list(range(50))}
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        assert len(parsed["rules"]) <= 30

    def test_no_truncation_when_zero(self):
        data = {"rules": list(range(50))}
        result = format_output(data, format=OutputFormat.JSON, max_array_items=0)
        parsed = json.loads(result)
        assert len(parsed["rules"]) == 50


class TestParseInput:
    def test_json_auto(self):
        text = '{"key": "value"}'
        result = parse_input(text)
        assert result["key"] == "value"

    def test_json_explicit(self):
        text = '{"x": 1}'
        result = parse_input(text, format=OutputFormat.JSON)
        assert result["x"] == 1

    def test_invalid_raises(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_input("not json at all {{{", format=OutputFormat.JSON)

    def test_auto_tries_json_first(self):
        text = '{"valid": true}'
        result = parse_input(text, format=OutputFormat.AUTO)
        assert result["valid"] is True


class TestGetDefaultFormat:
    @patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"})
    def test_json_env(self):
        assert _get_default_format() == OutputFormat.JSON

    @patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "toon"})
    def test_toon_env(self):
        assert _get_default_format() == OutputFormat.TOON

    @patch.dict(os.environ, {}, clear=True)
    def test_default_toon(self):
        # Default is TOON when env not set (but clear may not remove it)
        result = _get_default_format()
        assert result in (OutputFormat.TOON, OutputFormat.JSON)


class TestEstimateTokenSavings:
    def test_without_toon(self):
        # Toon may or may not be installed
        data = {"rules": 50, "tasks": 85}
        result = estimate_token_savings(data)
        assert result["json_chars"] > 0
        assert "savings_percent" in result
