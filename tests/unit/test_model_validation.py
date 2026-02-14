"""
Tests for Pydantic model input validation.

Per RULE-012: DSP Semantic Code Structure.
Validates Literal enum types and min_length constraints on API models.

Created: 2026-01-30
"""

import pytest
from pydantic import ValidationError

from governance.models import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    DecisionCreate,
    DecisionUpdate,
    DecisionResponse,
    TaskCreate,
    TaskResponse,
    SessionResponse,
    SessionCreate,
    AgentResponse,
    PaginationMeta,
    PaginatedRuleResponse,
    PaginatedTaskResponse,
    PaginatedSessionResponse,
    PaginatedAgentResponse,
    PaginatedDecisionResponse,
    APIStatus,
)


class TestRuleCreateValidation:
    """Validate RuleCreate model constraints."""

    def test_valid_rule_create(self):
        """Accept valid rule creation data."""
        rule = RuleCreate(
            rule_id="RULE-099",
            name="Test Rule",
            category="governance",
            priority="HIGH",
            directive="Do something",
        )
        assert rule.rule_id == "RULE-099"
        assert rule.status == "DRAFT"

    def test_all_categories_accepted(self):
        """Accept all valid category values."""
        for cat in ["governance", "technical", "operational"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category=cat,
                priority="LOW", directive="D",
            )
            assert rule.category == cat

    def test_all_priorities_accepted(self):
        """Accept all valid priority values."""
        for pri in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority=pri, directive="D",
            )
            assert rule.priority == pri

    def test_all_statuses_accepted(self):
        """Accept all valid status values."""
        for st in ["DRAFT", "ACTIVE", "DEPRECATED"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="D", status=st,
            )
            assert rule.status == st

    def test_invalid_category_rejected(self):
        """Reject invalid category value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="invalid",
                priority="LOW", directive="D",
            )
        assert "category" in str(exc_info.value)

    def test_invalid_priority_rejected(self):
        """Reject invalid priority value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="ULTRA", directive="D",
            )
        assert "priority" in str(exc_info.value)

    def test_invalid_status_rejected(self):
        """Reject invalid status value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="D", status="INVALID",
            )
        assert "status" in str(exc_info.value)

    def test_empty_rule_id_rejected(self):
        """Reject empty rule_id."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="", name="N", category="governance",
                priority="LOW", directive="D",
            )
        assert "rule_id" in str(exc_info.value)

    def test_empty_name_rejected(self):
        """Reject empty name."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="", category="governance",
                priority="LOW", directive="D",
            )
        assert "name" in str(exc_info.value)

    def test_empty_directive_rejected(self):
        """Reject empty directive."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="",
            )
        assert "directive" in str(exc_info.value)


class TestRuleUpdateValidation:
    """Validate RuleUpdate model constraints."""

    def test_valid_partial_update(self):
        """Accept partial update with valid values."""
        update = RuleUpdate(priority="CRITICAL", status="ACTIVE")
        assert update.priority == "CRITICAL"
        assert update.status == "ACTIVE"
        assert update.name is None

    def test_empty_update_allowed(self):
        """Accept update with no fields set."""
        update = RuleUpdate()
        assert update.name is None
        assert update.category is None

    def test_invalid_category_rejected(self):
        """Reject invalid category in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(category="wrong")

    def test_invalid_priority_rejected(self):
        """Reject invalid priority in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(priority="SUPER")

    def test_invalid_status_rejected(self):
        """Reject invalid status in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(status="ARCHIVED")


class TestDecisionCreateValidation:
    """Validate DecisionCreate model constraints."""

    def test_valid_decision_create(self):
        """Accept valid decision creation data."""
        decision = DecisionCreate(
            decision_id="DECISION-099",
            name="Test Decision",
            context="Some context",
            rationale="Some reasoning",
        )
        assert decision.decision_id == "DECISION-099"
        assert decision.status == "PENDING"

    def test_all_statuses_accepted(self):
        """Accept all valid decision status values."""
        for st in ["PENDING", "APPROVED", "REJECTED"]:
            decision = DecisionCreate(
                decision_id="D1", name="N", context="C",
                rationale="R", status=st,
            )
            assert decision.status == st

    def test_invalid_status_rejected(self):
        """Reject invalid decision status."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="C",
                rationale="R", status="MAYBE",
            )

    def test_empty_decision_id_rejected(self):
        """Reject empty decision_id."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="", name="N", context="C", rationale="R",
            )

    def test_empty_name_rejected(self):
        """Reject empty name."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="", context="C", rationale="R",
            )

    def test_empty_context_rejected(self):
        """Reject empty context."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="", rationale="R",
            )

    def test_empty_rationale_rejected(self):
        """Reject empty rationale."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="C", rationale="",
            )


