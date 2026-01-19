"""MCP Output Format Handler - TOON vs JSON.

Per GAP-DATA-001: Token optimization for context reduction.
Per MCP-OUTPUT-01-v1: Standardized output formatting.

TOON (Token-Oriented Object Notation) provides 30-60% token savings
compared to JSON, reducing context consumption in LLM interactions.

Usage:
    from governance.mcp_output import format_output, OutputFormat

    # Default JSON (backward compatible)
    result = format_output(data)

    # TOON format for token savings
    result = format_output(data, format=OutputFormat.TOON)

    # Auto-select based on environment
    result = format_output(data, format=OutputFormat.AUTO)

Environment Variables:
    MCP_OUTPUT_FORMAT: "json" (default) or "toon"
"""

import json
import os
from enum import Enum
from typing import Any, Optional

# Lazy-loaded TOON module
_toons: Optional[Any] = None


class OutputFormat(Enum):
    """MCP output format options."""
    JSON = "json"
    TOON = "toon"
    AUTO = "auto"  # Uses MCP_OUTPUT_FORMAT env var


def _get_toons():
    """Lazy load toons module.

    The toons library uses JSON-like API:
    - toons.dumps(data) -> str
    - toons.loads(text) -> data
    """
    global _toons
    if _toons is None:
        try:
            import toons as t
            # Verify API exists
            if hasattr(t, 'dumps') and hasattr(t, 'loads'):
                _toons = t
            else:
                _toons = False
        except ImportError:
            # Fallback: toons not installed
            _toons = False
    return _toons


def _get_default_format() -> OutputFormat:
    """Get default format from environment."""
    env_format = os.getenv("MCP_OUTPUT_FORMAT", "json").lower()
    if env_format == "toon":
        return OutputFormat.TOON
    return OutputFormat.JSON


def format_output(
    data: Any,
    format: OutputFormat = OutputFormat.AUTO,
    indent: int = 2,
    ensure_ascii: bool = False
) -> str:
    """Format data for MCP tool output.

    Args:
        data: Data to serialize (dict, list, or any JSON-serializable)
        format: Output format (JSON, TOON, or AUTO)
        indent: JSON indentation (ignored for TOON)
        ensure_ascii: Escape non-ASCII characters (JSON only)

    Returns:
        Formatted string (JSON or TOON)

    Example:
        >>> format_output({"rules": 50, "tasks": 85})
        '{"rules": 50, "tasks": 85}'

        >>> format_output({"rules": 50}, format=OutputFormat.TOON)
        'rules: 50'
    """
    # Resolve AUTO format
    if format == OutputFormat.AUTO:
        format = _get_default_format()

    # TOON format
    if format == OutputFormat.TOON:
        toons = _get_toons()
        if toons and toons is not False:
            try:
                return toons.dumps(data)
            except Exception:
                # Fallback to JSON on encoding error
                pass

    # Default: JSON format
    return json.dumps(data, indent=indent, default=str, ensure_ascii=ensure_ascii)


def parse_input(text: str, format: OutputFormat = OutputFormat.AUTO) -> Any:
    """Parse input from TOON or JSON format.

    Args:
        text: Input string (JSON or TOON)
        format: Expected format (AUTO tries both)

    Returns:
        Parsed Python object

    Raises:
        ValueError: If parsing fails
    """
    if format == OutputFormat.AUTO:
        # Try JSON first (more common)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try TOON
        toons = _get_toons()
        if toons and toons is not False:
            try:
                return toons.loads(text)
            except Exception:
                pass

        raise ValueError("Failed to parse input as JSON or TOON")

    if format == OutputFormat.TOON:
        toons = _get_toons()
        if toons and toons is not False:
            return toons.loads(text)
        raise ValueError("TOON format requested but toons module not available")

    return json.loads(text)


def estimate_token_savings(data: Any) -> dict:
    """Estimate token savings between JSON and TOON.

    Args:
        data: Data to compare

    Returns:
        Dict with json_chars, toon_chars, savings_percent
    """
    json_output = json.dumps(data, default=str)
    json_chars = len(json_output)

    toons = _get_toons()
    if toons and toons is not False:
        try:
            toon_output = toons.dumps(data)
            toon_chars = len(toon_output)
            savings = ((json_chars - toon_chars) / json_chars) * 100
            return {
                "json_chars": json_chars,
                "toon_chars": toon_chars,
                "savings_percent": round(savings, 1),
                "toon_available": True
            }
        except Exception:
            pass

    return {
        "json_chars": json_chars,
        "toon_chars": None,
        "savings_percent": 0,
        "toon_available": False
    }


# Convenience exports
__all__ = [
    "OutputFormat",
    "format_output",
    "parse_input",
    "estimate_token_savings",
]
