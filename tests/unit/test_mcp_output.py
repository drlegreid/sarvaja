"""Unit tests for MCP output format handler.

Per GAP-DATA-001: TOON format implementation.
Per TEST-GUARD-01-v1: Test coverage for new modules.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_output_format_values(self):
        """Test OutputFormat enum has expected values."""
        from governance.mcp_output import OutputFormat

        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TOON.value == "toon"
        assert OutputFormat.AUTO.value == "auto"


class TestFormatOutput:
    """Tests for format_output function."""

    def test_format_output_json_default(self):
        """Test JSON output is default."""
        from governance.mcp_output import format_output, OutputFormat

        data = {"rules": 50, "tasks": 85}
        result = format_output(data, format=OutputFormat.JSON)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data

    def test_format_output_handles_nested(self):
        """Test nested data structures."""
        from governance.mcp_output import format_output, OutputFormat

        data = {
            "summary": {"total": 50, "open": 24},
            "items": [{"id": "GAP-001"}, {"id": "GAP-002"}]
        }
        result = format_output(data, format=OutputFormat.JSON)

        parsed = json.loads(result)
        assert parsed["summary"]["total"] == 50
        assert len(parsed["items"]) == 2

    def test_format_output_handles_datetime(self):
        """Test datetime serialization via default=str."""
        from governance.mcp_output import format_output, OutputFormat
        from datetime import datetime

        data = {"created": datetime(2026, 1, 19, 12, 0, 0)}
        result = format_output(data, format=OutputFormat.JSON)

        # Should not raise, datetime converted to string
        assert "2026" in result

    def test_format_output_auto_uses_env(self):
        """Test AUTO format respects MCP_OUTPUT_FORMAT env."""
        from governance.mcp_output import format_output, OutputFormat

        data = {"test": "data"}

        # Default (no env) should use JSON
        with patch.dict(os.environ, {}, clear=True):
            # Reset cached format by reimporting
            import importlib
            import governance.mcp_output as mcp_out
            importlib.reload(mcp_out)

            result = mcp_out.format_output(data, format=OutputFormat.AUTO)
            # Should be valid JSON
            json.loads(result)


class TestParseInput:
    """Tests for parse_input function."""

    def test_parse_input_json(self):
        """Test parsing JSON input."""
        from governance.mcp_output import parse_input, OutputFormat

        json_str = '{"rules": 50}'
        result = parse_input(json_str, format=OutputFormat.JSON)

        assert result == {"rules": 50}

    def test_parse_input_auto_tries_json_first(self):
        """Test AUTO format tries JSON first."""
        from governance.mcp_output import parse_input, OutputFormat

        json_str = '{"rules": 50}'
        result = parse_input(json_str, format=OutputFormat.AUTO)

        assert result == {"rules": 50}

    def test_parse_input_invalid_json_raises(self):
        """Test invalid JSON raises when explicitly requesting JSON format."""
        from governance.mcp_output import parse_input, OutputFormat
        import json

        with pytest.raises(json.JSONDecodeError):
            parse_input("not valid json", format=OutputFormat.JSON)


class TestEstimateTokenSavings:
    """Tests for estimate_token_savings function."""

    def test_estimate_returns_json_chars(self):
        """Test estimation returns JSON character count."""
        from governance.mcp_output import estimate_token_savings

        data = {"rules": 50, "tasks": 85}
        result = estimate_token_savings(data)

        assert "json_chars" in result
        assert result["json_chars"] > 0
        assert "toon_available" in result


class TestToonIntegration:
    """Integration tests with actual toons library (if available)."""

    @pytest.fixture
    def skip_if_no_toons(self):
        """Skip test if toons not installed."""
        try:
            import toons
            yield toons
        except ImportError:
            pytest.skip("toons library not installed")

    def test_toon_format_output(self, skip_if_no_toons):
        """Test TOON format output with real library."""
        from governance.mcp_output import format_output, OutputFormat

        data = {"rules": 50, "tasks": 85, "sessions": 32}
        result = format_output(data, format=OutputFormat.TOON)

        # TOON output should be shorter than non-indented JSON
        json_output = json.dumps(data)  # No indent = compact
        # Note: TOON is ~24% shorter for simple objects
        assert len(result) <= len(json_output)

    def test_toon_roundtrip(self, skip_if_no_toons):
        """Test TOON encode/decode roundtrip."""
        from governance.mcp_output import format_output, parse_input, OutputFormat

        data = {"id": "GAP-001", "status": "open", "priority": "HIGH"}

        encoded = format_output(data, format=OutputFormat.TOON)
        decoded = parse_input(encoded, format=OutputFormat.TOON)

        assert decoded == data

    def test_estimate_shows_savings(self, skip_if_no_toons):
        """Test token savings estimation with real library."""
        from governance.mcp_output import estimate_token_savings

        # Larger data shows better savings
        data = {
            "items": [
                {"id": f"GAP-{i:03d}", "status": "open", "priority": "MEDIUM"}
                for i in range(10)
            ]
        }
        result = estimate_token_savings(data)

        assert result["toon_available"] is True
        assert result["toon_chars"] < result["json_chars"]
        assert result["savings_percent"] > 0


class TestFallbackBehavior:
    """Tests for fallback when toons not available."""

    def test_toon_format_fallback_to_json(self):
        """Test TOON format falls back to JSON when library unavailable."""
        from governance.mcp_output import format_output, OutputFormat

        # Mock toons as unavailable
        with patch("governance.mcp_output._toons", False):
            data = {"test": "data"}
            result = format_output(data, format=OutputFormat.TOON)

            # Should fallback to valid JSON
            parsed = json.loads(result)
            assert parsed == data
