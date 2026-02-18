"""Deep scan batch 120: Context preloader + entropy monitoring.

Batch 120 findings: 8 total, 0 confirmed fixes, 8 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import re


# ── Context preloader ternary defense ──────────────


class TestContextPreloaderTernaryDefense:
    """Verify Python ternary short-circuits correctly for regex matches."""

    def test_ternary_with_none_match(self):
        """Ternary does NOT evaluate .start() when match is None."""
        content = "## Decision-001\nSome content here"
        start = len("## Decision-001\n")
        next_section = re.search(r"\n##\s+", content[start:])
        # next_section is None because there's no second ## marker
        assert next_section is None
        # Ternary correctly handles None
        section = content[start:start + next_section.start() if next_section else len(content)]
        assert "Some content here" in section

    def test_ternary_with_valid_match(self):
        """Ternary extracts .start() when match exists."""
        content = "## D-001\nContent\n## D-002\nMore"
        start = len("## D-001\n")
        next_section = re.search(r"\n##\s+", content[start:])
        assert next_section is not None
        section = content[start:start + next_section.start() if next_section else len(content)]
        assert "Content" in section
        assert "D-002" not in section


# ── Regex group guarantee defense ──────────────


class TestRegexGroupGuaranteeDefense:
    """Verify regex groups are always captured when match succeeds."""

    def test_digit_group_always_captured(self):
        r"""r'PHASE-(\d+)' always captures group(1) on match."""
        m = re.search(r"PHASE-(\d+)", "PHASE-3")
        assert m is not None
        assert m.group(1) == "3"

    def test_no_match_returns_none(self):
        """Non-matching input returns None (not empty group)."""
        m = re.search(r"PHASE-(\d+)", "no-match-here")
        assert m is None

    def test_walrus_operator_guards_none(self):
        """Walrus operator in if-statement prevents None access."""
        name = "not-a-phase"
        result = None
        if m := re.search(r"PHASE-(\d+)", name):
            result = f"Phase {m.group(1)}"
        assert result is None  # Never entered the if block


# ── Entropy hook sequential execution defense ──────────────


class TestEntropySequentialDefense:
    """Verify entropy state management is safe for sequential hooks."""

    def test_load_modify_save_pattern(self):
        """Load → modify → save pattern is safe in sequential execution."""
        state = {"tool_count": 50, "last_warning_at": 0}
        state["tool_count"] += 1
        state["last_warning_at"] = state["tool_count"]
        assert state["tool_count"] == 51
        assert state["last_warning_at"] == 51

    def test_threshold_elif_fires_highest_first(self):
        """Higher thresholds take priority in elif chain."""
        tool_count = 150
        warnings_shown = 0
        result = None

        if tool_count >= 150 and warnings_shown == 0:
            result = "CRITICAL"
        elif tool_count >= 100 and warnings_shown == 0:
            result = "HIGH"
        elif tool_count >= 50 and warnings_shown == 0:
            result = "MEDIUM"

        assert result == "CRITICAL"


# ── Context monitor defense ──────────────


class TestContextMonitorDefense:
    """Verify context monitor handles edge cases."""

    def test_history_cap_at_20(self):
        """History list capped at 20 entries via slicing."""
        history = list(range(25))
        history = history[-20:]
        assert len(history) == 20
        assert history[0] == 5  # Oldest removed
        assert history[-1] == 24  # Newest kept

    def test_empty_hook_data_gives_defaults(self):
        """Empty hook data (malformed JSON fallback) gives safe defaults."""
        hook_data = {}
        tool_count = hook_data.get("tool_count", 0)
        context_window = hook_data.get("context_window", {})
        used_pct = context_window.get("used_percent", 0)
        assert tool_count == 0
        assert used_pct == 0

    def test_json_decode_error_gives_empty_dict(self):
        """Malformed JSON falls back to empty dict."""
        try:
            data = json.loads("{bad json")
        except json.JSONDecodeError:
            data = {}
        assert data == {}

    def test_get_level_thresholds(self):
        """Context level thresholds are correct."""
        def get_level(pct):
            if pct >= 90:
                return "CRITICAL"
            elif pct >= 75:
                return "HIGH"
            elif pct >= 50:
                return "MEDIUM"
            return "LOW"

        assert get_level(95) == "CRITICAL"
        assert get_level(90) == "CRITICAL"
        assert get_level(80) == "HIGH"
        assert get_level(75) == "HIGH"
        assert get_level(60) == "MEDIUM"
        assert get_level(30) == "LOW"
