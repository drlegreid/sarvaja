"""TOON Output Factory for Test Assertions.

Per GAP-DATA-001: Test utilities for TOON format validation.
Per DRY principles: Centralized TOON format helpers.

Created: 2026-01-19
"""

import json
from typing import Any, Dict, Optional


class TOONOutputFactory:
    """Factory for TOON format validation utilities.

    Usage:
        # Check if output is TOON format
        assert TOONOutputFactory.is_toon_format(output)

        # Parse output to data (works for both JSON and TOON)
        data = TOONOutputFactory.parse_auto(output)

        # Validate round-trip
        assert TOONOutputFactory.validate_roundtrip(original_data)
    """

    _toons_available: Optional[bool] = None

    @classmethod
    def _check_toons(cls) -> bool:
        """Check if toons library is available."""
        if cls._toons_available is None:
            try:
                import toons
                cls._toons_available = True
            except ImportError:
                cls._toons_available = False
        return cls._toons_available

    @staticmethod
    def is_toon_format(output: str) -> bool:
        """Check if output is in TOON format (not JSON).

        TOON format characteristics:
        - Does NOT start with { or [
        - Has field names followed by colon
        - May have array notation like items[3]{...}:
        """
        stripped = output.strip()
        # JSON starts with { or [
        if stripped.startswith("{") or stripped.startswith("["):
            return False
        return True

    @staticmethod
    def is_json_format(output: str) -> bool:
        """Check if output is valid JSON."""
        try:
            json.loads(output)
            return True
        except json.JSONDecodeError:
            return False

    @classmethod
    def parse_auto(cls, output: str) -> Any:
        """Parse output automatically detecting format.

        Args:
            output: String output from MCP tool

        Returns:
            Parsed data structure

        Raises:
            ValueError: If unable to parse
        """
        # Try JSON first
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

        # Try TOON if available
        if cls._check_toons():
            import toons
            try:
                return toons.loads(output)
            except Exception:
                pass

        raise ValueError(f"Unable to parse output: {output[:100]}...")

    @classmethod
    def format_as_toon(cls, data: Any) -> str:
        """Format data as TOON if library available, else JSON.

        Args:
            data: Data to format

        Returns:
            TOON-formatted string (or JSON fallback)
        """
        if cls._check_toons():
            import toons
            return toons.dumps(data)
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def format_as_json(cls, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def validate_roundtrip(cls, original_data: Any) -> bool:
        """Validate data survives TOON encode/decode roundtrip.

        Args:
            original_data: Original data structure

        Returns:
            True if roundtrip successful
        """
        if not cls._check_toons():
            return True  # Skip if toons not available

        import toons
        encoded = toons.dumps(original_data)
        decoded = toons.loads(encoded)
        return decoded == original_data

    @classmethod
    def measure_savings(cls, data: Any) -> Dict[str, Any]:
        """Measure token savings between JSON and TOON.

        Args:
            data: Data to measure

        Returns:
            Dict with json_chars, toon_chars, savings_percent
        """
        json_output = json.dumps(data, indent=2, default=str)
        json_chars = len(json_output)

        if cls._check_toons():
            import toons
            toon_output = toons.dumps(data)
            toon_chars = len(toon_output)
            savings = ((json_chars - toon_chars) / json_chars) * 100
            return {
                "json_chars": json_chars,
                "toon_chars": toon_chars,
                "savings_percent": round(savings, 1),
                "toon_available": True,
            }

        return {
            "json_chars": json_chars,
            "toon_chars": json_chars,
            "savings_percent": 0,
            "toon_available": False,
        }

    @classmethod
    def assert_toon_default(cls, output: str, context: str = "") -> None:
        """Assert that output is TOON format (default behavior).

        Args:
            output: MCP tool output
            context: Optional context for error message

        Raises:
            AssertionError: If output is JSON instead of TOON
        """
        if not cls._check_toons():
            return  # Can't test without toons library

        if not cls.is_toon_format(output):
            prefix = f"{context}: " if context else ""
            raise AssertionError(
                f"{prefix}Expected TOON format but got JSON. "
                f"Output starts with: {output[:50]}..."
            )

    @classmethod
    def assert_json_when_requested(cls, output: str, context: str = "") -> None:
        """Assert that output is valid JSON when requested.

        Args:
            output: MCP tool output
            context: Optional context for error message

        Raises:
            AssertionError: If output is not valid JSON
        """
        if not cls.is_json_format(output):
            prefix = f"{context}: " if context else ""
            raise AssertionError(
                f"{prefix}Expected JSON format but got invalid JSON. "
                f"Output starts with: {output[:50]}..."
            )
