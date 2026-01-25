"""
RF-004: Robot Framework Library for MCP Output Format.

Wraps governance/mcp_output.py for Robot Framework tests.
Per GAP-DATA-001: TOON format implementation.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MCPOutputLibrary:
    """Robot Framework library for MCP Output Format testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._toons_available = False
        try:
            import toons
            self._toons_available = True
        except ImportError:
            pass

    def toons_available(self) -> bool:
        """Check if toons library is available."""
        return self._toons_available

    # =========================================================================
    # OutputFormat Tests
    # =========================================================================

    def output_format_values(self) -> Dict[str, str]:
        """Test OutputFormat enum has expected values."""
        from governance.mcp_output import OutputFormat
        return {
            "json": OutputFormat.JSON.value,
            "toon": OutputFormat.TOON.value,
            "auto": OutputFormat.AUTO.value
        }

    # =========================================================================
    # format_output Tests
    # =========================================================================

    def format_output_json_default(self) -> Dict[str, Any]:
        """Test JSON output is default."""
        from governance.mcp_output import format_output, OutputFormat

        data = {"rules": 50, "tasks": 85}
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        return {
            "valid_json": True,
            "data_matches": parsed == data
        }

    def format_output_handles_nested(self) -> Dict[str, Any]:
        """Test nested data structures."""
        from governance.mcp_output import format_output, OutputFormat

        data = {
            "summary": {"total": 50, "open": 24},
            "items": [{"id": "GAP-001"}, {"id": "GAP-002"}]
        }
        result = format_output(data, format=OutputFormat.JSON)
        parsed = json.loads(result)
        return {
            "summary_total": parsed["summary"]["total"],
            "items_count": len(parsed["items"])
        }

    def format_output_handles_datetime(self) -> Dict[str, Any]:
        """Test datetime serialization via default=str."""
        from governance.mcp_output import format_output, OutputFormat
        from datetime import datetime

        data = {"created": datetime(2026, 1, 19, 12, 0, 0)}
        result = format_output(data, format=OutputFormat.JSON)
        return {
            "no_error": True,
            "contains_year": "2026" in result
        }

    # =========================================================================
    # parse_input Tests
    # =========================================================================

    def parse_input_json(self) -> Dict[str, Any]:
        """Test parsing JSON input."""
        from governance.mcp_output import parse_input, OutputFormat

        json_str = '{"rules": 50}'
        result = parse_input(json_str, format=OutputFormat.JSON)
        return {
            "rules": result["rules"],
            "is_dict": isinstance(result, dict)
        }

    def parse_input_auto_tries_json_first(self) -> Dict[str, Any]:
        """Test AUTO format tries JSON first."""
        from governance.mcp_output import parse_input, OutputFormat

        json_str = '{"rules": 50}'
        result = parse_input(json_str, format=OutputFormat.AUTO)
        return {
            "rules": result["rules"],
            "is_dict": isinstance(result, dict)
        }

    def parse_input_invalid_json_raises(self) -> Dict[str, Any]:
        """Test invalid JSON raises JSONDecodeError."""
        from governance.mcp_output import parse_input, OutputFormat

        try:
            parse_input("not valid json", format=OutputFormat.JSON)
            return {"raised_error": False}
        except json.JSONDecodeError:
            return {"raised_error": True}

    # =========================================================================
    # estimate_token_savings Tests
    # =========================================================================

    def estimate_token_savings(self) -> Dict[str, Any]:
        """Test estimation returns JSON character count."""
        from governance.mcp_output import estimate_token_savings

        data = {"rules": 50, "tasks": 85}
        result = estimate_token_savings(data)
        return {
            "has_json_chars": "json_chars" in result,
            "json_chars_positive": result.get("json_chars", 0) > 0,
            "has_toon_available": "toon_available" in result
        }

    # =========================================================================
    # TOON Integration Tests
    # =========================================================================

    def toon_format_output(self) -> Dict[str, Any]:
        """Test TOON format output with real library."""
        if not self._toons_available:
            return {"skipped": True, "reason": "toons not installed"}

        from governance.mcp_output import format_output, OutputFormat

        data = {"rules": 50, "tasks": 85, "sessions": 32}
        result = format_output(data, format=OutputFormat.TOON)
        json_output = json.dumps(data)
        return {
            "toon_shorter_or_equal": len(result) <= len(json_output),
            "toon_length": len(result),
            "json_length": len(json_output)
        }

    def toon_roundtrip(self) -> Dict[str, Any]:
        """Test TOON encode/decode roundtrip."""
        if not self._toons_available:
            return {"skipped": True, "reason": "toons not installed"}

        from governance.mcp_output import format_output, parse_input, OutputFormat

        data = {"id": "GAP-001", "status": "open", "priority": "HIGH"}
        encoded = format_output(data, format=OutputFormat.TOON)
        decoded = parse_input(encoded, format=OutputFormat.TOON)
        return {
            "roundtrip_successful": decoded == data
        }

    def estimate_shows_savings(self) -> Dict[str, Any]:
        """Test token savings estimation with real library."""
        if not self._toons_available:
            return {"skipped": True, "reason": "toons not installed"}

        from governance.mcp_output import estimate_token_savings

        data = {
            "items": [
                {"id": f"GAP-{i:03d}", "status": "open", "priority": "MEDIUM"}
                for i in range(10)
            ]
        }
        result = estimate_token_savings(data)
        return {
            "toon_available": result["toon_available"],
            "toon_smaller": result.get("toon_chars", 0) < result["json_chars"],
            "savings_percent": result.get("savings_percent", 0)
        }

    # =========================================================================
    # Fallback Behavior Tests
    # =========================================================================

    def toon_format_fallback_to_json(self) -> Dict[str, Any]:
        """Test TOON format falls back to JSON when library unavailable."""
        from governance.mcp_output import format_output, OutputFormat

        with patch("governance.mcp_output._toons", False):
            data = {"test": "data"}
            result = format_output(data, format=OutputFormat.TOON)
            parsed = json.loads(result)
            return {
                "valid_json": True,
                "data_matches": parsed == data
            }

    # =========================================================================
    # MCP Tool Helper Tests
    # =========================================================================

    def format_mcp_result_exists(self) -> Dict[str, Any]:
        """Test format_mcp_result is importable from common."""
        from governance.mcp_tools.common import format_mcp_result
        return {
            "callable": callable(format_mcp_result)
        }

    def format_mcp_result_json_explicit(self) -> Dict[str, Any]:
        """Test JSON output when explicitly requested via env."""
        from governance.mcp_tools.common import format_mcp_result

        data = {"rule_id": "RULE-001", "status": "ACTIVE"}

        with patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"}):
            result = format_mcp_result(data)
            parsed = json.loads(result)
            return {
                "valid_json": True,
                "data_matches": parsed == data
            }

    def format_mcp_result_handles_datetime(self) -> Dict[str, Any]:
        """Test datetime serialization (in JSON mode for compatibility)."""
        from governance.mcp_tools.common import format_mcp_result
        from datetime import datetime

        data = {"created": datetime(2026, 1, 19, 12, 0, 0)}

        with patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"}):
            result = format_mcp_result(data)
            return {
                "contains_year": "2026" in result
            }

    def format_mcp_result_with_list(self) -> Dict[str, Any]:
        """Test list output in JSON mode."""
        from governance.mcp_tools.common import format_mcp_result

        data = [{"id": "GAP-001"}, {"id": "GAP-002"}]

        with patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"}):
            result = format_mcp_result(data)
            parsed = json.loads(result)
            return {
                "list_length": len(parsed),
                "first_id": parsed[0]["id"]
            }
