"""DSP-04b: task_parsers.py normalize_status comprehensive tests.

task_parsers.normalize_status is DIFFERENT from task_lifecycle.normalize_status.
task_parsers handles emoji/markdown/legacy symbols → canonical status.
task_lifecycle handles CLOSED→DONE alias only.

This tests the task_parsers version which is used during workspace scanning.
"""
import pytest

from governance.task_parsers import normalize_status


# =============================================================================
# 1. DONE Mappings
# =============================================================================


class TestDoneMappings:
    """All symbols/strings that should map to DONE."""

    def test_checkmark_emoji(self):
        assert normalize_status("✅") == "DONE"

    def test_checkmark_done(self):
        assert normalize_status("✅ DONE") == "DONE"

    def test_done_string(self):
        assert normalize_status("DONE") == "DONE"

    def test_closed_maps_to_done(self):
        """CLOSED normalized to DONE per EPIC-TASK-TAXONOMY-V2."""
        assert normalize_status("CLOSED") == "DONE"

    def test_completed_lowercase(self):
        assert normalize_status("completed") == "DONE"

    def test_completed_uppercase(self):
        assert normalize_status("COMPLETED") == "DONE"


# =============================================================================
# 2. IN_PROGRESS Mappings
# =============================================================================


class TestInProgressMappings:
    """All symbols that should map to IN_PROGRESS."""

    def test_construction_emoji(self):
        assert normalize_status("🚧") == "IN_PROGRESS"

    def test_in_progress_space(self):
        assert normalize_status("IN PROGRESS") == "IN_PROGRESS"

    def test_in_progress_underscore(self):
        assert normalize_status("IN_PROGRESS") == "IN_PROGRESS"

    def test_in_progress_lowercase(self):
        assert normalize_status("in_progress") == "IN_PROGRESS"


# =============================================================================
# 3. OPEN Mappings
# =============================================================================


class TestOpenMappings:
    """All symbols that should map to OPEN."""

    def test_hourglass_emoji(self):
        assert normalize_status("⏳") == "OPEN"

    def test_hourglass_pending(self):
        assert normalize_status("⏳ Pending") == "OPEN"

    def test_pending_uppercase(self):
        assert normalize_status("PENDING") == "OPEN"

    def test_pending_lowercase(self):
        assert normalize_status("pending") == "OPEN"

    def test_clipboard_emoji(self):
        assert normalize_status("📋") == "OPEN"

    def test_clipboard_todo(self):
        assert normalize_status("📋 TODO") == "OPEN"

    def test_todo_string(self):
        assert normalize_status("TODO") == "OPEN"

    def test_open_string(self):
        assert normalize_status("OPEN") == "OPEN"


# =============================================================================
# 4. Hold/Deferred → OPEN Mappings
# =============================================================================


class TestHoldMappings:
    """Held/deferred tasks map to OPEN (resolution handles deferred state)."""

    def test_pause_emoji(self):
        assert normalize_status("⏸️") == "OPEN"

    def test_pause_hold(self):
        assert normalize_status("⏸️ Hold") == "OPEN"

    def test_pause_na(self):
        assert normalize_status("⏸️ N/A") == "OPEN"

    def test_on_hold_uppercase(self):
        assert normalize_status("ON HOLD") == "OPEN"

    def test_on_hold_underscore(self):
        assert normalize_status("ON_HOLD") == "OPEN"

    def test_deferred(self):
        assert normalize_status("DEFERRED") == "OPEN"


# =============================================================================
# 5. Edge Cases
# =============================================================================


class TestNormalizeStatusEdgeCases:
    """Unknown values, whitespace, fallbacks."""

    def test_unknown_defaults_to_open(self):
        assert normalize_status("UNKNOWN") == "OPEN"

    def test_empty_string_defaults_to_open(self):
        assert normalize_status("") == "OPEN"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped before lookup."""
        assert normalize_status("  DONE  ") == "DONE"

    def test_mixed_case_not_recognized(self):
        """Only exact matches work — 'Done' is not in the map."""
        assert normalize_status("Done") == "OPEN"

    def test_random_string_defaults_to_open(self):
        assert normalize_status("banana") == "OPEN"
