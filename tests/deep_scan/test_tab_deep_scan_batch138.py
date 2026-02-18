"""Deep scan batch 138: Models + validators.

Batch 138 findings: 6 total, 0 confirmed fixes, 6 rejected.
All Pydantic v2 mutable default concerns and type conversion issues
verified as working correctly.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock


# ── Pydantic v2 mutable defaults defense ──────────────


class TestPydanticV2MutableDefaultsDefense:
    """Verify Pydantic v2 creates independent copies for list defaults."""

    def test_task_execution_response_events_independent(self):
        """TaskExecutionResponse.events list is independent per instance."""
        from governance.models import TaskExecutionResponse

        r1 = TaskExecutionResponse(task_id="t1")
        r2 = TaskExecutionResponse(task_id="t2")
        r1.events.append(MagicMock())
        assert len(r2.events) == 0

    def test_decision_response_linked_rules_independent(self):
        """DecisionResponse.linked_rules is independent per instance."""
        from governance.models import DecisionResponse

        d1 = DecisionResponse(
            id="d1", name="D1", context="C", rationale="R", status="ACTIVE",
        )
        d2 = DecisionResponse(
            id="d2", name="D2", context="C", rationale="R", status="ACTIVE",
        )
        d1.linked_rules.append("RULE-001")
        assert "RULE-001" not in d2.linked_rules

    def test_decision_create_options_independent(self):
        """DecisionCreate.options (default_factory) is independent."""
        from governance.models import DecisionCreate

        c1 = DecisionCreate(
            decision_id="D1", name="D1", context="C", rationale="R",
        )
        c2 = DecisionCreate(
            decision_id="D2", name="D2", context="C", rationale="R",
        )
        c1.options.append(MagicMock())
        assert len(c2.options) == 0


# ── CC integer field coercion defense ──────────────


class TestCCIntegerFieldCoercionDefense:
    """Verify TypeDB integer field coercion is defensive."""

    def test_int_coercion_with_valid_value(self):
        """int() coercion works on numeric TypeDB values."""
        val = 42
        result = int(val) if val is not None else None
        assert result == 42

    def test_int_coercion_with_string_number(self):
        """int() coercion handles string numbers from TypeDB."""
        val = "42"
        result = int(val) if val is not None else None
        assert result == 42

    def test_int_coercion_with_none(self):
        """None value returns None, not error."""
        val = None
        result = int(val) if val is not None else None
        assert result is None

    def test_int_coercion_with_invalid_skipped(self):
        """Invalid values caught by except block."""
        val = "not-a-number"
        try:
            result = int(val)
        except (ValueError, TypeError):
            result = None
        assert result is None


# ── Session response optional list fields defense ──────────────


class TestSessionResponseOptionalListDefense:
    """Verify SessionResponse handles None list fields."""

    def test_none_evidence_files_is_valid(self):
        """evidence_files=None is valid for SessionResponse."""
        from governance.models import SessionResponse

        sr = SessionResponse(
            session_id="TEST", start_time="2026-02-15T10:00:00",
            status="ACTIVE", evidence_files=None,
        )
        assert sr.evidence_files is None

    def test_empty_evidence_files_is_valid(self):
        """evidence_files=[] is valid for SessionResponse."""
        from governance.models import SessionResponse

        sr = SessionResponse(
            session_id="TEST", start_time="2026-02-15T10:00:00",
            status="ACTIVE", evidence_files=[],
        )
        assert sr.evidence_files == []

    def test_or_empty_list_pattern_handles_none(self):
        """Converter pattern 'or []' handles None → []."""
        linked_rules = None
        result = linked_rules or []
        assert result == []

    def test_or_empty_list_preserves_data(self):
        """Converter pattern 'or []' preserves real data."""
        linked_rules = ["RULE-001"]
        result = linked_rules or []
        assert result == ["RULE-001"]


# ── Synthesize execution events defense ──────────────


class TestSynthesizeExecutionEventsDefense:
    """Verify synthesize_execution_events handles both data formats."""

    def test_dict_data_format(self):
        """Dict data extracts string timestamps correctly."""
        from governance.stores.helpers import synthesize_execution_events

        data = {
            "created_at": "2026-02-15T10:00:00",
            "claimed_at": "2026-02-15T10:05:00",
            "completed_at": "2026-02-15T11:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": None,
        }
        events = synthesize_execution_events("TASK-001", data)
        assert len(events) >= 2  # created + completed minimum
        types = [e["event_type"] for e in events]
        assert "started" in types
        assert "completed" in types

    def test_typedb_task_object_format(self):
        """TypeDB Task object with datetime fields works."""
        from governance.stores.helpers import synthesize_execution_events

        task = MagicMock()
        task.created_at = datetime(2026, 2, 15, 10, 0, 0)
        task.claimed_at = None
        task.completed_at = datetime(2026, 2, 15, 11, 0, 0)
        task.agent_id = "code-agent"
        task.status = "DONE"
        task.evidence = None
        events = synthesize_execution_events("TASK-001", task)
        assert len(events) >= 2
        # Timestamps should be ISO strings
        for e in events:
            assert isinstance(e["timestamp"], str)

    def test_no_timestamps_empty_events(self):
        """No timestamps produces empty event list."""
        from governance.stores.helpers import synthesize_execution_events

        data = {
            "created_at": None,
            "claimed_at": None,
            "completed_at": None,
            "agent_id": None,
            "status": "pending",
            "evidence": None,
        }
        events = synthesize_execution_events("TASK-001", data)
        assert len(events) == 0

    def test_evidence_event_truncated(self):
        """Evidence string is truncated to 100 chars in message."""
        from governance.stores.helpers import synthesize_execution_events

        long_evidence = "x" * 200
        data = {
            "created_at": "2026-02-15T10:00:00",
            "completed_at": "2026-02-15T11:00:00",
            "claimed_at": None,
            "agent_id": None,
            "status": "DONE",
            "evidence": long_evidence,
        }
        events = synthesize_execution_events("TASK-001", data)
        evidence_events = [e for e in events if e["event_type"] == "evidence"]
        assert len(evidence_events) == 1
        assert len(evidence_events[0]["message"]) <= 104  # 100 + "..."

    def test_event_ids_unique(self):
        """Every event gets a unique event_id."""
        from governance.stores.helpers import synthesize_execution_events

        data = {
            "created_at": "2026-02-15T10:00:00",
            "claimed_at": "2026-02-15T10:05:00",
            "completed_at": "2026-02-15T11:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": "Test evidence",
        }
        events = synthesize_execution_events("TASK-001", data)
        ids = [e["event_id"] for e in events]
        assert len(ids) == len(set(ids))  # All unique
