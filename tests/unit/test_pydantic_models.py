"""
Tests for governance Pydantic API models.

Per GAP-MCP-008: Validates request/response models for API endpoints.
Covers validation constraints, defaults, optional fields, and serialization.

Created: 2026-01-30
"""

import pytest

from governance.models import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskExecutionEvent,
    TaskExecutionResponse,
    DecisionCreate,
    DecisionUpdate,
    DecisionResponse,
    SessionResponse,
    SessionCreate,
    SessionEnd,
    SessionUpdate,
    EvidenceResponse,
    EvidenceSearchResult,
    EvidenceSearchResponse,
    FileContentResponse,
    AgentResponse,
    AgentTaskAssign,
    ExecutiveReportSection,
    ExecutiveSummarySession,
    ExecutiveReportResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    PaginationMeta,
    PaginatedRuleResponse,
    PaginatedTaskResponse,
    PaginatedSessionResponse,
    PaginatedAgentResponse,
    PaginatedDecisionResponse,
    APIStatus,
)


class TestRuleCreate:
    """Test RuleCreate validation."""

    def test_valid_minimal(self):
        r = RuleCreate(rule_id="RULE-001", name="Test", category="governance",
                       priority="HIGH", directive="Do something")
        assert r.rule_id == "RULE-001"
        assert r.status == "DRAFT"
        assert r.tags is None
        assert r.applicable_roles is None

    def test_all_fields(self):
        r = RuleCreate(rule_id="R1", name="Full", category="technical",
                       priority="CRITICAL", directive="Dir", status="ACTIVE",
                       tags="security,auth", applicable_roles="admin,reviewer")
        assert r.tags == "security,auth"
        assert r.status == "ACTIVE"

    def test_invalid_category(self):
        with pytest.raises(Exception):
            RuleCreate(rule_id="R1", name="X", category="INVALID",
                       priority="HIGH", directive="D")

    def test_invalid_priority(self):
        with pytest.raises(Exception):
            RuleCreate(rule_id="R1", name="X", category="governance",
                       priority="ULTRA", directive="D")

    def test_empty_rule_id_rejected(self):
        with pytest.raises(Exception):
            RuleCreate(rule_id="", name="X", category="governance",
                       priority="HIGH", directive="D")

    def test_empty_name_rejected(self):
        with pytest.raises(Exception):
            RuleCreate(rule_id="R1", name="", category="governance",
                       priority="HIGH", directive="D")


class TestRuleUpdate:
    """Test RuleUpdate partial update model."""

    def test_all_none_default(self):
        r = RuleUpdate()
        assert r.name is None
        assert r.category is None
        assert r.priority is None
        assert r.directive is None
        assert r.status is None

    def test_partial_update(self):
        r = RuleUpdate(name="Updated", priority="LOW")
        assert r.name == "Updated"
        assert r.priority == "LOW"
        assert r.category is None


class TestRuleResponse:
    """Test RuleResponse model."""

    def test_minimal(self):
        r = RuleResponse(id="R1", name="Test", category="governance",
                        priority="HIGH", status="ACTIVE", directive="Dir")
        assert r.id == "R1"
        assert r.semantic_id is None
        assert r.document_path is None

    def test_with_optionals(self):
        r = RuleResponse(id="R1", name="Test", category="governance",
                        priority="HIGH", status="ACTIVE", directive="Dir",
                        semantic_id="GOV-RULE-01-v1", applicability="MANDATORY")
        assert r.semantic_id == "GOV-RULE-01-v1"
        assert r.applicability == "MANDATORY"


class TestTaskCreate:
    """Test TaskCreate validation."""

    def test_minimal(self):
        t = TaskCreate(task_id="T1", description="Do thing", phase="Phase1")
        assert t.status == "TODO"
        assert t.agent_id is None
        assert t.body is None
        assert t.linked_rules is None

    def test_with_all_fields(self):
        t = TaskCreate(task_id="T1", description="Do", phase="P1",
                       status="IN_PROGRESS", agent_id="A1", body="Details",
                       linked_rules=["R1", "R2"], linked_sessions=["S1"],
                       gap_id="GAP-001")
        assert t.linked_rules == ["R1", "R2"]
        assert t.gap_id == "GAP-001"


class TestTaskResponse:
    """Test TaskResponse model."""

    def test_minimal(self):
        t = TaskResponse(task_id="T1", description="Test", phase="P1", status="OPEN")
        assert t.resolution is None
        assert t.linked_commits is None
        assert t.evidence is None

    def test_full_response(self):
        t = TaskResponse(
            task_id="T1", description="Test", phase="P1", status="CLOSED",
            resolution="CERTIFIED", agent_id="A1",
            created_at="2026-01-30T10:00:00", completed_at="2026-01-30T12:00:00",
            linked_rules=["R1"], linked_sessions=["S1"], linked_commits=["abc123"],
            gap_id="GAP-001", evidence="[Verification: L3] Tests pass"
        )
        assert t.resolution == "CERTIFIED"
        assert t.linked_commits == ["abc123"]


class TestDecisionModels:
    """Test Decision request/response models."""

    def test_create_defaults(self):
        d = DecisionCreate(decision_id="D1", name="N", context="C", rationale="R")
        assert d.status == "PENDING"

    def test_create_invalid_status(self):
        with pytest.raises(Exception):
            DecisionCreate(decision_id="D1", name="N", context="C",
                          rationale="R", status="INVALID")

    def test_update_all_none(self):
        d = DecisionUpdate()
        assert d.name is None
        assert d.decision_date is None

    def test_response(self):
        d = DecisionResponse(id="D1", name="N", context="C", rationale="R", status="APPROVED")
        assert d.linked_rules == []
        assert d.decision_date is None


