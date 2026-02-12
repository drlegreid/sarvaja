"""
Unit tests for Governance API Pydantic Models.

Per DOC-SIZE-01-v1: Tests for governance/models.py module.
Tests: RuleCreate, RuleUpdate, RuleResponse, TaskCreate, TaskUpdate, TaskResponse,
       DecisionCreate, DecisionUpdate, DecisionResponse, SessionResponse,
       SessionCreate, SessionEnd, SessionUpdate, PaginationMeta,
       ProjectCreate, ProjectResponse, APIStatus.
"""

import pytest
from pydantic import ValidationError


# ── RuleCreate ───────────────────────────────────────────────────


class TestRuleCreate:
    def test_valid(self):
        from governance.models import RuleCreate
        r = RuleCreate(rule_id="R-1", name="Rule", category="governance",
                       priority="HIGH", directive="Do things")
        assert r.rule_id == "R-1"
        assert r.status == "DRAFT"

    def test_invalid_category(self):
        from governance.models import RuleCreate
        with pytest.raises(ValidationError):
            RuleCreate(rule_id="R-1", name="Rule", category="invalid",
                       priority="HIGH", directive="Do things")

    def test_invalid_priority(self):
        from governance.models import RuleCreate
        with pytest.raises(ValidationError):
            RuleCreate(rule_id="R-1", name="Rule", category="governance",
                       priority="URGENT", directive="Do things")

    def test_empty_rule_id(self):
        from governance.models import RuleCreate
        with pytest.raises(ValidationError):
            RuleCreate(rule_id="", name="Rule", category="governance",
                       priority="HIGH", directive="Do things")

    def test_with_tags(self):
        from governance.models import RuleCreate
        r = RuleCreate(rule_id="R-1", name="Rule", category="technical",
                       priority="LOW", directive="d", tags="a,b")
        assert r.tags == "a,b"

    def test_all_categories(self):
        from governance.models import RuleCreate
        for cat in ("governance", "technical", "operational"):
            r = RuleCreate(rule_id="R-1", name="R", category=cat,
                           priority="LOW", directive="d")
            assert r.category == cat


# ── RuleUpdate ───────────────────────────────────────────────────


class TestRuleUpdate:
    def test_all_optional(self):
        from governance.models import RuleUpdate
        r = RuleUpdate()
        assert r.name is None
        assert r.category is None

    def test_partial_update(self):
        from governance.models import RuleUpdate
        r = RuleUpdate(name="Updated")
        assert r.name == "Updated"
        assert r.status is None

    def test_invalid_status(self):
        from governance.models import RuleUpdate
        with pytest.raises(ValidationError):
            RuleUpdate(status="INVALID")


# ── RuleResponse ─────────────────────────────────────────────────


class TestRuleResponse:
    def test_valid(self):
        from governance.models import RuleResponse
        r = RuleResponse(id="R-1", name="Rule", category="governance",
                         priority="HIGH", status="ACTIVE", directive="d")
        assert r.id == "R-1"
        assert r.linked_tasks_count == 0

    def test_with_optional_fields(self):
        from governance.models import RuleResponse
        r = RuleResponse(id="R-1", name="Rule", category="governance",
                         priority="HIGH", status="ACTIVE", directive="d",
                         semantic_id="GOV-RULE-01-v1", document_path="/docs/r.md")
        assert r.semantic_id == "GOV-RULE-01-v1"


# ── TaskCreate ───────────────────────────────────────────────────


class TestTaskCreate:
    def test_valid(self):
        from governance.models import TaskCreate
        t = TaskCreate(task_id="T-1", description="Task", phase="VALIDATE")
        assert t.status == "TODO"
        assert t.agent_id is None

    def test_missing_phase(self):
        from governance.models import TaskCreate
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T-1", description="Task")

    def test_with_linked_rules(self):
        from governance.models import TaskCreate
        t = TaskCreate(task_id="T-1", description="d", phase="IMPLEMENT",
                       linked_rules=["R-1", "R-2"])
        assert t.linked_rules == ["R-1", "R-2"]


# ── TaskResponse ─────────────────────────────────────────────────


class TestTaskResponse:
    def test_valid(self):
        from governance.models import TaskResponse
        t = TaskResponse(task_id="T-1", description="d", phase="VALIDATE", status="OPEN")
        assert t.resolution is None
        assert t.linked_commits is None

    def test_with_all_fields(self):
        from governance.models import TaskResponse
        t = TaskResponse(
            task_id="T-1", description="d", phase="CERTIFY", status="DONE",
            resolution="VALIDATED", agent_id="code-agent",
            linked_rules=["R-1"], linked_sessions=["S-1"],
            linked_commits=["abc123"], gap_id="GAP-001",
            evidence="[Verification: L2] passed",
        )
        assert t.resolution == "VALIDATED"
        assert t.linked_commits == ["abc123"]


