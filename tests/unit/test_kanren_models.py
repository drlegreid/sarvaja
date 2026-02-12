"""
Unit tests for Kanren Domain Models.

Per DOC-SIZE-01-v1: Tests for kanren/models.py module.
Tests: AgentContext, TaskContext, RuleContext dataclasses.
"""

from governance.kanren.models import AgentContext, TaskContext, RuleContext


class TestAgentContext:
    def test_basic(self):
        ctx = AgentContext(agent_id="A-1", name="Test", trust_score=0.85, agent_type="code")
        assert ctx.agent_id == "A-1"
        assert ctx.name == "Test"
        assert ctx.trust_score == 0.85
        assert ctx.agent_type == "code"

    def test_equality(self):
        a = AgentContext(agent_id="A-1", name="Test", trust_score=0.85, agent_type="code")
        b = AgentContext(agent_id="A-1", name="Test", trust_score=0.85, agent_type="code")
        assert a == b

    def test_different(self):
        a = AgentContext(agent_id="A-1", name="X", trust_score=0.85, agent_type="code")
        b = AgentContext(agent_id="A-2", name="Y", trust_score=0.90, agent_type="review")
        assert a != b


class TestTaskContext:
    def test_basic(self):
        ctx = TaskContext(task_id="T-1", priority="HIGH", requires_evidence=True)
        assert ctx.task_id == "T-1"
        assert ctx.priority == "HIGH"
        assert ctx.requires_evidence is True
        assert ctx.assigned_agent is None

    def test_with_agent(self):
        ctx = TaskContext(task_id="T-1", priority="MEDIUM", requires_evidence=False,
                          assigned_agent="code-agent")
        assert ctx.assigned_agent == "code-agent"

    def test_default_agent_none(self):
        ctx = TaskContext(task_id="T-1", priority="LOW", requires_evidence=False)
        assert ctx.assigned_agent is None


class TestRuleContext:
    def test_basic(self):
        ctx = RuleContext(rule_id="RULE-001", priority="CRITICAL",
                          status="ACTIVE", category="SESSION")
        assert ctx.rule_id == "RULE-001"
        assert ctx.priority == "CRITICAL"
        assert ctx.status == "ACTIVE"
        assert ctx.category == "SESSION"

    def test_equality(self):
        a = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="ARCH")
        b = RuleContext(rule_id="R-1", priority="HIGH", status="ACTIVE", category="ARCH")
        assert a == b
