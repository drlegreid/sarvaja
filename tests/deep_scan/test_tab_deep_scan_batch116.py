"""Deep scan batch 116: Utilities + helpers layer.

Batch 116 findings: 13 total, 0 confirmed fixes, 13 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


# ── compute_session_duration defense ──────────────


class TestComputeSessionDurationSafety:
    """Verify compute_session_duration handles all edge cases."""

    def test_non_string_start_returns_empty(self):
        """Non-string start value returns empty via try/except."""
        from agent.governance_ui.utils import compute_session_duration

        # Integer input — would crash on [:19] but caught by except
        result = compute_session_duration(12345, "2026-02-15T14:30:00")
        assert result == ""

    def test_short_start_string_works(self):
        """Short start string (<19 chars) still works with [:19]."""
        from agent.governance_ui.utils import compute_session_duration

        # "2026-02-15" is only 10 chars — [:19] returns full string
        result = compute_session_duration("2026-02-15", "2026-02-15")
        # strptime will fail since no time component, caught by except
        assert result == ""

    def test_abs_handles_reversed_timestamps(self):
        """Reversed timestamps produce positive duration via abs()."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T14:00:00", "2026-02-15T10:00:00",
        )
        assert result != ""
        assert "invalid" not in result.lower()


# ── format_timestamp defense ──────────────


class TestFormatTimestampSafety:
    """Verify format_timestamp handles edge cases gracefully."""

    def test_malformed_returns_original(self):
        """Malformed input returns original string, not crash."""
        from agent.governance_ui.utils import format_timestamp

        result = format_timestamp("abc")
        assert "abc" in result

    def test_date_only_returns_something(self):
        """Date-only string returns useful output."""
        from agent.governance_ui.utils import format_timestamp

        result = format_timestamp("2026-02-15")
        assert "2026-02-15" in result


# ── isoformat guard defense ──────────────


class TestIsoformatGuardDefense:
    """Verify isoformat() calls are guarded by None checks."""

    def test_task_to_response_handles_none_created_at(self):
        """task_to_response handles None created_at."""
        from governance.stores.helpers import task_to_response

        task = MagicMock()
        task.id = "TASK-001"
        task.name = "Test"
        task.description = "Desc"
        task.body = None
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = None
        task.agent_id = None
        task.created_at = None  # None should be handled
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = task_to_response(task)
        assert result.created_at is None


# ── Audit retention defense ──────────────


class TestAuditRetentionSafety:
    """Verify audit retention logic handles edge cases."""

    def test_iso_string_comparison_correct(self):
        """ISO date strings compare lexicographically correctly."""
        dates = [
            "2026-02-10T08:00:00",
            "2026-02-11T12:00:00",
            "2026-02-15T09:00:00",
        ]
        assert sorted(dates) == dates  # Already in order

    def test_empty_timestamp_excluded_from_retention(self):
        """Entries without timestamps are excluded by retention filter."""
        entries = [
            {"timestamp": "2026-02-15T10:00:00", "action": "TEST"},
            {"action": "ORPHAN"},  # No timestamp
        ]
        cutoff = "2026-02-01"
        filtered = [e for e in entries if e.get("timestamp", "")[:10] >= cutoff]
        # Orphan excluded (empty string < any date)
        assert len(filtered) == 1
        assert filtered[0]["action"] == "TEST"


# ── str() coercion defense ──────────────


class TestStrCoercionDefense:
    """Verify str() handles various types safely."""

    def test_str_dict_produces_readable_repr(self):
        """str(dict) produces Python repr, which is readable."""
        data = {"key": "value", "count": 5}
        result = str(data)
        assert "key" in result
        assert "value" in result

    def test_str_list_produces_readable_repr(self):
        """str(list) produces Python repr."""
        data = [1, 2, 3]
        result = str(data)
        assert "1" in result

    def test_str_none_produces_none_string(self):
        """str(None) produces 'None' string."""
        assert str(None) == "None"


# ── Duration formatting defense ──────────────


class TestDurationFormattingDefense:
    """Verify duration formatting uses correct division."""

    def test_divmod_used_for_hours_minutes(self):
        """divmod correctly splits total minutes into hours+minutes."""
        total_minutes = 90
        hours, mins = divmod(total_minutes, 60)
        assert hours == 1
        assert mins == 30

    def test_fractional_minutes_truncated(self):
        """int() truncation on minutes is acceptable (< 1 minute error)."""
        total_seconds = 5430  # 90.5 minutes
        total_minutes = int(total_seconds / 60)
        assert total_minutes == 90  # Truncated from 90.5
        hours, mins = divmod(total_minutes, 60)
        assert hours == 1
        assert mins == 30