# ── DecisionCreate ───────────────────────────────────────────────


class TestDecisionCreate:
    def test_valid(self):
        from governance.models import DecisionCreate
        d = DecisionCreate(decision_id="D-1", name="Decision",
                           context="ctx", rationale="why")
        assert d.status == "PENDING"

    def test_with_options(self):
        from governance.models import DecisionCreate, DecisionOption
        opt = DecisionOption(label="Option A", pros=["fast"], cons=["risky"])
        d = DecisionCreate(decision_id="D-1", name="D", context="c",
                           rationale="r", options=[opt], selected_option="Option A")
        assert len(d.options) == 1

    def test_invalid_status(self):
        from governance.models import DecisionCreate
        with pytest.raises(ValidationError):
            DecisionCreate(decision_id="D-1", name="D", context="c",
                           rationale="r", status="INVALID")


# ── DecisionResponse ─────────────────────────────────────────────


class TestDecisionResponse:
    def test_valid(self):
        from governance.models import DecisionResponse
        d = DecisionResponse(id="D-1", name="D", context="c",
                             rationale="r", status="APPROVED")
        assert d.linked_rules == []
        assert d.options == []


# ── SessionModels ────────────────────────────────────────────────


class TestSessionModels:
    def test_session_create(self):
        from governance.models import SessionCreate
        s = SessionCreate(description="Test session")
        assert s.session_id is None
        assert s.cc_session_uuid is None

    def test_session_create_with_cc(self):
        from governance.models import SessionCreate
        s = SessionCreate(
            description="Test", cc_session_uuid="uuid-123",
            cc_project_slug="sarvaja", cc_git_branch="master",
        )
        assert s.cc_session_uuid == "uuid-123"

    def test_session_response(self):
        from governance.models import SessionResponse
        s = SessionResponse(session_id="S-1", start_time="2026-01-01", status="ACTIVE")
        assert s.tasks_completed == 0
        assert s.cc_tool_count is None

    def test_session_end(self):
        from governance.models import SessionEnd
        s = SessionEnd(tasks_completed=5, evidence_files=["f.md"])
        assert s.tasks_completed == 5

    def test_session_update(self):
        from governance.models import SessionUpdate
        s = SessionUpdate(status="COMPLETED", tasks_completed=3)
        assert s.description is None


# ── PaginationMeta ───────────────────────────────────────────────


class TestPaginationMeta:
    def test_valid(self):
        from governance.models import PaginationMeta
        p = PaginationMeta(total=100, offset=0, limit=50, has_more=True, returned=50)
        assert p.has_more is True

    def test_empty(self):
        from governance.models import PaginationMeta
        p = PaginationMeta(total=0, offset=0, limit=50, has_more=False, returned=0)
        assert p.total == 0


# ── ProjectCreate ────────────────────────────────────────────────


class TestProjectCreate:
    def test_valid(self):
        from governance.models import ProjectCreate
        p = ProjectCreate(name="My Project")
        assert p.project_id is None
        assert p.path is None

    def test_with_id_and_path(self):
        from governance.models import ProjectCreate
        p = ProjectCreate(project_id="PROJ-1", name="P", path="/home/test")
        assert p.project_id == "PROJ-1"


# ── ChatModels ───────────────────────────────────────────────────


class TestChatModels:
    def test_chat_message_request(self):
        from governance.models import ChatMessageRequest
        r = ChatMessageRequest(content="hello")
        assert r.agent_id is None
        assert r.session_id is None

    def test_chat_message_response(self):
        from governance.models import ChatMessageResponse
        r = ChatMessageResponse(id="M-1", role="user", content="hi",
                                timestamp="2026-01-01")
        assert r.status == "complete"

    def test_chat_session_response(self):
        from governance.models import ChatSessionResponse
        r = ChatSessionResponse(session_id="C-1", messages=[])
        assert r.active_task_id is None


# ── APIStatus ────────────────────────────────────────────────────


class TestAPIStatus:
    def test_valid(self):
        from governance.models import APIStatus
        s = APIStatus(status="ok", typedb_connected=True,
                      rules_count=50, decisions_count=10)
        assert s.version == "1.0.0"
        assert s.auth_enabled is False