class TestDecisionUpdateValidation:
    """Validate DecisionUpdate model constraints."""

    def test_valid_partial_update(self):
        """Accept partial update with valid status."""
        update = DecisionUpdate(status="APPROVED")
        assert update.status == "APPROVED"

    def test_invalid_status_rejected(self):
        """Reject invalid decision status in update."""
        with pytest.raises(ValidationError):
            DecisionUpdate(status="SUPERSEDED")


class TestTaskCreateValidation:
    """Validate TaskCreate model constraints."""

    def test_valid_task_create(self):
        """Accept valid task creation data."""
        task = TaskCreate(
            task_id="T-001",
            description="Implement feature",
            phase="development",
        )
        assert task.task_id == "T-001"
        assert task.status == "TODO"

    def test_empty_task_id_accepted_for_auto_gen(self):
        """Empty task_id is valid (auto-generated at service level per META-TAXON-01-v1)."""
        task = TaskCreate(task_id="", description="D", phase="P")
        assert task.task_id == ""

    def test_none_task_id_accepted(self):
        """None task_id is valid (auto-generated from task_type at service level)."""
        task = TaskCreate(description="D", phase="P", task_type="bug")
        assert task.task_id is None

    def test_empty_description_rejected(self):
        """Reject empty description."""
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T1", description="", phase="P")

    def test_empty_phase_rejected(self):
        """Reject empty phase."""
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T1", description="D", phase="")

    def test_optional_fields_default_none(self):
        """Optional fields default to None."""
        task = TaskCreate(task_id="T1", description="D", phase="P")
        assert task.agent_id is None
        assert task.body is None
        assert task.linked_rules is None
        assert task.gap_id is None


class TestResponseModels:
    """Validate response model construction and defaults."""

    def test_rule_response_minimal(self):
        """RuleResponse with required fields only."""
        r = RuleResponse(
            id="RULE-001", name="Test", category="governance",
            priority="HIGH", status="ACTIVE", directive="Do X",
        )
        assert r.id == "RULE-001"
        assert r.semantic_id is None
        assert r.created_date is None
        assert r.document_path is None

    def test_rule_response_with_optional(self):
        """RuleResponse with all optional fields."""
        r = RuleResponse(
            id="RULE-001", name="Test", category="governance",
            priority="HIGH", status="ACTIVE", directive="Do X",
            semantic_id="GOV-RULE-01-v1", created_date="2026-01-30",
            document_path="docs/rules/leaf/GOV-RULE-01-v1.md",
            applicability="MANDATORY",
        )
        assert r.semantic_id == "GOV-RULE-01-v1"
        assert r.applicability == "MANDATORY"

    def test_task_response_defaults(self):
        """TaskResponse optional fields default correctly."""
        t = TaskResponse(
            task_id="T-001", description="Task", phase="P10", status="OPEN",
        )
        assert t.resolution is None
        assert t.agent_id is None
        assert t.linked_rules is None
        assert t.linked_commits is None

    def test_decision_response_defaults(self):
        """DecisionResponse with defaults."""
        d = DecisionResponse(
            id="DECISION-001", name="D", context="C",
            rationale="R", status="APPROVED",
        )
        assert d.decision_date is None
        assert d.linked_rules == []

    def test_session_response_defaults(self):
        """SessionResponse with required fields."""
        s = SessionResponse(
            session_id="SESSION-2026-01-30", start_time="2026-01-30T00:00:00",
            status="active",
        )
        assert s.tasks_completed == 0
        assert s.end_time is None
        assert s.evidence_files is None

    def test_agent_response_defaults(self):
        """AgentResponse with default list fields."""
        a = AgentResponse(
            agent_id="agent-001", name="Claude", agent_type="curator",
            status="active",
        )
        assert a.trust_score == 0.0
        assert a.tasks_executed == 0
        assert a.capabilities == []
        assert a.recent_sessions == []
        assert a.active_tasks == []

    def test_session_create_auto_id(self):
        """SessionCreate allows optional session_id."""
        s = SessionCreate(description="Test session")
        assert s.session_id is None
        assert s.agent_id is None


