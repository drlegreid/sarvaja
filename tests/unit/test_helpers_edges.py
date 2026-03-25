"""DSP-07: Store Helpers Edge Case Tests.

Covers gaps in governance/stores/helpers.py:
1. task_to_response — taxonomy V2 fields (layer/concern/method)
2. task_to_response — resolution_notes, workspace_id
3. session_to_response — all CC attributes
4. compute_session_duration_from_timestamps — edge cases
5. synthesize_execution_events — all event types
6. _str_or_none, _dt_to_iso — type guards
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from governance.stores.helpers import (
    task_to_response,
    session_to_response,
    compute_session_duration_from_timestamps,
    synthesize_execution_events,
    extract_session_id,
    _str_or_none,
    _dt_to_iso,
)
from governance.typedb.entities import Task, Session


# =============================================================================
# 1. _str_or_none Guard
# =============================================================================


class TestStrOrNone:
    """_str_or_none guards against non-string values (e.g., MagicMock)."""

    def test_string_passthrough(self):
        assert _str_or_none("hello") == "hello"

    def test_none_returns_none(self):
        assert _str_or_none(None) is None

    def test_int_returns_none(self):
        assert _str_or_none(42) is None

    def test_mock_returns_none(self):
        assert _str_or_none(MagicMock()) is None

    def test_empty_string_passthrough(self):
        assert _str_or_none("") == ""


# =============================================================================
# 2. _dt_to_iso Guard
# =============================================================================


class TestDtToIso:
    """_dt_to_iso handles datetime, string, and None."""

    def test_datetime_to_iso(self):
        dt = datetime(2026, 1, 15, 10, 30)
        assert _dt_to_iso(dt) == "2026-01-15T10:30:00"

    def test_string_passthrough(self):
        assert _dt_to_iso("2026-01-15T10:30:00") == "2026-01-15T10:30:00"

    def test_none_returns_none(self):
        assert _dt_to_iso(None) is None

    def test_non_standard_type_coerced(self):
        """Non-standard types are str()-ed."""
        result = _dt_to_iso(12345)
        assert result == "12345"


# =============================================================================
# 3. compute_session_duration_from_timestamps
# =============================================================================


class TestComputeSessionDuration:
    """Duration computation edge cases."""

    def test_normal_duration(self):
        start = datetime(2026, 1, 1, 9, 0)
        end = datetime(2026, 1, 1, 10, 30)
        assert compute_session_duration_from_timestamps(start, end) == "1h 30m"

    def test_short_duration(self):
        start = datetime(2026, 1, 1, 9, 0)
        end = datetime(2026, 1, 1, 9, 15)
        assert compute_session_duration_from_timestamps(start, end) == "15m"

    def test_very_short_duration(self):
        start = datetime(2026, 1, 1, 9, 0, 0)
        end = datetime(2026, 1, 1, 9, 0, 30)
        assert compute_session_duration_from_timestamps(start, end) == "<1m"

    def test_ongoing_session(self):
        start = datetime(2026, 1, 1, 9, 0)
        assert compute_session_duration_from_timestamps(start, None) == "ongoing"

    def test_no_start_returns_none(self):
        assert compute_session_duration_from_timestamps(None, None) is None

    def test_over_24h_cap(self):
        start = datetime(2026, 1, 1, 9, 0)
        end = datetime(2026, 1, 3, 9, 0)
        assert compute_session_duration_from_timestamps(start, end) == ">24h"

    def test_repair_generated_estimate(self):
        """Repair-generated timestamps get estimate marker."""
        start = "2026-01-01T09:00:00"
        end = "2026-01-01T13:00:00"
        assert compute_session_duration_from_timestamps(start, end) == "~4h (est)"

    def test_string_timestamps(self):
        start = "2026-01-01T09:00:00"
        end = "2026-01-01T10:45:00"
        assert compute_session_duration_from_timestamps(start, end) == "1h 45m"

    def test_negative_duration_absolute(self):
        """End before start → uses absolute value."""
        start = datetime(2026, 1, 1, 10, 0)
        end = datetime(2026, 1, 1, 9, 0)
        assert compute_session_duration_from_timestamps(start, end) == "1h 0m"


# =============================================================================
# 4. task_to_response — Taxonomy V2 Fields
# =============================================================================


class TestTaskToResponseTaxonomyV2:
    """task_to_response includes all new taxonomy fields."""

    def test_layer_concern_method_present(self):
        task = Task(
            id="T-1", name="test", status="TODO", phase="P10",
            layer="api", concern="security", method="automated",
        )
        resp = task_to_response(task)
        assert resp.layer == "api"
        assert resp.concern == "security"
        assert resp.method == "automated"

    def test_resolution_notes_present(self):
        task = Task(
            id="T-2", name="test", status="DONE", phase="P10",
            resolution_notes="Fixed via hotpatch",
        )
        resp = task_to_response(task)
        assert resp.resolution_notes == "Fixed via hotpatch"

    def test_mock_layer_returns_none(self):
        """MagicMock attributes are guarded to None."""
        task = MagicMock()
        task.id = "T-3"
        task.body = None
        task.description = "test"
        task.name = "test"
        task.phase = "P10"
        task.status = "TODO"
        task.resolution = "NONE"
        task.priority = "MEDIUM"
        task.task_type = "bug"
        task.summary = "test > mock > guard"
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None
        task.workspace_id = None
        task.resolution_notes = None
        # These are MagicMock — should be guarded to None
        task.layer = MagicMock()
        task.concern = MagicMock()
        task.method = MagicMock()

        resp = task_to_response(task)
        assert resp.layer is None
        assert resp.concern is None
        assert resp.method is None


# =============================================================================
# 5. session_to_response — CC Attributes
# =============================================================================


class TestSessionToResponseCCAttributes:
    """session_to_response includes Claude Code session attributes."""

    def test_all_cc_attributes(self):
        session = Session(
            id="S-CC-1", name="test", status="COMPLETED",
            started_at=datetime(2026, 1, 1, 9, 0),
            completed_at=datetime(2026, 1, 1, 10, 0),
            cc_session_uuid="uuid-123",
            cc_project_slug="platform",
            cc_git_branch="main",
            cc_tool_count=42,
            cc_thinking_chars=10000,
            cc_compaction_count=2,
            cc_external_name="Session about bugs",
        )
        resp = session_to_response(session)
        assert resp.cc_session_uuid == "uuid-123"
        assert resp.cc_project_slug == "platform"
        assert resp.cc_git_branch == "main"
        assert resp.cc_tool_count == 42
        assert resp.cc_thinking_chars == 10000
        assert resp.cc_compaction_count == 2
        assert resp.cc_external_name == "Session about bugs"

    def test_missing_cc_attributes_default_none(self):
        session = Session(
            id="S-CC-2", name="test",
            started_at=datetime(2026, 1, 1, 9, 0),
        )
        resp = session_to_response(session)
        assert resp.cc_session_uuid is None
        assert resp.cc_tool_count is None


# =============================================================================
# 6. synthesize_execution_events
# =============================================================================


class TestSynthesizeExecutionEvents:
    """synthesize_execution_events from task data."""

    def test_created_event(self):
        events = synthesize_execution_events("T-1", {
            "created_at": "2026-01-01T09:00:00",
            "status": "OPEN",
        })
        types = [e["event_type"] for e in events]
        assert "started" in types

    def test_claimed_event(self):
        events = synthesize_execution_events("T-1", {
            "created_at": "2026-01-01T09:00:00",
            "claimed_at": "2026-01-01T09:30:00",
            "agent_id": "code-agent",
            "status": "IN_PROGRESS",
        })
        types = [e["event_type"] for e in events]
        assert "claimed" in types

    def test_completed_event_on_done(self):
        events = synthesize_execution_events("T-1", {
            "created_at": "2026-01-01T09:00:00",
            "completed_at": "2026-01-01T10:00:00",
            "status": "DONE",
        })
        types = [e["event_type"] for e in events]
        assert "completed" in types

    def test_evidence_event(self):
        events = synthesize_execution_events("T-1", {
            "created_at": "2026-01-01T09:00:00",
            "evidence": "Tests pass: 42/42",
            "status": "DONE",
        })
        types = [e["event_type"] for e in events]
        assert "evidence" in types
        evidence_evt = [e for e in events if e["event_type"] == "evidence"][0]
        assert "42/42" in evidence_evt["message"]

    def test_empty_task_no_events(self):
        events = synthesize_execution_events("T-1", {})
        assert len(events) == 0

    def test_done_status_without_completed_at(self):
        """DONE status generates completed event even without timestamp."""
        events = synthesize_execution_events("T-1", {
            "status": "DONE",
        })
        types = [e["event_type"] for e in events]
        assert "completed" in types

    def test_long_evidence_truncated(self):
        long_evidence = "X" * 200
        events = synthesize_execution_events("T-1", {
            "evidence": long_evidence,
            "status": "DONE",
        })
        evidence_evt = [e for e in events if e["event_type"] == "evidence"][0]
        assert evidence_evt["message"].endswith("...")
        assert len(evidence_evt["message"]) <= 104  # 100 + "..."

    def test_typedb_task_object(self):
        """Accepts TypeDB Task objects too (hasattr path)."""
        task = Task(
            id="T-OBJ", name="test", status="DONE", phase="P10",
            created_at=datetime(2026, 1, 1, 9, 0),
            completed_at=datetime(2026, 1, 1, 10, 0),
            agent_id="code-agent",
        )
        events = synthesize_execution_events("T-OBJ", task)
        types = [e["event_type"] for e in events]
        assert "started" in types
        assert "completed" in types


# =============================================================================
# 7. extract_session_id
# =============================================================================


class TestExtractSessionId:
    """extract_session_id from filename patterns."""

    def test_standard_format(self):
        assert extract_session_id("SESSION-2026-01-15-Bug-fix.md") == "SESSION-2026-01-15-Bug-fix"

    def test_with_topic(self):
        assert extract_session_id("SESSION-2026-03-24-taxonomy-v2.md") is not None

    def test_non_session_file(self):
        assert extract_session_id("README.md") is None

    def test_partial_match(self):
        assert extract_session_id("SESSION-2026-01-15-test") is not None
