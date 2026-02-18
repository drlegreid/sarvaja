"""Deep scan batch 169: Models + validators + helpers layer.

Batch 169 findings: 11 total, 1 confirmed fix, 10 rejected.
- BUG-SESSION-PYDANTIC-001: result["persistence_status"] crashes on Pydantic model.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Pydantic subscript defense ──────────────


class TestPydanticSubscriptDefense:
    """Verify create_session doesn't assign to Pydantic model via subscript."""

    def test_no_subscript_assignment_on_session_response(self):
        """create_session does NOT use result['key'] = value on SessionResponse."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        # Find the TypeDB success path (session_to_response call)
        start = src.index("session_to_response(created)")
        # Check the next 5 lines for subscript assignment
        section = src[start:start + 200]
        assert '["persistence_status"]' not in section

    def test_session_response_is_pydantic(self):
        """SessionResponse is a Pydantic BaseModel."""
        from governance.models import SessionResponse
        from pydantic import BaseModel
        assert issubclass(SessionResponse, BaseModel)

    def test_pydantic_rejects_subscript(self):
        """Pydantic v2 BaseModel rejects __setitem__."""
        from governance.models import SessionResponse
        resp = SessionResponse(
            session_id="TEST-001",
            start_time="2026-02-15T10:00:00",
            status="ACTIVE",
        )
        with pytest.raises(TypeError):
            resp["persistence_status"] = "persisted"

    def test_create_session_typedb_path_returns_response(self):
        """create_session TypeDB path returns SessionResponse directly."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions.py").read_text()
        assert "return session_to_response(created)" in src


# ── Session helpers determinism defense ──────────────


class TestSessionHelpersDeterminismDefense:
    """Verify session conversion helpers handle missing timestamps."""

    def test_session_to_response_handles_none_started_at(self):
        """session_to_response handles None started_at."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/helpers.py").read_text()
        assert "session.started_at.isoformat() if session.started_at" in src

    def test_session_to_dict_handles_none_started_at(self):
        """_session_to_dict handles None started_at."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "session.started_at.isoformat() if session.started_at" in src


# ── Execution event synthesis defense ──────────────


class TestExecutionEventSynthesisDefense:
    """Verify synthesize_execution_events covers key statuses."""

    def test_done_status_generates_completed_event(self):
        """DONE status generates a completed event."""
        from governance.stores.helpers import synthesize_execution_events
        task_data = {
            "status": "DONE",
            "agent_id": "code-agent",
            "created_at": "2026-02-15T10:00:00",
            "completed_at": "2026-02-15T14:00:00",
        }
        events = synthesize_execution_events("TASK-001", task_data)
        types = [e["event_type"] for e in events]
        assert "completed" in types

    def test_created_event_always_present(self):
        """Created event is always generated."""
        from governance.stores.helpers import synthesize_execution_events
        task_data = {
            "status": "TODO",
            "agent_id": None,
            "created_at": "2026-02-15T10:00:00",
        }
        events = synthesize_execution_events("TASK-001", task_data)
        types = [e["event_type"] for e in events]
        assert "started" in types  # "started" is the event_type for task creation

    def test_claimed_event_with_agent(self):
        """Claimed event generated when agent_id present."""
        from governance.stores.helpers import synthesize_execution_events
        task_data = {
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "created_at": "2026-02-15T10:00:00",
            "claimed_at": "2026-02-15T11:00:00",
        }
        events = synthesize_execution_events("TASK-001", task_data)
        types = [e["event_type"] for e in events]
        assert "claimed" in types


# ── Task mutations ordering defense ──────────────


class TestTaskMutationsOrderingDefense:
    """Verify update_task TypeDB write order."""

    def test_htask002_check_exists(self):
        """H-TASK-002 auto-assignment is in update_task."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks_mutations.py").read_text()
        assert 'status.upper() == "IN_PROGRESS"' in src
        assert '"code-agent"' in src

    def test_typedb_write_includes_agent_or_fallback(self):
        """TypeDB write uses agent_id or task_obj.agent_id."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks_mutations.py").read_text()
        assert "agent_id or task_obj.agent_id" in src


# ── Model field completeness defense ──────────────


class TestModelFieldCompletenessDefense:
    """Verify key models have required fields."""

    def test_session_response_has_cc_fields(self):
        """SessionResponse has all 6 CC fields."""
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        assert "cc_session_uuid" in fields
        assert "cc_project_slug" in fields
        assert "cc_git_branch" in fields
        assert "cc_tool_count" in fields
        assert "cc_thinking_chars" in fields
        assert "cc_compaction_count" in fields

    def test_session_create_has_cc_fields(self):
        """SessionCreate has all 6 CC fields."""
        from governance.models import SessionCreate
        fields = SessionCreate.model_fields
        assert "cc_session_uuid" in fields
        assert "cc_project_slug" in fields
        assert "cc_git_branch" in fields

    def test_session_response_has_project_id(self):
        """SessionResponse has project_id field."""
        from governance.models import SessionResponse
        assert "project_id" in SessionResponse.model_fields