class TestSessionModels:
    """Test Session request/response models."""

    def test_response_defaults(self):
        s = SessionResponse(session_id="S1", start_time="2026-01-30T10:00:00", status="ACTIVE")
        assert s.tasks_completed == 0
        assert s.end_time is None
        assert s.evidence_files is None

    def test_create(self):
        s = SessionCreate(description="Test session")
        assert s.session_id is None
        assert s.agent_id is None

    def test_end(self):
        s = SessionEnd(tasks_completed=5, evidence_files=["e1.json"])
        assert s.tasks_completed == 5

    def test_update(self):
        s = SessionUpdate(status="ENDED", tasks_completed=3)
        assert s.description is None


class TestEvidenceModels:
    """Test Evidence models."""

    def test_response(self):
        e = EvidenceResponse(evidence_id="E1", source="pytest", content="OK", created_at="2026-01-30")
        assert e.session_id is None

    def test_search_result(self):
        r = EvidenceSearchResult(source="test.py", source_type="file", score=0.95, content="data")
        assert r.score == 0.95

    def test_search_response(self):
        r = EvidenceSearchResponse(query="test", results=[], count=0, search_method="chromadb")
        assert r.results == []


class TestAgentModels:
    """Test Agent models."""

    def test_response_defaults(self):
        a = AgentResponse(agent_id="A1", name="Agent", agent_type="reviewer", status="ACTIVE")
        assert a.tasks_executed == 0
        assert a.trust_score == 0.0
        assert a.capabilities == []
        assert a.recent_sessions == []
        assert a.active_tasks == []

    def test_task_assign(self):
        a = AgentTaskAssign(task_id="T1")
        assert a.task_id == "T1"


class TestExecutiveReport:
    """Test Executive Report models."""

    def test_section(self):
        s = ExecutiveReportSection(title="Highlights", content="All good")
        assert s.metrics is None
        assert s.status is None

    def test_session_summary(self):
        s = ExecutiveSummarySession(session_id="S1", date="2026-01-30",
                                    tasks_completed=5, decisions_made=2,
                                    rules_applied=["R1"], key_outcomes=["Done"])
        assert s.tasks_completed == 5

    def test_report_response(self):
        r = ExecutiveReportResponse(
            report_id="RPT-1", generated_at="2026-01-30", period="2026-01-30",
            sections=[], overall_status="healthy", metrics_summary={"rules": 50}
        )
        assert r.overall_status == "healthy"


class TestChatModels:
    """Test Chat models."""

    def test_message_request(self):
        m = ChatMessageRequest(content="Hello")
        assert m.agent_id is None
        assert m.session_id is None

    def test_message_response(self):
        m = ChatMessageResponse(id="M1", role="agent", content="Hi", timestamp="T1")
        assert m.status == "complete"
        assert m.agent_name is None

    def test_session_response(self):
        s = ChatSessionResponse(session_id="S1", messages=[])
        assert s.active_task_id is None


class TestPagination:
    """Test pagination models."""

    def test_meta(self):
        p = PaginationMeta(total=100, offset=0, limit=20, has_more=True, returned=20)
        assert p.has_more is True

    def test_paginated_rules(self):
        p = PaginatedRuleResponse(
            items=[],
            pagination=PaginationMeta(total=0, offset=0, limit=20, has_more=False, returned=0)
        )
        assert p.items == []

    def test_paginated_tasks(self):
        p = PaginatedTaskResponse(
            items=[],
            pagination=PaginationMeta(total=0, offset=0, limit=20, has_more=False, returned=0)
        )
        assert len(p.items) == 0

    def test_paginated_sessions(self):
        p = PaginatedSessionResponse(
            items=[],
            pagination=PaginationMeta(total=5, offset=0, limit=20, has_more=False, returned=5)
        )
        assert p.pagination.total == 5

    def test_paginated_agents(self):
        p = PaginatedAgentResponse(
            items=[],
            pagination=PaginationMeta(total=0, offset=0, limit=10, has_more=False, returned=0)
        )
        assert p.pagination.limit == 10

    def test_paginated_decisions(self):
        p = PaginatedDecisionResponse(
            items=[],
            pagination=PaginationMeta(total=0, offset=0, limit=10, has_more=False, returned=0)
        )
        assert p.items == []


class TestAPIStatus:
    """Test APIStatus model."""

    def test_defaults(self):
        s = APIStatus(status="OK", typedb_connected=True, rules_count=50, decisions_count=10)
        assert s.version == "1.0.0"
        assert s.auth_enabled is False

    def test_custom_version(self):
        s = APIStatus(status="OK", typedb_connected=False, rules_count=0,
                     decisions_count=0, version="2.0.0", auth_enabled=True)
        assert s.version == "2.0.0"
        assert s.auth_enabled is True


class TestTaskExecutionModels:
    """Test task execution event models."""

    def test_event(self):
        e = TaskExecutionEvent(event_id="E1", task_id="T1", event_type="claimed",
                              timestamp="2026-01-30T10:00:00", message="Agent claimed task")
        assert e.agent_id is None
        assert e.details is None

    def test_execution_response(self):
        r = TaskExecutionResponse(task_id="T1")
        assert r.events == []
        assert r.current_status == "pending"
        assert r.current_agent is None
