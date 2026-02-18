"""Deep scan batch 123: Models + schemas + data validation.

Batch 123 findings: 9 total, 0 confirmed fixes, 9 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Pydantic v2 list default independence defense ──────────────


class TestPydanticV2ListDefaultDefense:
    """Verify Pydantic v2 creates independent list copies (NOT shared)."""

    def test_agent_create_list_independence(self):
        """AgentCreate capabilities list is independent per instance."""
        from governance.models import AgentCreate

        a1 = AgentCreate(agent_id="a1", name="A1", agent_type="code")
        a2 = AgentCreate(agent_id="a2", name="A2", agent_type="code")

        a1.capabilities.append("code-review")
        assert "code-review" not in a2.capabilities

    def test_agent_response_list_independence(self):
        """AgentResponse list fields are independent."""
        from governance.models import AgentResponse

        r1 = AgentResponse(
            agent_id="a1", name="A1", agent_type="code",
            trust_score=0.8, status="ACTIVE",
        )
        r2 = AgentResponse(
            agent_id="a2", name="A2", agent_type="code",
            trust_score=0.9, status="ACTIVE",
        )

        r1.capabilities.append("testing")
        r1.recent_sessions.append("s1")
        r1.active_tasks.append("t1")

        assert "testing" not in r2.capabilities
        assert "s1" not in r2.recent_sessions
        assert "t1" not in r2.active_tasks

    def test_decision_response_list_independence(self):
        """DecisionResponse linked_rules is independent."""
        from governance.models import DecisionResponse

        d1 = DecisionResponse(
            id="d1", name="D1", context="Ctx", rationale="Rat",
            status="ACTIVE",
        )
        d2 = DecisionResponse(
            id="d2", name="D2", context="Ctx", rationale="Rat",
            status="ACTIVE",
        )

        d1.linked_rules.append("RULE-001")
        assert "RULE-001" not in d2.linked_rules


# ── Task conversion fallback chain defense ──────────────


class TestTaskConversionFallbackDefense:
    """Verify task conversion handles missing fields gracefully."""

    def test_task_to_dict_converts_datetime(self):
        """_task_to_dict converts datetime to ISO string."""
        from governance.stores.typedb_access import _task_to_dict

        task = MagicMock()
        task.id = "TASK-001"
        task.name = "Test Task"
        task.description = "Description"
        task.body = None
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = None
        task.agent_id = None
        task.created_at = datetime(2026, 2, 15, 10, 0, 0)
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

        result = _task_to_dict(task)
        assert isinstance(result["created_at"], str)
        assert result["task_id"] == "TASK-001"
        assert result["status"] == "TODO"

    def test_or_empty_list_handles_none(self):
        """'or []' pattern handles None linked_* fields."""
        linked_rules = None
        result = linked_rules or []
        assert result == []

    def test_or_empty_list_preserves_values(self):
        """'or []' pattern preserves non-empty lists."""
        linked_rules = ["RULE-001", "RULE-002"]
        result = linked_rules or []
        assert result == ["RULE-001", "RULE-002"]


# ── Task status consistency defense ──────────────


class TestTaskStatusConsistencyDefense:
    """Verify task status values are consistent."""

    def test_task_create_default_status(self):
        """TaskCreate defaults to TODO status."""
        from governance.models import TaskCreate

        task = TaskCreate(description="Test", phase="planning")
        assert task.status == "TODO"

    def test_task_create_accepts_custom_status(self):
        """TaskCreate accepts custom status values."""
        from governance.models import TaskCreate

        task = TaskCreate(
            description="Test", phase="planning", status="IN_PROGRESS",
        )
        assert task.status == "IN_PROGRESS"


# ── Session response field defaults defense ──────────────


class TestSessionResponseFieldDefense:
    """Verify SessionResponse handles optional fields."""

    def test_session_response_minimal(self):
        """SessionResponse with minimal fields succeeds."""
        from governance.models import SessionResponse

        sr = SessionResponse(
            session_id="SESSION-2026-02-15-TEST",
            start_time="2026-02-15T10:00:00",
            status="ACTIVE",
        )
        assert sr.session_id == "SESSION-2026-02-15-TEST"
        assert sr.status == "ACTIVE"
        assert sr.agent_id is None

    def test_session_response_cc_fields(self):
        """SessionResponse with CC fields succeeds."""
        from governance.models import SessionResponse

        sr = SessionResponse(
            session_id="SESSION-2026-02-15-CC-abc123",
            start_time="2026-02-15T10:00:00",
            status="COMPLETED",
            cc_session_uuid="uuid-123",
            cc_project_slug="sarvaja",
        )
        assert sr.cc_session_uuid == "uuid-123"
        assert sr.cc_project_slug == "sarvaja"


# ── Rule response optional fields defense ──────────────


class TestRuleResponseOptionalDefense:
    """Verify RuleResponse handles optional fields."""

    def test_applicability_defaults_none(self):
        """applicability defaults to None (optional)."""
        from governance.models import RuleResponse

        rule = RuleResponse(
            id="TEST-001", name="Test", category="TEST",
            priority="HIGH", directive="Test directive", status="ACTIVE",
        )
        assert rule.applicability is None

    def test_applicability_accepts_valid(self):
        """applicability accepts MANDATORY/RECOMMENDED values."""
        from governance.models import RuleResponse

        rule = RuleResponse(
            id="TEST-001", name="Test", category="TEST",
            priority="HIGH", directive="Test directive", status="ACTIVE",
            applicability="MANDATORY",
        )
        assert rule.applicability == "MANDATORY"