class TestPaginationModels:
    """Validate pagination model construction."""

    def test_pagination_meta(self):
        """PaginationMeta stores all fields."""
        meta = PaginationMeta(
            total=100, offset=0, limit=20, has_more=True, returned=20,
        )
        assert meta.total == 100
        assert meta.has_more is True

    def test_paginated_rule_response(self):
        """PaginatedRuleResponse wraps items + pagination."""
        rules = [RuleResponse(
            id="R1", name="N", category="governance",
            priority="LOW", status="ACTIVE", directive="D",
        )]
        resp = PaginatedRuleResponse(
            items=rules,
            pagination=PaginationMeta(
                total=1, offset=0, limit=20, has_more=False, returned=1,
            ),
        )
        assert len(resp.items) == 1
        assert resp.pagination.total == 1
        assert resp.pagination.has_more is False

    def test_paginated_task_response(self):
        """PaginatedTaskResponse wraps task items."""
        tasks = [TaskResponse(
            task_id="T1", description="D", phase="P10", status="TODO",
        )]
        resp = PaginatedTaskResponse(
            items=tasks,
            pagination=PaginationMeta(
                total=50, offset=20, limit=20, has_more=True, returned=1,
            ),
        )
        assert resp.pagination.offset == 20
        assert resp.pagination.has_more is True

    def test_paginated_empty_items(self):
        """Paginated response with empty items list."""
        resp = PaginatedDecisionResponse(
            items=[],
            pagination=PaginationMeta(
                total=0, offset=0, limit=20, has_more=False, returned=0,
            ),
        )
        assert len(resp.items) == 0
        assert resp.pagination.returned == 0

    def test_paginated_session_response(self):
        """PaginatedSessionResponse wraps session items."""
        sessions = [SessionResponse(
            session_id="S1", start_time="2026-01-30T00:00:00", status="active",
        )]
        resp = PaginatedSessionResponse(
            items=sessions,
            pagination=PaginationMeta(
                total=1, offset=0, limit=20, has_more=False, returned=1,
            ),
        )
        assert resp.items[0].session_id == "S1"

    def test_paginated_agent_response(self):
        """PaginatedAgentResponse wraps agent items."""
        agents = [AgentResponse(
            agent_id="A1", name="Bot", agent_type="curator", status="active",
        )]
        resp = PaginatedAgentResponse(
            items=agents,
            pagination=PaginationMeta(
                total=1, offset=0, limit=20, has_more=False, returned=1,
            ),
        )
        assert resp.items[0].agent_id == "A1"


class TestAPIStatus:
    """Validate APIStatus model."""

    def test_api_status_defaults(self):
        """APIStatus with required fields and defaults."""
        status = APIStatus(
            status="healthy", typedb_connected=True,
            rules_count=50, decisions_count=10,
        )
        assert status.version == "1.0.0"
        assert status.auth_enabled is False

    def test_api_status_custom(self):
        """APIStatus with custom version."""
        status = APIStatus(
            status="degraded", typedb_connected=False,
            rules_count=0, decisions_count=0, version="2.0.0",
        )
        assert status.version == "2.0.0"
        assert status.typedb_connected is False
