"""
Unit tests for Kanren Domain Models.

Per DOC-SIZE-01-v1: Tests for kanren/models.py module.
Tests: AgentContext, TaskContext, RuleContext dataclasses.
"""

import pytest
from dataclasses import asdict

from governance.kanren.models import AgentContext, TaskContext, RuleContext


class TestAgentContext:
    """Tests for AgentContext dataclass."""

    def test_basic(self):
        a = AgentContext(agent_id="AGENT-001", name="Code", trust_score=0.85, agent_type="claude-code")
        assert a.agent_id == "AGENT-001"
        assert a.name == "Code"
        assert a.trust_score == 0.85
        assert a.agent_type == "claude-code"

    def test_asdict(self):
        a = AgentContext(agent_id="A-1", name="n", trust_score=0.5, agent_type="test")
        d = asdict(a)
        assert isinstance(d, dict)
        assert d["trust_score"] == 0.5

    def test_high_trust(self):
        a = AgentContext(agent_id="A-1", name="Expert", trust_score=1.0, agent_type="claude-code")
        assert a.trust_score == 1.0

    def test_low_trust(self):
        a = AgentContext(agent_id="A-1", name="New", trust_score=0.0, agent_type="test-agent")
        assert a.trust_score == 0.0


class TestTaskContext:
    """Tests for TaskContext dataclass."""

    def test_required_fields(self):
        t = TaskContext(task_id="T-001", priority="HIGH", requires_evidence=True)
        assert t.task_id == "T-001"
        assert t.priority == "HIGH"
        assert t.requires_evidence is True

    def test_default_assigned_agent(self):
        t = TaskContext(task_id="T-1", priority="LOW", requires_evidence=False)
        assert t.assigned_agent is None

    def test_with_assigned_agent(self):
        t = TaskContext(task_id="T-1", priority="CRITICAL", requires_evidence=True, assigned_agent="AGENT-001")
        assert t.assigned_agent == "AGENT-001"

    def test_asdict(self):
        t = TaskContext(task_id="T-1", priority="MEDIUM", requires_evidence=False)
        d = asdict(t)
        assert d["priority"] == "MEDIUM"
        assert d["assigned_agent"] is None


class TestRuleContext:
    """Tests for RuleContext dataclass."""

    def test_basic(self):
        r = RuleContext(rule_id="RULE-001", priority="CRITICAL", status="ACTIVE", category="governance")
        assert r.rule_id == "RULE-001"
        assert r.priority == "CRITICAL"
        assert r.status == "ACTIVE"
        assert r.category == "governance"

    def test_asdict(self):
        r = RuleContext(rule_id="R-1", priority="LOW", status="DRAFT", category="test")
        d = asdict(r)
        assert isinstance(d, dict)
        assert d["status"] == "DRAFT"
