"""
Tests for TypeDB entity data classes.

Per RULE-012, GAP-FILE-003: Core domain entities.
Covers Rule, Decision, Task, Session, Agent, InferenceResult.

Created: 2026-01-30
"""

import pytest
from datetime import datetime

from governance.typedb.entities import (
    Rule,
    Decision,
    Task,
    Session,
    Agent,
    InferenceResult,
)


class TestRule:
    """Test Rule dataclass."""

    def test_minimal(self):
        r = Rule(id="R1", name="Test", category="governance",
                priority="HIGH", status="ACTIVE", directive="Do X")
        assert r.id == "R1"
        assert r.rule_type is None
        assert r.semantic_id is None
        assert r.applicability is None
        assert r.created_date is None

    def test_with_optionals(self):
        r = Rule(id="R1", name="Test", category="technical",
                priority="CRITICAL", status="ACTIVE", directive="Dir",
                rule_type="FOUNDATIONAL", semantic_id="GOV-RULE-01-v1",
                applicability="MANDATORY", created_date=datetime(2026, 1, 30))
        assert r.rule_type == "FOUNDATIONAL"
        assert r.semantic_id == "GOV-RULE-01-v1"
        assert r.applicability == "MANDATORY"
        assert r.created_date.year == 2026

    def test_rule_types(self):
        for rt in ["FOUNDATIONAL", "OPERATIONAL", "TECHNICAL", "META", "LEAF"]:
            r = Rule(id="R1", name="N", category="c", priority="p",
                    status="s", directive="d", rule_type=rt)
            assert r.rule_type == rt


class TestDecision:
    """Test Decision dataclass."""

    def test_minimal(self):
        d = Decision(id="D1", name="Decision", context="Ctx",
                    rationale="Because", status="APPROVED")
        assert d.id == "D1"
        assert d.decision_date is None

    def test_with_date(self):
        dt = datetime(2026, 1, 15, 10, 30)
        d = Decision(id="D1", name="N", context="C", rationale="R",
                    status="PENDING", decision_date=dt)
        assert d.decision_date.day == 15


class TestTask:
    """Test Task dataclass."""

    def test_minimal(self):
        t = Task(id="T1", name="Do thing", status="OPEN", phase="Phase1")
        assert t.resolution == "NONE"
        assert t.description is None
        assert t.body is None
        assert t.agent_id is None
        assert t.linked_rules is None
        assert t.linked_sessions is None
        assert t.linked_commits is None
        assert t.business is None
        assert t.design is None
        assert t.architecture is None
        assert t.test_section is None
        assert t.parent_task is None
        assert t.child_tasks is None
        assert t.item_type is None
        assert t.document_path is None

    def test_with_lifecycle(self):
        t = Task(id="T1", name="N", status="CLOSED", phase="P1",
                resolution="CERTIFIED", evidence="Tests pass",
                completed_at=datetime(2026, 1, 30))
        assert t.resolution == "CERTIFIED"
        assert t.evidence == "Tests pass"

    def test_with_relationships(self):
        t = Task(id="T1", name="N", status="IN_PROGRESS", phase="P1",
                linked_rules=["R1", "R2"], linked_sessions=["S1"],
                linked_commits=["abc123"], gap_id="GAP-001",
                agent_id="A1")
        assert len(t.linked_rules) == 2
        assert t.linked_commits == ["abc123"]

    def test_detail_sections(self):
        t = Task(id="T1", name="N", status="OPEN", phase="P1",
                business="User needs X", design="Build form",
                architecture="React + API", test_section="Unit tests")
        assert t.business == "User needs X"
        assert t.test_section == "Unit tests"

    def test_task_relationships(self):
        t = Task(id="T1", name="N", status="OPEN", phase="P1",
                parent_task="T0", child_tasks=["T2", "T3"],
                blocks=["T4"], blocked_by=["T5"],
                related_tasks=["T6"])
        assert t.parent_task == "T0"
        assert len(t.child_tasks) == 2

    def test_unified_work_item(self):
        t = Task(id="T1", name="N", status="OPEN", phase="P1",
                item_type="gap", document_path="docs/gaps/GAP-001.md")
        assert t.item_type == "gap"
        assert t.document_path == "docs/gaps/GAP-001.md"


class TestSession:
    """Test Session dataclass."""

    def test_minimal(self):
        s = Session(id="S1")
        assert s.status == "ACTIVE"
        assert s.tasks_completed == 0
        assert s.name is None
        assert s.description is None
        assert s.agent_id is None

    def test_completed_session(self):
        s = Session(id="S1", name="Work", description="Did things",
                   status="ENDED", tasks_completed=5,
                   agent_id="A1",
                   started_at=datetime(2026, 1, 30, 9, 0),
                   completed_at=datetime(2026, 1, 30, 17, 0),
                   linked_rules_applied=["R1", "R2"],
                   linked_decisions=["D1"],
                   evidence_files=["e1.json"])
        assert s.tasks_completed == 5
        assert len(s.linked_rules_applied) == 2


class TestAgent:
    """Test Agent dataclass."""

    def test_minimal(self):
        a = Agent(id="A1", name="TestAgent", agent_type="reviewer")
        assert a.status == "ACTIVE"
        assert a.trust_score == 0.8
        assert a.compliance_rate == 0.9
        assert a.accuracy_rate == 0.85
        assert a.tenure_days == 0
        assert a.tasks_executed == 0
        assert a.last_active is None

    def test_with_metrics(self):
        a = Agent(id="A1", name="N", agent_type="executor",
                 status="ACTIVE", trust_score=0.95,
                 compliance_rate=0.98, accuracy_rate=0.92,
                 tenure_days=30, tasks_executed=50,
                 last_active=datetime(2026, 1, 30))
        assert a.trust_score == 0.95
        assert a.tasks_executed == 50


class TestInferenceResult:
    """Test InferenceResult dataclass."""

    def test_empty(self):
        r = InferenceResult(query="test", results=[], count=0, inference_used=False)
        assert r.results == []
        assert r.inference_used is False

    def test_with_results(self):
        r = InferenceResult(
            query="depends on RULE-001",
            results=[{"type": "dep", "rule_id": "RULE-002"}],
            count=1,
            inference_used=True
        )
        assert r.count == 1
        assert r.inference_used is True
